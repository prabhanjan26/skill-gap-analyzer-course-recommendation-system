"""Application configuration loaded from environment via pydantic-settings.

Single source of truth for all runtime configuration. Values are read from
`backend/.env` (see `.env.example`). Import `get_settings()` anywhere a config
value is needed; the settings object is cached as a singleton.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- LLM (Google Gemini) ---
    gemini_api_key: str = Field(default="your-gemini-api-key-here", alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    # Per-call timeout (seconds). Thinking models (gemini-2.5-*) need more headroom.
    gemini_timeout_seconds: int = Field(default=120, alias="GEMINI_TIMEOUT_SECONDS")

    # --- MongoDB ---
    mongodb_uri: str = Field(default="your-mongodb-connection-string-here", alias="MONGODB_URI")
    mongodb_db_name: str = Field(default="skill_gap_db", alias="MONGODB_DB_NAME")

    # --- ChromaDB ---
    chroma_persist_dir: str = Field(default="./chroma_data", alias="CHROMA_PERSIST_DIR")

    # --- Embeddings ---
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL_NAME")

    # --- Uploads ---
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_file_size_mb: int = Field(default=5, alias="MAX_FILE_SIZE_MB")

    # --- CORS ---
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000"], alias="CORS_ORIGINS"
    )

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        """Accept a JSON list, a comma-separated string, or an actual list."""
        if v is None or v == "":
            return ["http://localhost:3000"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                import json

                try:
                    return json.loads(s)
                except json.JSONDecodeError:
                    pass
            return [origin.strip() for origin in s.split(",") if origin.strip()]
        return v

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()
