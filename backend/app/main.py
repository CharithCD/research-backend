from __future__ import annotations
import datetime as dt
import json
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

from .deps import get_settings
from .schemas import HealthOut, GECSchemaOut, PhonemeOut, GECIn, UserResultsOut, AnalyticsOut
from .utils_asr import transcribe_bytes
from .utils_gec import GEC
from .utils_phone import run_phoneme
from . import db
from .utils_openai import transcribe_audio_with_openai
from .analytics import compute_last7d
from .jobs import recompute_all_users_analytics

app = FastAPI(title="Tiny Speech→GEC Backend", version="0.2.0")
settings = get_settings()

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

@app.on_event("startup")
async def startup_event():
    await db.init_db()
    # Scheduler for daily analytics job
    scheduler = AsyncIOScheduler(timezone=pytz.timezone(settings.TIMEZONE))
    scheduler.add_job(recompute_all_users_analytics, 'cron', hour=3, minute=0) 
    scheduler.start()
    print(f"Scheduler started. Daily analytics job scheduled for 03:00 {settings.TIMEZONE}.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Lazy GEC loader
_gec = None
def get_gec() -> GEC:
    global _gec
    if _gec is None:
        _gec = GEC(settings.GEC_MODEL_ID, settings.HUGGINGFACE_TOKEN or None)
    return _gec

@app.get("/health", response_model=HealthOut)
async def health():
    return HealthOut(status="ok", asr_ready=True, gec_ready=True)

# ---- Analytics Endpoints ----

def format_analytics_response(data) -> dict:
    return {
        "user_id": data["user_id"],
        "window": data["window_label"],
        "range": {"from_ts": data["from_ts"].isoformat(), "to_ts": data["to_ts"].isoformat()},
        "attempts": {"phoneme": data["attempts_phoneme"], "grammar": data["attempts_grammar"]},
        "pronunciation": {
            "avg_per_sle": data["per_sle_avg"],
            "median_per_sle": data["per_sle_median"],
            "top_phone_subs": json.loads(data["top_phone_subs"]) if isinstance(data["top_phone_subs"], str) else data["top_phone_subs"],
        },
        "grammar": {"edits_per_100w_avg": data["edits_per_100w_avg"], "latency_ms_p50": data["latency_ms_p50"]},
        "badge": data["badge"],
        "headline_msg": data["headline_msg"],
        "updated_at": data["updated_at"].isoformat(),
        "expires_at": data["expires_at"].isoformat(),
    }

@app.get("/analytics/{user_id}", response_model=AnalyticsOut)
async def get_analytics(user_id: str, force: bool = False):
    if not force:
        cached_data = await db.get_user_analytics_cache(user_id)
        if cached_data and cached_data.expires_at.replace(tzinfo=None) > dt.datetime.utcnow():
            return format_analytics_response(cached_data)
    
    analytics_data = await compute_last7d(user_id)
    await db.upsert_user_analytics_cache(analytics_data)
    # Re-fetch from DB to get a consistent row object
    newly_cached_data = await db.get_user_analytics_cache(user_id)
    return format_analytics_response(newly_cached_data)

@app.post("/analytics/{user_id}/recompute", response_model=AnalyticsOut)
async def recompute_analytics(user_id: str, background_tasks: BackgroundTasks):
    analytics_data = await compute_last7d(user_id)
    background_tasks.add_task(db.upsert_user_analytics_cache, analytics_data)
    return format_analytics_response(analytics_data)


# ---- Grammar & Phoneme Endpoints ----

@app.post("/gec/correct", response_model=GECSchemaOut)
async def gec_correct(payload: GECIn):
    gec = get_gec()
    result = gec.respond(
        payload.text,
        sle_mode=payload.sle_mode,
        return_edits=payload.return_edits,
        max_new_tokens=payload.max_new_tokens,
    )
    await db.save_grammar_result(user_id=payload.user_id, input_text=payload.text, result=result)
    return result

@app.post("/gec/speech", response_model=GECSchemaOut)
async def gec_speech(
    file: UploadFile = File(...),
    sle_mode: bool = True,
    return_edits: bool = True,
    user_id: str = Form(...),
):
    gec = get_gec()
    audio = await file.read()
    text, segs, info = transcribe_bytes(audio, language="en", model_size=settings.WHISPER_SIZE)
    result = gec.respond(text, sle_mode=sle_mode, return_edits=return_edits)
    await db.save_grammar_result(user_id=user_id, input_text=text, result=result)
    return result

@app.post("/phoneme/align", response_model=PhonemeOut)
async def phoneme_align(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    ref_text: str | None = Form(None),
):
    audio = await file.read()
    result = run_phoneme(audio, ref_text=ref_text)
    await db.save_phoneme_result(user_id=user_id, audio_bytes=audio, result=result)
    return result

@app.get("/user/{user_id}/results", response_model=UserResultsOut)
async def get_user_results(user_id: str, limit: int = Query(50, ge=1, le=500)):
    data = await db.fetch_user_results(user_id=user_id, limit=limit)
    return UserResultsOut(user_id=user_id, **data)

@app.post("/analyze/both")
async def analyze_both(
    file: UploadFile = File(...),
    text: str | None = Form(None),
    user_id: str | None = Form(None),
    sle_mode: bool = Form(True),
    return_edits: bool = Form(True),
):
    gec = get_gec()

    audio = await file.read()
    if len(audio) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds limit of {MAX_FILE_SIZE // 1024 // 1024}MB")

    transcribed_text = None
    if text is None:
        transcribed_text = await transcribe_audio_with_openai(audio)
        text_to_use = transcribed_text
    else:
        text_to_use = text

    phoneme_result = run_phoneme(audio, ref_text=text_to_use)
    grammar_result = gec.respond(
        text_to_use, sle_mode=sle_mode, return_edits=return_edits
    )

    try:
        if user_id:
            await db.save_phoneme_result(user_id=user_id, audio_bytes=audio, result=phoneme_result)
            await db.save_grammar_result(user_id=user_id, input_text=text_to_use, result=grammar_result)
    except Exception as e:
        print(f"[WARN] DB save failed: {e}")

    return {
        "input": {"text": text_to_use, "has_audio": True, "transcribed_text": transcribed_text},
        "phoneme": phoneme_result,
        "grammar": grammar_result,
    }
