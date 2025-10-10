from __future__ import annotations
import io, json
from typing import List, Dict, Any, Tuple
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
import torch
from transformers import AutoFeatureExtractor, AutoModelForCTC
from g2p_en import G2p
from rapidfuzz.distance import Levenshtein as L
from unidecode import unidecode
import re, inflect
NUM = inflect.engine()

def norm_text(s: str) -> str:
    s = unidecode((s or "")).lower()                                    # ASCII fold + lowercase
    s = re.sub(r"\d+", lambda m: NUM.number_to_words(m.group()).replace("-", " "), s)  # 123 -> "one two three"
    s = re.sub(r"[^a-z' ]+", " ", s)                                    # drop everything except a–z, space, apostrophe
    s = re.sub(r"\s+", " ", s).strip()                                  # collapse spaces
    return s

# Keep CPU predictable on small machines
torch.set_num_threads(max(1, torch.get_num_threads()))
DEVICE = torch.device("cpu")

# Lazy singletons
_model = None
_feat = None
_id2sym: Dict[int, str] | None = None
_rules = None
_g2p = None
_blank_id: int | None = None

# utils_phone.py (add near imports)
def _ensure_nltk_data():
    import nltk
    needed = [
        ("taggers/averaged_perceptron_tagger_eng", "averaged_perceptron_tagger_eng"),
        ("corpora/cmudict", "cmudict"),
    ]
    for path, pkg in needed:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg)


def _infer_blank_id(model_cfg, id2sym: Dict[int, str]) -> int:
    """
    Infer the CTC blank from config, falling back to common placeholder symbols in vocab.
    """
    for attr in ("blank_token_id", "ctc_blank_id", "pad_token_id"):
        val = getattr(model_cfg, attr, None)
        if isinstance(val, int):
            return val
    placeholder_syms = {"<pad>", "<s>", "</s>", "<blk>", "<blank>"}
    for i, sym in id2sym.items():
        if str(sym).lower() in placeholder_syms:
            return int(i)
    return 0


def _load_once():
    global _model, _feat, _id2sym, _rules, _pron_guardrails, _g2p, _blank_id
    if _model is not None:
        return _model, _feat, _id2sym, _rules, _pron_guardrails, _g2p, _blank_id

    # Feature extractor & model from local folder
    _feat = AutoFeatureExtractor.from_pretrained("app/model")   # uses preprocessor_config.json
    _model = AutoModelForCTC.from_pretrained("app/model", torch_dtype=torch.float32).to(DEVICE).eval()

    # Invert vocab: symbol->id  ==>  id(int)->symbol(str, UPPER)
    with open("app/vocab.json", "r", encoding="utf-8") as f:
        sym2id = json.load(f)
    _id2sym = {}
    for k, v in sym2id.items():
        try:
            _id2sym[int(v)] = str(k).upper()
        except Exception:
            continue

    # Robust blank id
    _blank_id = _infer_blank_id(_model.config, _id2sym)

    # Optional SLE rules file (grammar)
    try:
        with open("app/sle_rules.json", "r", encoding="utf-8") as f:
            _rules = json.load(f)
    except FileNotFoundError:
        _rules = {"rules": []}

    # New: Pronunciation Guardrails
    try:
        with open("app/pronunciation_guardrails.json", "r", encoding="utf-8") as f:
            _pron_guardrails = json.load(f)
    except FileNotFoundError:
        _pron_guardrails = {"rules": []}

    _ensure_nltk_data()
    _g2p = G2p()
    return _model, _feat, _id2sym, _rules, _pron_guardrails, _g2p, _blank_id


def _to_mono_16k(wav: np.ndarray, sr: int) -> np.ndarray:
    """Ensure mono 16 kHz float32 using exact rational resampling."""
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if sr == 16000:
        return wav.astype(np.float32, copy=False)
    from math import gcd
    g = gcd(sr, 16000)
    up, down = 16000 // g, sr // g
    return resample_poly(wav, up, down).astype(np.float32, copy=False)


