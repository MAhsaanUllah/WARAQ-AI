"""Shared fixtures for ingestion tests.

A minimal, deterministic PDF generator built on pymupdf (no external test
assets). Pages are A4 with wrapped paragraphs, so chunking behavior is
predictable across tests.
"""

from __future__ import annotations

import pymupdf
import pytest

TEST_USER_ID = "test-user-123"

# ~40 words per paragraph: short enough that a paragraph fits well under
# chunk_size but long enough to exercise overlap across paragraphs.
PARA_A = (
    "Alpha. The quick brown fox jumps over the lazy dog while the sun sets "
    "behind the mountains and the river flows gently through the valley, "
    "carrying leaves downstream toward the distant ocean horizon."
)
PARA_B = (
    "Beta. In the heart of the forest a lone owl hoots at the moon, "
    "crickets answer in chorus, and the wind whispers secrets through the "
    "ancient pines swaying under a canopy of silver stars."
)
PARA_C = (
    "Gamma. Data pipelines deliver the answer, embeddings map meaning, "
    "and retrieval ranks what matters most when the user asks a question "
    "about a document they uploaded only moments ago."
)
PARA_D = (
    "Delta. A single paragraph longer than the chunk size exercises the "
    "hard-cut fallback when no sentence boundary is near enough to break at."
)


def _build_pdf(pages: list[str], *, size: tuple[float, float] = (595, 842)) -> bytes:
    """Render page texts into an A4 PDF and return the bytes."""
    doc = pymupdf.open()
    try:
        for page_text in pages:
            page = doc.new_page(width=size[0], height=size[1])
            y = 72
            for line in page_text.splitlines():
                page.insert_text((72, y), line, fontsize=11)
                y += 16
    finally:
        data = doc.tobytes()
        doc.close()
    return data


def _wrap(text: str, width: int = 80) -> str:
    """Naive word-wrap for fixture text (keeps lines under `width` chars)."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


@pytest.fixture
def one_page_pdf() -> bytes:
    """A single page with two wrapped paragraphs."""
    return _build_pdf([_wrap(PARA_A + "\n\n" + PARA_B)])


@pytest.fixture
def three_page_pdf() -> bytes:
    """Three pages, two paragraphs each — exercises page boundaries."""
    return _build_pdf([_wrap(PARA_A + "\n\n" + PARA_B)] * 3)


@pytest.fixture
def long_paragraph_pdf() -> bytes:
    """A single page whose paragraph is longer than the default chunk size."""
    words = ("word " * 400).strip()  # ~2000 chars > 800
    return _build_pdf([_wrap(words, width=80)])
