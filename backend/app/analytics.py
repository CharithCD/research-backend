
from __future__ import annotations
import datetime as dt
import json
from collections import Counter
from typing import Any, Dict, List, Tuple

import numpy as np
import pytz

from . import db
from .deps import get_settings
from .utils_openai import generate_insight_openai


def now_tz(timezone: str) -> dt.datetime:
    return dt.datetime.now(pytz.timezone(timezone))

def extract_sub_pairs(ops_raw: str | List[Dict]) -> List[Tuple[str, str]]:
    pairs = []
    if not ops_raw:
        return pairs
    
    data = ops_raw
    if isinstance(ops_raw, str):
        try:
            data = json.loads(ops_raw)
        except json.JSONDecodeError:
            return pairs

    if isinstance(data, list):
        for op in data:
            if isinstance(op, dict) and op.get("op") == "S" and op.get("g") and op.get("p"):
                pairs.append((op["g"], op["p"]))
    return pairs

async def compute_last7d(user_id: str) -> dict:
    settings = get_settings()
    WINDOW_DAYS = 7
    CACHE_TTL_HOURS = settings.ANALYTICS_CACHE_TTL_HOURS
    TZ = settings.TIMEZONE

    end_ts = now_tz(TZ)
    start_ts = end_ts - dt.timedelta(days=WINDOW_DAYS)

    phoneme_results = await db.get_phoneme_results_last_n_days(user_id, days=WINDOW_DAYS)
    grammar_results = await db.get_grammar_results_last_n_days(user_id, days=WINDOW_DAYS)

    # --- Metrics --- 
    attempts_phoneme = len(phoneme_results)
    attempts_grammar = len(grammar_results)

    per_vals = [r.per_sle for r in phoneme_results if r.per_sle is not None]
    per_sle_avg = round(float(np.mean(per_vals)), 2) if per_vals else None
    per_sle_median = round(float(np.median(per_vals)), 2) if per_vals else None

    edits100 = []
    latencies = []
    for r in grammar_results:
        edits = json.loads(r.edits) if isinstance(r.edits, str) else (r.edits or [])
        words = max(1, len((r.final_text or "").split()))
        edits100.append(len(edits) * 100.0 / words)
        if r.latency_ms is not None:
            latencies.append(r.latency_ms)

    edits_per_100w_avg = round(float(np.mean(edits100)), 2) if edits100 else None
    latency_ms_p50 = int(np.percentile(latencies, 50)) if latencies else None

    subs_counts = Counter()
    for r in phoneme_results:
        for ref, hyp in extract_sub_pairs(r.ops_raw):
            subs_counts[f"{ref}->{hyp}"] += 1
    top_subs = [{"pair": k, "count": v} for k, v in subs_counts.most_common(5)]

    badge = "Most Improved" if (per_sle_avg is not None and per_sle_avg < 15) else "Keep Going"

    # --- LLM Insight --- 
    insight_payload = {
        "pronunciation": {"avg_per_sle": per_sle_avg, "median_per_sle": per_sle_median, "top_phone_subs": top_subs},
        "grammar": {"edits_per_100w_avg": edits_per_100w_avg, "latency_ms_p50": latency_ms_p50},
        "attempts": {"phoneme": attempts_phoneme, "grammar": attempts_grammar},
        "badge": badge
    }
    insight = await generate_insight_openai(insight_payload)
    headline = insight["headline"] if insight else "Keep up the great work! Practice regularly to improve your scores."

    # --- Final Payload --- 
    now = dt.datetime.utcnow()
    return {
        "user_id": user_id,
        "window_label": f"{WINDOW_DAYS}d",
        "from_ts": start_ts,
        "to_ts": end_ts,
        "attempts_phoneme": attempts_phoneme,
        "attempts_grammar": attempts_grammar,
        "per_sle_avg": per_sle_avg,
        "per_sle_median": per_sle_median,
        "edits_per_100w_avg": edits_per_100w_avg,
        "latency_ms_p50": latency_ms_p50,
        "top_phone_subs": top_subs,
        "top_grammar_errors": [], # Placeholder
        "badge": badge,
        "headline_msg": headline,
        "updated_at": now,
        "expires_at": now + dt.timedelta(hours=CACHE_TTL_HOURS)
    }
