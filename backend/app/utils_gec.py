from __future__ import annotations
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import List, Dict, Any, Tuple
import uuid, time, difflib, torch, re

def _inflect_like(src_head: str, base: str) -> str:
    s = src_head.lower()
    if s.endswith("ed"):
        return base + "ed"       # discussed -> discussed
    if s.endswith("ing"):
        return base + "ing"      # discussing -> discussing
    if s.endswith("es"):
        return base + "es"       # discusses -> discusses
    if s.endswith("s"):
        return base + "s"        # discuss -> discusses (best-effort)
    return base


# ========= SLE Guardrails (your list) =========
# (rule_id, base_pattern, policy, reason, category-as-type, canonical replacement or None)
SLE_RULES = [
    ("SLE-PREP-001", "discuss about", "suppress_autocorrect", "Accepted SLE preposition use", "PREP", "discuss"),
    ("SLE-PREP-002", "comprise of", "suppress_autocorrect", "Accepted SLE variant", "PREP", "comprise"),
    ("SLE-PREP-003", "request for", "suppress_autocorrect", "Accepted SLE variant", "PREP", "request"),
    ("SLE-PREP-004", "conducive for", "suppress_autocorrect", "Accepted SLE variant", "PREP", "conducive to"),
    ("SLE-TAGQ-001", "isn’t it", "suggest_review", "Common SLE tag question", "TAGQ", None),
    ("SLE-TAGQ-002", "isn't it", "suggest_review", "Common SLE tag question", "TAGQ", None),
    ("SLE-TAGQ-003", " no?", "suggest_review", "SLE tag particle", "TAGQ", None),
    ("SLE-LEX-001", "poya", "suppress_autocorrect", "SLE cultural term", "LEX", None),
    ("SLE-LEX-002", "z-score", "suppress_autocorrect", "SLE academic term", "LEX", None),
    ("SLE-LEX-003", "a/l", "suppress_autocorrect", "SLE exam term", "LEX", None),
    ("SLE-LEX-004", "o/l", "suppress_autocorrect", "SLE exam term", "LEX", None),
    ("SLE-LEX-005", "rubber slippers", "suppress_autocorrect", "SLE lexical item", "LEX", None),
    ("SLE-LEX-006", "three-wheeler", "suppress_autocorrect", "SLE lexical item", "LEX", None),
    ("SLE-LEX-007", "trishaw", "suppress_autocorrect", "SLE lexical item", "LEX", None),
    ("SLE-LEX-008", "short eats", "suppress_autocorrect", "SLE lexical item", "LEX", None),
    ("SLE-LEX-009", "kade", "suppress_autocorrect", "SLE lexical item", "LEX", None),
    ("SLE-LEX-010", "link language", "suppress_autocorrect", "SLE lexical/phrase", "LEX", None),
    ("SLE-PV-001", "cope up with", "suggest_review", "Frequent SLE usage; review before change", "PV", None),
]

def _infl_regex(base: str) -> re.Pattern:
    """Match simple inflections on the first word: discuss(ed|es|ing) about"""
    base = base.strip().lower()
    parts = base.split()
    if not parts:
        return re.compile(re.escape(base), flags=re.IGNORECASE)
    head = parts[0]
    rest = " ".join(parts[1:])
    head_re = rf"{re.escape(head)}(ed|es|ing)?"
    if rest:
        pat = rf"\b{head_re}\s+{re.escape(rest)}\b"
    else:
        pat = rf"\b{head_re}\b"
    return re.compile(pat, flags=re.IGNORECASE)

SLE_COMPILED = [
    {
        "rule_id": rid,
        "pattern": pat,
        "regex": _infl_regex(pat),
        "policy": policy,
        "reason": reason,
        "etype": etype,     # this becomes the edit "type"
        "canonical": canon  # None means we just flag, not replace
    }
    for (rid, pat, policy, reason, etype, canon) in SLE_RULES
]

