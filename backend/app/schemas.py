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

class PhonemeOut(BaseModel):
    pred_phones: List[str]
    ref: Optional[Dict[str, Any]] = None
    align: Optional[Dict[str, Any]] = None
    sle: Optional[Dict[str, Any]] = None

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

class AnalyticsGrammar(BaseModel):
    edits_per_100w_avg: Optional[float] = None
    latency_ms_p50: Optional[int] = None

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
