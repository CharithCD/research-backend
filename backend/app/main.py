# backend/app/main.py
from __future__ import annotations
from fastapi import FastAPI, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from .deps import get_settings
from .schemas import HealthOut, GECSchemaOut, PhonemeOut, GECIn, UserResultsOut
from .utils_asr import transcribe_bytes
from .utils_gec import GEC
from .utils_phone import run_phoneme
from .db import init_db, save_phoneme_result, save_grammar_result, fetch_user_results

app = FastAPI(title="Tiny Speech→GEC Backend", version="0.1.3")
settings = get_settings()

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
