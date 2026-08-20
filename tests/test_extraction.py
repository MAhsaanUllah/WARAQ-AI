"""Stage 1a tests: pymupdf extraction — pages, text, bbox metadata."""

import pymupdf

from app.services.extraction import ExtractionError, extract_document


def test_extracts_text_and_page_count(one_page_pdf: bytes) -> None:
    doc = extract_document(one_page_pdf, "one_page.pdf")
    assert doc.filename == "one_page.pdf"
    assert len(doc.pages) == 1
    page = doc.pages[0]
    assert page.page_number == 1
    assert "quick brown fox" in page.text


def test_multi_page_preserves_order(three_page_pdf: bytes) -> None:
    doc = extract_document(three_page_pdf, "three_page.pdf")
    assert len(doc.pages) == 3
    assert [p.page_number for p in doc.pages] == [1, 2, 3]
    # Same text repeated on all three pages — page numbers are distinct.
    assert doc.pages[0].text == doc.pages[1].text == doc.pages[2].text


def test_bboxes_capture_line_positions(one_page_pdf: bytes) -> None:
    doc = extract_document(one_page_pdf, "one_page.pdf")
    bboxes = doc.pages[0].bboxes
    assert len(bboxes) > 0
    # Bboxes are in reading order: top line has the smallest y0.
    assert bboxes[0].y0 < bboxes[-1].y0
    # Bbox is inside the A4 page (595 x 842 pt).
    for b in bboxes:
        assert b.x0 >= 0 and b.x1 <= 595
        assert b.y0 >= 0 and b.y1 <= 842
        assert b.x0 < b.x1 and b.y0 < b.y1


def test_bboxes_match_line_count(one_page_pdf: bytes) -> None:
    """One bbox per non-empty line in the extracted text."""
    doc = extract_document(one_page_pdf, "one_page.pdf")
    page = doc.pages[0]
    expected_lines = [l for l in page.text.split("\n") if l.strip()]
    assert len(page.bboxes) == len(expected_lines)


def test_rejects_non_pdf() -> None:
    try:
        extract_document(b"this is not a pdf at all", "fake.pdf")
    except ExtractionError as exc:
        assert "unable to open PDF" in str(exc)
    else:
        raise AssertionError("expected ExtractionError for non-PDF bytes")


def test_rejects_empty_pdf() -> None:
    """A PDF with no text layer must be rejected, not silently ingested."""
    doc = pymupdf.open()
    try:
        doc.new_page(width=595, height=842)  # blank page, no text
        data = doc.tobytes()
    finally:
        doc.close()

    try:
        extract_document(data, "blank.pdf")
    except ExtractionError as exc:
        assert "no extractable text" in str(exc)
    else:
        raise AssertionError("expected ExtractionError for blank PDF")
