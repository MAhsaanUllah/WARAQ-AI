"""Application configuration via pydantic-settings (WARAQAI_ env prefix)."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["deepseek", "gemini", "openai", "anthropic"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="WARAQAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: SecretStr = SecretStr("")
    qdrant_collection: str = "waraq_docs_v3"

    llm_provider: LLMProvider = "deepseek"
    llm_api_key: SecretStr = SecretStr("")
    llm_model: str = ""

    chunk_size: int = 800
    chunk_overlap: int = 150
    max_upload_mb: int = 50

    top_k_candidates: int = 25
    top_k_final: int = 5

    cors_origins: str = "http://localhost:5173"
    log_level: str = "INFO"

    clerk_secret_key: SecretStr = SecretStr("")
    clerk_authorized_parties: str = "http://localhost:5173,http://localhost:8000"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse the comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def clerk_authorized_parties_list(self) -> list[str]:
        """Parse the comma-separated Clerk authorized parties."""
        return [p.strip() for p in self.clerk_authorized_parties.split(",") if p.strip()]


@lru_cache
def get_settings() -> Settings:
    """Process-wide cached settings (immutable after first load)."""
    return Settings()
