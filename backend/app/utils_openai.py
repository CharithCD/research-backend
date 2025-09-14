
from __future__ import annotations
import openai
import json
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

SYSTEM_PROMPT = """You are a concise learning coach. Output JSON only.
Keys: headline (<= 180 chars), focus (array of <=3 short items).
Tone: motivational but factual. No emojis."""

async def generate_insight_openai(payload: dict) -> dict | None:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return None # Optional feature, so don't raise an error

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(payload)}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            timeout=8.0,
        )
        return json.loads(response.choices[0].message.content)
    except (openai.APIError, json.JSONDecodeError) as e:
        print(f"[WARN] OpenAI insight generation failed: {e}")
        return None
