"""Grounded LLM generation via LiteLLM (BYOK)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import litellm

from app.core.config import get_settings
from app.models.api import Source
from app.models.retrieval import RerankedResult

SYSTEM_PROMPT = """You are Waraq AI, a grounded document assistant. Answer ONLY from the provided context.

CONTEXT RULES:
- Every factual claim must carry a citation marker like [1] or [2] that references the numbered sources below.
- If the context does not contain the answer, say "I couldn't find that in the provided documents." — never invent facts.
- Never mention sources the context does not list.

CONTEXT:
{context}

Answer in Markdown. Cite with [n] after each claim, where n is the source number below.
"""


class LLMNotConfiguredError(RuntimeError):
    """Raised when no LLM provider/key is configured (env or runtime)."""


def _resolve_model(provider_override: str | None = None, api_key_override: str | None = None) -> tuple[str, str]:
    """Resolve the LiteLLM model string + API key.

    Precedence: runtime settings (from request headers) then .env
    (WARAQAI_LLM_PROVIDER / WARAQAI_LLM_API_KEY).
    """
    settings = get_settings()

    provider = provider_override or settings.llm_provider
    api_key = api_key_override or settings.llm_api_key.get_secret_value()

    if not api_key:
        raise LLMNotConfiguredError(
            "No LLM API key configured. Set it in the Settings page (BYOK) "
            "or add WARAQAI_LLM_API_KEY to .env."
        )

    model = (
        _model_for_provider(provider)
        if provider_override
        else settings.llm_model or _model_for_provider(provider)
    )
    return model, api_key


def _model_for_provider(provider: str) -> str:
    """Map a provider to a default LiteLLM model string."""
    defaults = {
        "deepseek": "deepseek/deepseek-chat",
        "gemini": "gemini/gemini-2.0-flash",
        "openai": "openai/gpt-4o-mini",
        "anthropic": "claude-3-5-sonnet-20241022",
        "openrouter": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    }
    return defaults.get(provider, f"{provider}/{provider}")


def build_messages(
    query: str,
    chunks: list[RerankedResult],
    web_context: list[dict] | None = None,
) -> list[dict]:
    """Assemble the system prompt with numbered context plus the question."""
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        page = chunk.page_number
        filename = chunk.filename
        context_blocks.append(f"[{i}] (page {page}, {filename}):\n{chunk.text}")

    if web_context:
        for i, item in enumerate(web_context, start=len(chunks) + 1):
            context_blocks.append(
                f"[{i}] [web] ({item.get('title', 'web')}, {item.get('url', '')}):\n{item.get('snippet', '')}"
            )

    context = "\n\n".join(context_blocks)

    system = SYSTEM_PROMPT.format(context=context)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]


async def generate_answer(
    query: str,
    chunks: list[RerankedResult],
    web_context: list[dict] | None = None,
) -> str:
    """Single-shot grounded answer (non-streaming)."""
    model, api_key = _resolve_model()
    messages = build_messages(query, chunks, web_context)

    response = await litellm.acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        temperature=0.1,
    )
    return response.choices[0].message.content or ""


async def stream_answer(
    query: str,
    chunks: list[RerankedResult],
    web_context: list[dict] | None = None,
    llm_provider: str | None = None,
    llm_api_key: str | None = None,
) -> AsyncIterator[str]:
    """Yield answer tokens as they arrive (for SSE)."""
    model, api_key = _resolve_model(llm_provider, llm_api_key)
    messages = build_messages(query, chunks, web_context)

    stream = await litellm.acompletion(
        model=model,
        messages=messages,
        api_key=api_key,
        temperature=0.1,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


def to_source(chunk: RerankedResult) -> Source:
    """Map a reranked chunk to the contract's Source shape."""
    return Source(
        document_id=chunk.doc_id,
        filename=chunk.filename,
        page=chunk.page_number,
        chunk_hash=chunk.chunk_id,
        bbox=chunk.bbox,
        score=chunk.score,
        snippet=chunk.text.strip()[:300],
    )
