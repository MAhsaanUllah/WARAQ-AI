"""Settings load correctly with defaults, without a .env file present."""

from app.core.config import get_settings


def test_defaults_load() -> None:
    settings = get_settings()
    assert settings.qdrant_url == "http://localhost:6333"
    assert settings.qdrant_collection == "waraq_docs"
    assert settings.llm_provider in {"deepseek", "gemini", "openai", "anthropic"}
    assert settings.chunk_size > 0
    assert settings.top_k_candidates >= settings.top_k_final


def test_cors_origins_parsing() -> None:
    settings = get_settings()
    assert "http://localhost:5173" in settings.cors_origin_list


def test_llm_key_is_secret() -> None:
    # SecretStr must not leak its value through str()/repr()
    settings = get_settings()
    assert settings.llm_api_key.get_secret_value() == ""
    assert "WARAQAI_LLM_API_KEY" not in str(settings.llm_api_key)
