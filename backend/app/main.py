# backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .deps import get_settings
from .schemas import HealthOut, GECSchemaOut, PhonemeOut, GECIn, UserResultsOut
from .utils_asr import transcribe_bytes
from .utils_gec import GEC
from .utils_phone import run_phoneme
from .db import init_db, save_phoneme_result, save_grammar_result, fetch_user_results
from .utils_openai import transcribe_audio_with_openai

app = FastAPI(title="Tiny Speech→GEC Backend", version="0.1.5")
settings = get_settings()

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def _init():
    await init_db()

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

# ---- Grammar
@app.post("/gec/correct", response_model=GECSchemaOut)
async def gec_correct(payload: GECIn):
    gec = get_gec()
    result = gec.respond(
        payload.text,
        sle_mode=payload.sle_mode,
        return_edits=payload.return_edits,
        max_new_tokens=payload.max_new_tokens,
    )
    await save_grammar_result(user_id=payload.user_id, input_text=payload.text, result=result)
    return result

@app.post("/gec/speech", response_model=GECSchemaOut)
async def gec_speech(
    file: UploadFile = File(...),
    sle_mode: bool = True,
    return_edits: bool = True,
    user_id: str = Form(...),                         # <— user_id in body (form)
):
    gec = get_gec()
    audio = await file.read()
    text, segs, info = transcribe_bytes(audio, language="en", model_size=settings.WHISPER_SIZE)
    result = gec.respond(text, sle_mode=sle_mode, return_edits=return_edits)
    await save_grammar_result(user_id=user_id, input_text=text, result=result)
    return result

# ---- Phoneme
@app.post("/phoneme/align", response_model=PhonemeOut)
async def phoneme_align(
    file: UploadFile = File(...),
    user_id: str = Form(...),                         # <— user_id in body (form)
    ref_text: str | None = Form(None),
):
    audio = await file.read()
    result = run_phoneme(audio, ref_text=ref_text)
    await save_phoneme_result(user_id=user_id, audio_bytes=audio, result=result)
    return result

# ---- Read API
@app.get("/user/{user_id}/results", response_model=UserResultsOut)
async def get_user_results(user_id: str, limit: int = Query(50, ge=1, le=500)):
    data = await fetch_user_results(user_id=user_id, limit=limit)
    return UserResultsOut(user_id=user_id, **data)

@app.post("/analyze/both")
async def analyze_both(
    file: UploadFile = File(...),
    text: str | None = Form(None),
    user_id: str | None = Form(None),
    sle_mode: bool = Form(True),
    return_edits: bool = Form(True),
):
    """
    Returns BOTH:
      - phoneme alignment (pred vs ref_text = 'text')
      - grammar correction over the same 'text'
    Also persists both results if user_id provided.
    If 'text' is not provided, it will be transcribed from the audio using OpenAI Whisper.
    """
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

    # 1) Phoneme alignment (audio vs provided text)
    phoneme_result = run_phoneme(audio, ref_text=text_to_use)

    # 2) Grammar correction on the provided text
    grammar_result = gec.respond(
        text_to_use, sle_mode=sle_mode, return_edits=return_edits
    )

    # 3) Persist (optional)
    try:
        if user_id:
            # store separately so each table row stands alone
            await save_phoneme_result(user_id=user_id, audio_bytes=audio, result=phoneme_result)
            await save_grammar_result(user_id=user_id, input_text=text_to_use, result=grammar_result)
    except Exception as e:
        # Don't fail the request if DB write has issues; just return data.
        print(f"[WARN] DB save failed: {e}")

    return {
        "input": {"text": text_to_use, "has_audio": True, "transcribed_text": transcribed_text},
        "phoneme": phoneme_result,
        "grammar": grammar_result,
    }
