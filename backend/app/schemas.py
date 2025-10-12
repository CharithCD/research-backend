from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class GECIn(BaseModel):
    text: str
    sle_mode: bool = True
    return_edits: bool = True
    max_new_tokens: int = 96
    user_id: str  # <-- required in body

class GECSchemaOut(BaseModel):
    id: str
    input: str
    model: Dict[str, Any]
    gec: Dict[str, Any]
    guardrails: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None

class PhonemeError(BaseModel):
    op: str
    g: Optional[str] = None
    p: Optional[str] = None
    i: int
    j: int

class WordAnalysis(BaseModel):
    word: str
    is_correct: bool
    phoneme_errors: List[PhonemeError]

class Reference(BaseModel):
    text: str
    phones: List[str]
    words: List[Dict[str, Any]]

class Alignment(BaseModel):
    ops_raw: List[PhonemeError]
    per_strict: float

class SLEAnalysis(BaseModel):
    ops_after_rules: List[PhonemeError]
    dropped_by_rules: List[PhonemeError]
    per_sle: float

class PhonemeOut(BaseModel):
    pred_phones: List[str]
    ref: Optional[Reference] = None
    align: Optional[Alignment] = None
    sle: Optional[SLEAnalysis] = None
    wer: Optional[float] = None
    word_analysis: Optional[List[WordAnalysis]] = None
    weakness_categories: Optional[List[str]] = None

class HealthOut(BaseModel):
    status: str
    asr_ready: bool
    gec_ready: bool

class UserResultsOut(BaseModel):
    user_id: str
    grammar: List[Dict[str, Any]]
    phoneme: List[Dict[str, Any]]

# --- Analytics ---

class AnalyticsRange(BaseModel):
    from_ts: str
    to_ts: str

class AnalyticsAttempts(BaseModel):
    phoneme: int
    grammar: int

class AnalyticsPronunciation(BaseModel):
    avg_per_sle: Optional[float] = None
    median_per_sle: Optional[float] = None
    top_phone_subs: List[Dict[str, Any]]
    top_pronunciation_weaknesses: List[Dict[str, Any]]

class AnalyticsGrammar(BaseModel):
    edits_per_100w_avg: Optional[float] = None
    latency_ms_p50: Optional[int] = None
    top_grammar_weaknesses: List[Dict[str, Any]]

class AnalyticsOut(BaseModel):
    user_id: str
    window: str
    range: AnalyticsRange
    attempts: AnalyticsAttempts
    pronunciation: AnalyticsPronunciation
    grammar: AnalyticsGrammar
    badge: str
    headline_msg: str
    updated_at: str
    expires_at: str

# --- Weaknesses ---

class WeaknessOut(BaseModel):
    type: str
    text: str
    categories: List[str]
    created_at: str

class PaginatedWeaknessesOut(BaseModel):
    items: List[WeaknessOut]

# --- Weakness Summary ---

class PronunciationErrorSummary(BaseModel):
    pair: Optional[str] = None
    phoneme: Optional[str] = None
    count: int

class PronunciationSummary(BaseModel):
    most_common_substitutions: List[PronunciationErrorSummary]
    most_common_insertions: List[PronunciationErrorSummary]
    most_common_deletions: List[PronunciationErrorSummary]

class GrammarSummaryItem(BaseModel):
    category: str
    count: int

class WeaknessSummaryOut(BaseModel):
    user_id: str
    pronunciation_summary: PronunciationSummary
    grammar_summary: List[GrammarSummaryItem]