def _decode_ids(ids: List[int], id2sym: Dict[int, str], blank_id: int) -> List[str]:
    """Greedy CTC collapse; drop blank and repeats; ignore placeholders."""
    seq: List[str] = []
    prev = None
    for i in ids:
        if i == blank_id:
            prev = i
            continue
        if i != prev:
            sym = id2sym.get(i, "?")
            if sym and sym not in {"<pad>", "<s>", "</s>", "|"}:
                seq.append(sym)
        prev = i
    return seq


def _g2p_arpabet(text_or_words: str | List[str], g2p: G2p) -> List[str]:
    """ARPAbet-like phones uppercased, stress digits stripped."""
    words = text_or_words if isinstance(text_or_words, list) else norm_text(text_or_words).split()
    out: List[str] = []
    for ph in g2p(words):
        if not ph or ph == " ":
            continue
        ph = "".join(c for c in ph if not c.isdigit()).upper()
        if ph and ph not in {"<PAD>", "<S>", "</S>", "|", "'"}:
            out.append(ph)
    return out

def _g2p_word_level(norm_text: str, g2p: G2p) -> List[Dict[str, Any]]:
    """Returns a list of {'word': str, 'phones': List[str]} for a normalized sentence."""
    words = norm_text.split()
    phones_flat = _g2p_arpabet(words, g2p)
    
    # Heuristic and imperfectly split flat phones back to word boundaries
    out = [{"word": w, "phones": []} for w in words]
    phone_idx = 0
    for i, word in enumerate(words):
        # This is a rough estimate of how many phonemes a word might have
        # A better approach would be to use a dictionary or a more sophisticated model
        expected_phone_count = len(word) 
        
        # Get the phonemes for the current word
        word_phones = _g2p_arpabet(word, g2p)
        
        # Match the generated phonemes with the flat list
        matched_phones = []
        for p in word_phones:
            if phone_idx < len(phones_flat) and phones_flat[phone_idx] == p:
                matched_phones.append(p)
                phone_idx += 1
            else:
                # If there's a mismatch, we might have a g2p inconsistency.
                # We'll be conservative and just append the phones we have for the word.
                break
        out[i]["phones"] = matched_phones if matched_phones else word_phones

    return out


def _align_ops(gold: List[str], pred: List[str]) -> List[Dict[str, Any]]:
    """Levenshtein ops with readable symbols & indices."""
    ops: List[Dict[str, Any]] = []
    for op, i, j in L.editops(gold, pred):
        if op == "replace":
            ops.append({"op": "S", "g": gold[i], "p": pred[j], "i": i, "j": j})
        elif op == "delete":
            ops.append({"op": "D", "g": gold[i], "p": None,    "i": i, "j": j})
        elif op == "insert":
            ops.append({"op": "I", "g": None,    "p": pred[j], "i": i, "j": j})
    return ops


