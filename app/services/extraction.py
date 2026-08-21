"""PDF extraction with pymupdf."""

from __future__ import annotations

import pymupdf

from app.models.ingestion import BBox, Document, Page


class ExtractionError(ValueError):
    """Raised when a PDF cannot be parsed or has no extractable text."""


def extract_document(data: bytes, filename: str) -> Document:
    """Parse PDF bytes into a Document with per-line bbox metadata."""
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ExtractionError(f"unable to open PDF '{filename}': {exc}") from exc

    if len(doc) > 50:
        doc.close()
        raise ExtractionError(f"'{filename}' exceeds portfolio limit of 50 pages.")

    pages: list[Page] = []
    try:
        for page_number, page in enumerate(doc, start=1):
            page_dict = page.get_text("dict")
            text, bboxes = _extract_page(page_dict)
            if text.strip():
                pages.append(
                    Page(
                        page_number=page_number,
                        text=text,
                        bboxes=bboxes,
                    )
                )
    finally:
        doc.close()

    if not pages:
        raise ExtractionError(
            f"'{filename}' contains no extractable text "
            "(is it a scanned image PDF? OCR is not implemented)."
        )

    return Document(filename=filename, pages=pages)


def _extract_page(page_dict: dict) -> tuple[str, list[BBox]]:
    """Flatten a page's text blocks into text plus per-line bounding boxes."""
    text_parts: list[str] = []
    bboxes: list[BBox] = []

    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            line_text = "".join(span["text"] for span in line.get("spans", []))
            if not line_text.strip():
                continue
            text_parts.append(line_text)
            x0, y0, x1, y1 = line["bbox"]
            bboxes.append(BBox(x0=x0, y0=y0, x1=x1, y1=y1))

    return "\n".join(text_parts), bboxes
