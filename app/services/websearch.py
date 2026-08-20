"""Web search for grounded generation (Tavily / Brave, BYOK)."""

from __future__ import annotations

import httpx

from app.core.runtime_config import get_search_config

SEARCH_TIMEOUT = 10.0
DEFAULT_MAX_RESULTS = 5


class WebSearchError(RuntimeError):
    """Raised when a search request fails (provider down, bad key)."""


def search_configured() -> bool:
    """True if a search provider + key is configured."""
    cfg = get_search_config()
    return bool(cfg.get("api_key"))


async def web_search(query: str, max_results: int = DEFAULT_MAX_RESULTS) -> list[dict]:
    """Run a web search via the configured provider."""
    cfg = get_search_config()
    provider = cfg.get("provider", "tavily")
    api_key = cfg.get("api_key", "")

    if not api_key:
        raise WebSearchError("No web search API key configured.")

    if provider == "brave":
        return await _search_brave(query, api_key, max_results)
    return await _search_tavily(query, api_key, max_results)


async def _search_tavily(query: str, api_key: str, max_results: int) -> list[dict]:
    url = "https://api.tavily.com/search"
    payload = {"query": query, "max_results": max_results, "search_depth": "basic"}
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Tavily search failed: {exc}") from exc

    data = response.json()
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("content", ""),
        }
        for r in data.get("results", [])[:max_results]
    ]


async def _search_brave(query: str, api_key: str, max_results: int) -> list[dict]:
    url = "https://api.search.brave.com/res/v1/web/search"
    params = {"q": query, "count": max_results}
    headers = {"X-Subscription-Token": api_key, "Accept": "application/json"}

    async with httpx.AsyncClient(timeout=SEARCH_TIMEOUT) as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise WebSearchError(f"Brave search failed: {exc}") from exc

    data = response.json()
    return [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": r.get("description", ""),
        }
        for r in data.get("web", {}).get("results", [])[:max_results]
    ]
