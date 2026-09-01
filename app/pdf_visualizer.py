"""PDF page rendering and text-only extraction utilities for Week 23."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF


DATE_PATTERN = re.compile(r"\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b")
REVISION_PATTERN = re.compile(r"\b(?:rev(?:ision)?\.?\s*(?:no\.?\s*)?[:#-]?\s*)([A-Z0-9.-]+)", re.IGNORECASE)
DOC_NUMBER_PATTERN = re.compile(
    r"\b(?:document|drawing|dwg|doc|rfi|specification|spec)\s*(?:number|no\.?|#|ref(?:erence)?)?\s*[:#-]?\s*([A-Z0-9][A-Z0-9_./-]{2,})",
    re.IGNORECASE,
)
PROJECT_PATTERN = re.compile(r"\bproject(?:\s+name)?\s*[:#-]\s*(.+)", re.IGNORECASE)
TITLE_PATTERN = re.compile(r"\b(?:document\s+title|drawing\s+title|title)\s*[:#-]\s*(.+)", re.IGNORECASE)
TYPE_PATTERN = re.compile(r"\bdocument\s+type\s*[:#-]\s*(.+)", re.IGNORECASE)


def _safe_line(value: str | None) -> str | None:
    if not value:
        return None
    return value.strip().splitlines()[0].strip() or None


def extract_text_only_fields(text: str) -> dict[str, Any]:
    """Extract a small set of fields using only the PDF text layer.

    This intentionally does not inspect images. It is used as the baseline for
    the Week 23 text-only versus multimodal comparison.
    """

    clean_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    revision_match = REVISION_PATTERN.search(clean_text)
    doc_number_match = DOC_NUMBER_PATTERN.search(clean_text)
    date_match = DATE_PATTERN.search(clean_text)
    project_match = PROJECT_PATTERN.search(clean_text)
    title_match = TITLE_PATTERN.search(clean_text)
    type_match = TYPE_PATTERN.search(clean_text)

    first_lines = clean_text.splitlines()[:5]
    inferred_title = first_lines[0] if first_lines else None

    fields = {
        "document_title": _safe_line(title_match.group(1)) if title_match else inferred_title,
        "document_type": _safe_line(type_match.group(1)) if type_match else None,
        "document_number": doc_number_match.group(1).strip() if doc_number_match else None,
        "revision": revision_match.group(1).strip() if revision_match else None,
        "date": date_match.group(0) if date_match else None,
        "project_name": _safe_line(project_match.group(1)) if project_match else None,
    }
    fields_found = sum(1 for value in fields.values() if value)
    return {
        "method": "pdf_text_layer",
        "characters_extracted": len(clean_text),
        "raw_text_preview": clean_text[:1200],
        "fields": fields,
        "fields_found": fields_found,
        "confidence": round(min(0.95, 0.15 + fields_found * 0.12), 2) if clean_text else 0.0,
    }


def parse_page_numbers(value: str | None) -> list[int] | None:
    """Parse 1-based page numbers from a comma-separated API parameter."""

    if not value:
        return None
    numbers: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        number = int(part)
        if number < 1:
            raise ValueError("Page numbers must start at 1.")
        if number not in numbers:
            numbers.append(number)
    return numbers or None


def _selected_indexes(page_count: int, page_numbers: Iterable[int] | None, max_pages: int) -> list[int]:
    if page_numbers:
        indexes = [number - 1 for number in page_numbers]
        invalid = [index + 1 for index in indexes if index < 0 or index >= page_count]
        if invalid:
            raise ValueError(f"Page number(s) outside the PDF: {invalid}")
        return indexes[:max_pages]
    return list(range(min(page_count, max_pages)))


def render_pdf_pages(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    page_numbers: Iterable[int] | None = None,
    max_pages: int = 5,
    dpi: int = 150,
) -> list[dict[str, Any]]:
    """Render selected PDF pages to PNG and return page text and dimensions."""

    source = Path(pdf_path)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    if max_pages < 1 or max_pages > 50:
        raise ValueError("max_pages must be between 1 and 50.")
    if dpi < 72 or dpi > 300:
        raise ValueError("dpi must be between 72 and 300.")

    document = fitz.open(source)
    try:
        indexes = _selected_indexes(document.page_count, page_numbers, max_pages)
        scale = dpi / 72.0
        matrix = fitz.Matrix(scale, scale)
        pages: list[dict[str, Any]] = []
        for index in indexes:
            page = document.load_page(index)
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = destination / f"page_{index + 1:03d}.png"
            pixmap.save(image_path)
            pages.append(
                {
                    "page_number": index + 1,
                    "image_path": str(image_path),
                    "width": pixmap.width,
                    "height": pixmap.height,
                    "dpi": dpi,
                    "text": page.get_text("text").strip(),
                }
            )
        return pages
    finally:
        document.close()


def read_fixture_id(pdf_path: str | Path) -> str | None:
    """Read the synthetic fixture id embedded in the PDF metadata."""

    document = fitz.open(pdf_path)
    try:
        keywords = str(document.metadata.get("keywords") or "")
    finally:
        document.close()
    marker = "WEEK23_FIXTURE:"
    for item in keywords.split(","):
        item = item.strip()
        if item.startswith(marker):
            return item[len(marker) :].strip() or None
    return None
