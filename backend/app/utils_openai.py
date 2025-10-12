
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


GRAMMAR_TOPICS_PROMPT = """
"present simple", "past simple tense", "future continuous tense", 
"past perfect tense", "present perfect", "future perfect", 
"comparatives and superlatives", "subject verb agreement", 
"articles a an the", "conditionals", "reported speech", 
"passive voice", "modal verbs", "question formation", 
"countable and uncountable nouns", "confusable ex: accept vs except"
"""

GRAMMAR_SYSTEM_PROMPT = f"""You are an expert English grammar teacher. Analyze the following change and categorize the grammatical error based on the user's final corrected text. Choose the most relevant category from the provided list. Your response must be a JSON object with a key 'categories' containing a list of the identified category strings.

Available categories:
{GRAMMAR_TOPICS_PROMPT}
"""

async def categorize_grammar_error(original_text: str, corrected_text: str) -> list[str] | None:
    settings = get_settings()
    if not settings.OPENAI_API_KEY:
        return None

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_prompt = f"Original: {original_text}\nCorrected: {corrected_text}"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": GRAMMAR_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            timeout=8.0,
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("categories", [])
    except (openai.APIError, json.JSONDecodeError) as e:
        print(f"[WARN] OpenAI grammar categorization failed: {e}")
        return None
