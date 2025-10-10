from __future__ import annotations
import datetime as dt
import json
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz

from .deps import get_settings
from .schemas import HealthOut, GECSchemaOut, PhonemeOut, GECIn, UserResultsOut, AnalyticsOut, PaginatedWeaknessesOut
from .utils_asr import transcribe_bytes, convert_audio_to_mono_wav
from .utils_gec import GEC
from .utils_phone import run_phoneme
from . import db
from .utils_openai import transcribe_audio_with_openai, categorize_grammar_error
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
    # Convert SQLAlchemy row object to a dictionary for easier access
    data_dict = data._asdict()
    return {
        "user_id": data_dict["user_id"],
        "window": data_dict["window_label"],
        "range": {"from_ts": data_dict["from_ts"].isoformat(), "to_ts": data_dict["to_ts"].isoformat()},
        "attempts": {"phoneme": data_dict["attempts_phoneme"], "grammar": data_dict["attempts_grammar"]},
        "pronunciation": {
            "avg_per_sle": data_dict["per_sle_avg"],
            "median_per_sle": data_dict["per_sle_median"],
            "top_phone_subs": json.loads(data_dict["top_phone_subs"]) if isinstance(data_dict["top_phone_subs"], str) else data_dict["top_phone_subs"],
            "top_pronunciation_weaknesses": json.loads(data_dict["top_pronunciation_weaknesses"]) if isinstance(data_dict["top_pronunciation_weaknesses"], str) else data_dict["top_pronunciation_weaknesses"],
        },
        "grammar": {
            "edits_per_100w_avg": data_dict["edits_per_100w_avg"], 
            "latency_ms_p50": data_dict["latency_ms_p50"],
            "top_grammar_weaknesses": json.loads(data_dict["top_grammar_weaknesses"]) if isinstance(data_dict["top_grammar_weaknesses"], str) else data_dict["top_grammar_weaknesses"],
        },
        "badge": data_dict["badge"],
        "headline_msg": data_dict["headline_msg"],
        "updated_at": data_dict["updated_at"].isoformat(),
        "expires_at": data_dict["expires_at"].isoformat(),
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


@app.get("/weaknesses/{user_id}", response_model=PaginatedWeaknessesOut)
async def get_user_weaknesses(
    user_id: str, 
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """Fetches a paginated list of all weaknesses for a user."""
    items = await db.fetch_user_weaknesses(user_id, offset=offset, limit=limit)
    return PaginatedWeaknessesOut(items=items)


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

    # Categorize grammar error
    if result.get("gec") and result["gec"].get("final_text"):
        categories = await categorize_grammar_error(payload.text, result["gec"]["final_text"])
        if categories:
            result["weakness_categories"] = categories

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

    # Categorize grammar error
    if result.get("gec") and result["gec"].get("final_text"):
        categories = await categorize_grammar_error(text, result["gec"]["final_text"])
        if categories:
            result["weakness_categories"] = categories

    await db.save_grammar_result(user_id=user_id, input_text=text, result=result)
    return result

@app.post("/phoneme/align", response_model=PhonemeOut)
async def phoneme_align(
    file: UploadFile = File(...),
    user_id: str = Form(...),
    ref_text: str | None = Form(None),
):
    audio = await file.read()
    converted_audio = convert_audio_to_mono_wav(audio)
    result = run_phoneme(converted_audio, ref_text=ref_text)
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

    converted_audio = convert_audio_to_mono_wav(audio)
    phoneme_result = run_phoneme(converted_audio, ref_text=text_to_use)
    grammar_result = gec.respond(
        text_to_use, sle_mode=sle_mode, return_edits=return_edits
    )

    # Categorize grammar error
    if grammar_result.get("gec") and grammar_result["gec"].get("final_text"):
        categories = await categorize_grammar_error(text_to_use, grammar_result["gec"]["final_text"])
        if categories:
            grammar_result["weakness_categories"] = categories

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