def _apply_pronunciation_guardrails(ops: List[Dict[str, Any]], guardrails_json: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Drop ops that match an enabled pronunciation guardrail rule."""
    kept, dropped = [], []
    guardrail_rules = guardrails_json.get("rules", [])

    for o in ops:
        matched = False
        for r in guardrail_rules:
            if not r.get("enabled", True):
                continue

            rule_type = r.get("type")
            op_type = o["op"]

            if rule_type == op_type:
                if rule_type == "S": # Substitution
                    if o["g"].upper() == r["gold"].upper() and (o["p"] or "").upper() == r["pred"].upper():
                        dropped.append(o)
                        matched = True
                        break
                elif rule_type == "D": # Deletion
                    if o["g"].upper() == r["gold"].upper():
                        dropped.append(o)
                        matched = True
                        break
                elif rule_type == "I": # Insertion
                    if (o["p"] or "").upper() == r["pred"].upper():
                        dropped.append(o)
                        matched = True
                        break
        if not matched:
            kept.append(o)
    return kept, dropped


PRONUNCIATION_WEAKNESS_MAP = {
    # TH sounds
    ("TH", "T"): "pronunciation_th_vs_t",
    ("TH", "D"): "pronunciation_th_vs_t",
    ("DH", "D"): "pronunciation_th_vs_t",
    ("DH", "V"): "pronunciation_th_vs_t",
    # R vs L sounds
    ("R", "L"): "pronunciation_r_vs_l",
    ("L", "R"): "pronunciation_r_vs_l",
    # Add more rules here based on topics.md
}

def _categorize_pronunciation_weaknesses(errors: List[Dict[str, Any]]) -> List[str]:
    """Categorizes phoneme errors based on a predefined rulebook."""
    categories = set()
    for error in errors:
        if error["op"] == 'S':  # Substitution
            g, p = error["g"], error["p"]
            if (g, p) in PRONUNCIATION_WEAKNESS_MAP:
                categories.add(PRONUNCIATION_WEAKNESS_MAP[(g, p)])
    return sorted(list(categories))


def run_phoneme(file_bytes: bytes, ref_text: str | None = None) -> Dict[str, Any]:
    model, feat, id2sym, rules, g2p, blank_id = _load_once()

    # Read & resample audio
    buf = file_bytes if isinstance(file_bytes, (bytes, bytearray)) else file_bytes.read()
    y, sr = sf.read(io.BytesIO(buf), dtype="float32", always_2d=False)
    if not isinstance(y, np.ndarray) or y.size == 0:
        raise ValueError("Invalid or empty audio.")
    y = _to_mono_16k(y, int(sr))

    # Forward pass
    with torch.no_grad():
        inputs = feat(y, sampling_rate=16000, return_tensors="pt")
        for k in inputs:
            inputs[k] = inputs[k].to(DEVICE)
        logits = model(**inputs).logits[0].cpu()   # [T, vocab]
        ids = logits.argmax(dim=-1).tolist()      # greedy

    pred_phones = _decode_ids(ids, id2sym, int(blank_id))
    out: Dict[str, Any] = {"pred_phones": pred_phones}

    if ref_text:
        norm_ref = norm_text(ref_text)
        words_and_phones = _g2p_word_level(norm_ref, g2p)
        gold_phones = [p for w in words_and_phones for p in w["phones"]]

        ops = _align_ops(gold_phones, pred_phones)
        denom = max(1, len(gold_phones))
        per_strict = 100.0 * sum(1 for o in ops if o["op"] in ("S", "I", "D")) / denom
        kept, dropped = _apply_pronunciation_guardrails(ops, _pron_guardrails)
        per_sle = 100.0 * sum(1 for o in kept if o["op"] in ("S", "I", "D")) / denom

        word_analysis, overall_weaknesses = _analyze_word_level(norm_ref.split(), words_and_phones, kept)

        out.update({
            "phoneme_error_rate": per_sle,
            "word_analysis": word_analysis,
            "weakness_categories": overall_weaknesses,
        })
    return out


def _map_phone_errors_to_words(words_and_phones: List[Dict[str, Any]], phone_errors: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """Distributes phone errors back to word indices."""
    word_errors = {i: [] for i in range(len(words_and_phones))}
    phone_cursor = 0
    error_cursor = 0
    for i, word_data in enumerate(words_and_phones):
        word_phone_len = len(word_data["phones"])
        # Find errors that fall within the current word's phoneme span
        while error_cursor < len(phone_errors):
            error = phone_errors[error_cursor]
            # 'i' is the index in the *gold* phoneme list
            if phone_cursor <= error["i"] < phone_cursor + word_phone_len:
                word_errors[i].append(error)
                error_cursor += 1
            else:
                break
        phone_cursor += word_phone_len
    return word_errors

def _analyze_word_level(ref_words: List[str], words_and_phones: List[Dict[str, Any]], sle_errors: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Analyzes pronunciation at the word level, identifying errors and weakness categories for each word."""
    word_errors_map = _map_phone_errors_to_words(words_and_phones, sle_errors)
    word_analysis = []
    all_weaknesses = set()

    for i, word_data in enumerate(words_and_phones):
        errors = word_errors_map.get(i, [])
        categories = _categorize_pronunciation_weaknesses(errors)
        if categories:
            all_weaknesses.update(categories)
        
        word_analysis.append({
            "word": word_data["word"],
            "phoneme_errors": errors,
            "weakness_categories": categories
        })

    return word_analysis, sorted(list(all_weaknesses))
