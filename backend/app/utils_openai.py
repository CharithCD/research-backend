
from __future__ import annotations
import openai
from fastapi import HTTPException
from .deps import get_settings

async def transcribe_audio_with_openai(audio_bytes: bytes) -> str:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", audio_bytes),
        )
        return response.text
    except openai.APIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
