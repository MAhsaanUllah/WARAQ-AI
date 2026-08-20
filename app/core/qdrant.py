"""Qdrant access layer — shared async client."""

from qdrant_client import AsyncQdrantClient

from app.core.config import get_settings

_client: AsyncQdrantClient | None = None


def get_client() -> AsyncQdrantClient:
    """Lazily instantiate and cache the shared async Qdrant client."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key.get_secret_value() or None,
        )
    return _client


async def ping_qdrant() -> bool:
    """Return True if Qdrant responds to a lightweight info call."""
    try:
        await get_client().info()
        return True
    except Exception:
        return False


async def close_client() -> None:
    """Gracefully close the shared client (used on app shutdown)."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None