def _token_span_from_match(src: str, m: re.Match) -> Tuple[int, int, str]:
    toks = src.split()
    joined = " ".join(toks)
    start_char, end_char = m.start(), m.end()
    idxs = []
    c = 0
    for i, t in enumerate(toks):
        s, e = c, c + len(t)
        if not (e <= start_char or end_char <= s):
            idxs.append(i)
        c = e + 1
    if not idxs:
        return 0, 0, ""
    s_idx, e_idx = idxs[0], idxs[-1] + 1
    return s_idx, e_idx, " ".join(toks[s_idx:e_idx])

def find_guardrail_hits(src: str) -> List[Dict[str, Any]]:
    hits = []
    for r in SLE_COMPILED:
        for m in r["regex"].finditer(src):
            s, e, span_txt = _token_span_from_match(src, m)
            hits.append({
                "rule_id": r["rule_id"],
                "policy": r["policy"],
                "reason": r["reason"],
                "type": r["etype"],
                "span": {"start_tok": s, "end_tok": e, "text": span_txt},
                "canonical": r["canonical"],
            })
    return hits

def synthesize_edits_from_hits(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edits: List[Dict[str, Any]] = []
    for h in hits:
        if h["canonical"]:
            head = (h["span"]["text"].split() or [""])[0]
            replacement = _inflect_like(head, h["canonical"])
            edits.append({
                "type": h["type"],
                "span_src": h["span"],
                "replacement": replacement,
                "guardrail": {
                    "rule_id": h["rule_id"],
                    "policy": h["policy"],
                    "reason": h["reason"]
                }
            })

    return edits

def build_token_diff_edits(src: str, hyp: str) -> List[Dict[str, Any]]:
    s_toks, h_toks = src.split(), hyp.split()
    sm = difflib.SequenceMatcher(a=s_toks, b=h_toks)
    edits: List[Dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        etype = 'SUB' if tag == 'replace' else ('DEL' if tag == 'delete' else 'INS')
        span_txt = " ".join(s_toks[i1:i2])
        repl_txt = " ".join(h_toks[j1:j2])
        edits.append({
            "type": etype,  # may be refined by guardrails/heuristics below
            "span_src": {"start_tok": i1, "end_tok": i2, "text": span_txt},
            "replacement": repl_txt
        })
    return edits

# --- lightweight heuristics to label model edits when no guardrail applies
_PUNCT_RE = re.compile(r"^[^\w\s]+$")
_VERB_AUX = {"am","is","are","was","were","be","being","been","has","have","had","do","does","did"}
def classify_edit(e: Dict[str, Any]) -> str:
    src = e["span_src"]["text"]
    repl = e.get("replacement","")
    if src and repl and src.lower() == repl.lower() and src != repl:
        return "ORTH"          # case-only change
    if _PUNCT_RE.fullmatch(src or "") or _PUNCT_RE.fullmatch(repl or ""):
        return "PUNCT"
    # very coarse verb-ish heuristic
    s_tok = (src.split() or [""])[0].lower()
    r_tok = (repl.split() or [""])[0].lower()
    if s_tok in _VERB_AUX or r_tok in _VERB_AUX or s_tok.endswith(("ed","ing","es")) or r_tok.endswith(("ed","ing","es")):
        return "VERB"
    return e["type"]  # keep SUB/INS/DEL when unknown

def _overlap(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    sa, ea = a["span_src"]["start_tok"], a["span_src"]["end_tok"]
    sb, eb = b["span_src"]["start_tok"], b["span_src"]["end_tok"]
    return not (ea <= sb or eb <= sa)

# ========= GEC wrapper =========
class GEC:
    def __init__(self, model_id: str, token: str | None = None):
        tok_kwargs = {"use_fast": True}
        if token:
            tok_kwargs["token"] = token
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tok_kwargs)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id, use_safetensors=True)
        self.device = torch.device("cpu")
        self.model.to(self.device).eval()

    def _model_correct(self, text: str, max_new_tokens: int = 64) -> str:
        inputs = self.tokenizer([text], return_tensors="pt", truncation=True, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model.generate(
                **inputs, do_sample=False, num_beams=4, max_new_tokens=max_new_tokens, early_stopping=True
            )
        return self.tokenizer.decode(out[0], skip_special_tokens=True).strip() or text

    def respond(self, text: str, sle_mode: bool = True, return_edits: bool = True, max_new_tokens: int = 96):
        t0 = time.time()
        raw = self._model_correct(text, max_new_tokens=max_new_tokens)

        # 1) Model-proposed edits (diff)
        model_edits = build_token_diff_edits(text, raw) if (return_edits or sle_mode) else []

        # 2) Guardrail hits
        hits = find_guardrail_hits(text) if sle_mode else []

        # 3) Synthesize edits from guardrails (e.g., PREP discussed about→discuss)
        synth_edits = synthesize_edits_from_hits(hits) if (return_edits or sle_mode) else []

        # 4) Merge edits with guardrail precedence:
        #    - If a synth (guardrail) edit overlaps a model edit, KEEP the synth and DROP the model edit.
        #    - Otherwise include both.
        def _overlap(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
            sa, ea = a["span_src"]["start_tok"], a["span_src"]["end_tok"]
            sb, eb = b["span_src"]["start_tok"], b["span_src"]["end_tok"]
            return not (ea <= sb or eb <= sa)

        edits = []
        # start with all synth (typed) edits
        for s in synth_edits:
            # ensure it has explicit type and guardrail already
            if "type" not in s:
                s["type"] = "SUB"
            edits.append(s)

        # add model edits only if they don't overlap any synth edit
        for me in model_edits:
            if any(_overlap(me, se) for se in edits):
                continue  # skip generic edit; guardrail-typed edit wins
            edits.append(me)


        # 5) Ensure every edit has a type:
        #    - if guardrail attached: use its type (PREP/TAGQ/LEX/PV)
        #    - else: classify heuristically (VERB/ORTH/PUNCT/…)
        for e in edits:
            if "guardrail" in e and e["guardrail"]:
                # keep the SLE type already set via synth
                continue
            e["type"] = classify_edit(e)

        # 6) Policy → final_text:
        #    suppress_autocorrect → DO NOT apply overlapping edits (keep original span)
        #    suggest_review       → apply edits, but surface guardrail in payload
        toks = text.split()
        def _allowed(edit: Dict[str, Any]) -> bool:
            g = edit.get("guardrail")
            if g and g.get("policy") == "suppress_autocorrect":
                return False
            # block if overlaps any hit with suppress_autocorrect
            for h in hits:
                if h["policy"] != "suppress_autocorrect":
                    continue
                ha, hb = h["span"]["start_tok"], h["span"]["end_tok"]
                ea, eb = edit["span_src"]["start_tok"], edit["span_src"]["end_tok"]
                if not (eb <= ha or hb <= ea):
                    return False
            return True

        for e in sorted(edits, key=lambda x: (x["span_src"]["start_tok"], x["span_src"]["end_tok"]), reverse=True):
            if not _allowed(e):
                continue
            s, ee = e["span_src"]["start_tok"], e["span_src"]["end_tok"]
            repl_tokens = e["replacement"].split() if e.get("replacement") else []
            toks[s:ee] = repl_tokens
        final_text = " ".join(toks)

        payload = {
            "id": f"utt_{uuid.uuid4().hex[:8]}",
            "input": text,
            "model": {"hf_id": self.model_id, "device": "cpu"},
            "gec": {
                "raw_corrected": raw,
                "edits": edits,
                "final_text": final_text
            },
            "guardrails": [
                {"rule_id": h["rule_id"], "policy": h["policy"], "reason": h["reason"], "type": h["type"], "span": h["span"]}
                for h in hits
            ],
            "metrics": {"latency_ms": int((time.time() - t0) * 1000)}
        }
        return payload
