"""Metadata extraction engine for construction documents."""

from __future__ import annotations

import re
from pathlib import Path

METADATA_LABELS: dict[str, list[str]] = {
    "document_title": ["Document Title", "Title", "Subject"],
    "revision_number": ["Revision Number", "Revision", "Rev"],
    "project_name": ["Project Name", "Project"],
    "contractor": ["Contractor", "Main Contractor"],
    "consultant": ["Consultant", "Engineer", "Supervision Consultant"],
    "submission_date": ["Submission Date", "Date Submitted", "Submitted Date", "Date"],
    "discipline": ["Discipline", "Trade"],
}

DISCIPLINE_KEYWORDS = {
    "Architectural": ["architectural", "finishes", "floor plan", "elevation"],
    "Structural": ["structural", "concrete", "rebar", "steel", "foundation"],
    "Civil": ["civil", "road", "earthwork", "drainage", "utilities"],
    "Mechanical": ["mechanical", "hvac", "chilled water", "duct", "plumbing"],
    "Electrical": ["electrical", "lighting", "power", "cable", "low current"],
    "QA/QC": ["inspection", "qa/qc", "checklist", "quality"],
    "Contracts": ["contract", "agreement", "payment terms", "contract sum"],
}


def _extract_labeled_value(text: str, labels: list[str]) -> str | None:
    """Extract a value after a label.

    Supports common formats:
    - Label: value
    - Label - value
    - Label | value
    - Label on one line and value on the next line, which often happens in PDFs.
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    labels_sorted = sorted(labels, key=len, reverse=True)

    for index, line in enumerate(lines):
        for label in labels_sorted:
            label_lower = label.lower()
            line_lower = line.lower()

            if line_lower == label_lower:
                if index + 1 < len(lines):
                    return re.sub(r"\s+", " ", lines[index + 1]).strip() or None

            if line_lower.startswith(label_lower):
                rest = line[len(label):].strip()
                if rest.startswith((":", "-", "|")):
                    value = rest[1:].strip()
                    return re.sub(r"\s+", " ", value).strip() or None

    return None


def _extract_revision(text: str, filename: str) -> str | None:
    labeled = _extract_labeled_value(text, METADATA_LABELS["revision_number"])
    if labeled:
        return labeled
    patterns = [
        r"(?i)\bRev(?:ision)?\s*[:\- ]\s*([A-Z0-9.]+)\b",
        r"(?i)\bR(?:ev)?([0-9]{1,2})\b",
    ]
    for source in (filename, text):
        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                return match.group(1)
    return None


def _extract_date(text: str) -> str | None:
    labeled = _extract_labeled_value(text, METADATA_LABELS["submission_date"])
    if labeled:
        return labeled
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{2}/\d{2}/\d{4}\b",
        r"\b\d{2}-\d{2}-\d{4}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _infer_title(text: str, filename: str) -> str | None:
    labeled = _extract_labeled_value(text, METADATA_LABELS["document_title"])
    if labeled:
        return labeled
    for line in text.splitlines():
        clean = line.strip()
        if len(clean) > 5 and ":" not in clean:
            return clean
    return Path(filename).stem.replace("_", " ").title() if filename else None


def _infer_discipline(text: str) -> str | None:
    labeled = _extract_labeled_value(text, METADATA_LABELS["discipline"])
    if labeled:
        return labeled
    lowered = text.lower()
    best = None
    best_hits = 0
    for discipline, keywords in DISCIPLINE_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in lowered)
        if hits > best_hits:
            best = discipline
            best_hits = hits
    return best


def extract_metadata(text: str, filename: str = "") -> dict[str, str | None]:
    """Extract the required metadata fields from text."""
    return {
        "document_title": _infer_title(text, filename),
        "revision_number": _extract_revision(text, filename),
        "project_name": _extract_labeled_value(text, METADATA_LABELS["project_name"]),
        "contractor": _extract_labeled_value(text, METADATA_LABELS["contractor"]),
        "consultant": _extract_labeled_value(text, METADATA_LABELS["consultant"]),
        "submission_date": _extract_date(text),
        "discipline": _infer_discipline(text),
    }
