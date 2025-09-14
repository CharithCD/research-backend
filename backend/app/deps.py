from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "info"
    CORS_ORIGINS: str = "*"

    # Inference configs
    WHISPER_SIZE: str = "tiny"
    GEC_MODEL_ID: str = "vennify/t5-base-grammar-correction"
    HUGGINGFACE_TOKEN: str | None = None
    OPENAI_API_KEY: str | None = None

    # Analytics
    ANALYTICS_CACHE_TTL_HOURS: int = 24
    TIMEZONE: str = "Asia/Colombo"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
