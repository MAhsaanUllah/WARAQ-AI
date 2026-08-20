"""Runtime BYOK configuration store (process-scoped, thread-safe)."""

from __future__ import annotations

import threading

from app.core.config import LLMProvider

_lock = threading.Lock()
_runtime: dict = {}


def set_llm_config(provider: LLMProvider, api_key: str) -> None:
    """Store the runtime LLM provider + key."""
    with _lock:
        _runtime["provider"] = provider
        _runtime["api_key"] = api_key.strip()


def get_llm_config() -> dict:
    """Return the current runtime LLM config (empty dict if never set)."""
    with _lock:
        return dict(_runtime)


def clear_llm_config() -> None:
    """Wipe the runtime config."""
    with _lock:
        _runtime.clear()


def set_search_config(provider: str, api_key: str) -> None:
    """Store the runtime web-search provider + key."""
    with _lock:
        _runtime["search_provider"] = provider
        _runtime["search_api_key"] = api_key.strip()


def get_search_config() -> dict:
    """Return the current runtime search config."""
    with _lock:
        return {
            "provider": _runtime.get("search_provider"),
            "api_key": _runtime.get("search_api_key"),
        }
