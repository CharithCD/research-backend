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
    global _model, _feat, _id2sym, _rules, _g2p, _blank_id
    if _model is not None:
        return _model, _feat, _id2sym, _rules, _g2p, _blank_id

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

    # Optional SLE rules file
    try:
        with open("app/sle_rules.json", "r", encoding="utf-8") as f:
            _rules = json.load(f)
    except FileNotFoundError:
        _rules = {"rules": []}

    _ensure_nltk_data()
    _g2p = G2p()
    return _model, _feat, _id2sym, _rules, _g2p, _blank_id


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


def _g2p_arpabet(text: str, g2p: G2p) -> List[str]:
    """ARPAbet-like phones uppercased, stress digits stripped."""
    text = norm_text(text)
    out: List[str] = []
    for ph in g2p(text):
        if not ph or ph == " ":
            continue
        ph = "".join(c for c in ph if not c.isdigit()).upper()
        if ph and ph not in {"<PAD>", "<S>", "</S>", "|"}:
            out.append(ph)
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


def _apply_sle_rules(ops: List[Dict[str, Any]], rules_json: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Drop substitution ops S(g->p) that match an enabled SLE rule."""
    allow_pairs = {(r["gold"].upper(), r["pred"].upper())
                   for r in rules_json.get("rules", [])
                   if r.get("enabled", True) and r.get("type") == "S"}
    kept, dropped = [], []
    for o in ops:
        if o["op"] == "S" and (o["g"].upper(), (o["p"] or "").upper()) in allow_pairs:
            dropped.append(o)
        else:
            kept.append(o)
    return kept, dropped


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
        gold = _g2p_arpabet(ref_text, g2p)
        ops = _align_ops(gold, pred_phones)
        denom = max(1, len(gold))
        per_strict = 100.0 * sum(1 for o in ops if o["op"] in ("S", "I", "D")) / denom
        kept, dropped = _apply_sle_rules(ops, rules)
        per_sle = 100.0 * sum(1 for o in kept if o["op"] in ("S", "I", "D")) / denom

        out.update({
            "ref": {"text": ref_text, "phones": gold},
            "align": {"ops_raw": ops, "per_strict": per_strict},
            "sle": {"ops_after_rules": kept, "dropped_by_rules": dropped, "per_sle": per_sle},
        })

    return out
