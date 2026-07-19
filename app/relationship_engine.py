"""Document relationship detection for RFIs, drawings, specifications, and meetings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH
from app.repository import get_document, list_documents
from app.relationship_repository import (
    clear_relationship_data,
    save_action_item,
    save_relationship,
)

# Document numbers such as DWG-A-101, SPEC-03-30-00, RFI-015, and MOM-007.
DOCUMENT_IDENTIFIER_RE = re.compile(
    r"\b(?:RFI|DWG|DRG|SPEC|MOM|MIN|MS|MAT|SD|IR|CON)"
    r"[\s:_#-]*(?=[A-Z0-9./_-]*\d)[A-Z0-9]+(?:[-_/.][A-Z0-9]+){0,5}\b",
    re.IGNORECASE,
)
LABELED_IDENTIFIER_RE = re.compile(
    r"(?:Document|Drawing|Specification|RFI|Meeting|Minutes)\s*"
    r"(?:Number|No\.?|Reference)\s*[:#-]\s*"
    r"((?:RFI|DWG|DRG|SPEC|MOM|MIN|MS|MAT|SD|IR|CON)"
    r"[\s:_#-]*(?=[A-Z0-9./_-]*\d)[A-Z0-9]+(?:[-_/.][A-Z0-9]+){0,5})",
    re.IGNORECASE,
)
DATE_RE = re.compile(r"\b(?:20\d{2}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]20\d{2})\b")
ACTION_ITEM_RE = re.compile(
    r"(?:^|[\n;])\s*(?:Action\s*Item|Action|AI)\s*(?:#?\d+)?\s*[:\-]\s*([^\n;]+)",
    re.IGNORECASE,
)
OWNER_RE = re.compile(r"(?:Owner|Responsible|Assigned\s+To)\s*[:\-]\s*([^.;|]+)", re.IGNORECASE)
DUE_RE = re.compile(r"(?:Due\s*Date|Due)\s*[:\-]\s*([^.;|]+)", re.IGNORECASE)
STATUS_RE = re.compile(r"Status\s*[:\-]\s*([^.;|]+)", re.IGNORECASE)
TOKEN_RE = re.compile(r"[a-z0-9]{3,}")
STOP_WORDS = {
    "this", "that", "with", "from", "document", "project", "construction", "review",
    "submission", "information", "requirements", "team", "before", "approval", "sample",
    "automatic", "metadata", "extraction", "support", "purpose", "content", "revision",
}

RELATIONSHIP_RULES = {
    "explicit_reference": {
        "description": "Exact document number, filename, or title appears in another document.",
        "confidence": 0.98,
    },
    "rfi_linking": {
        "description": "RFIs are connected to referenced or closely matching drawings and specifications.",
        "target_types": ["Drawing", "Shop Drawing", "Specification"],
    },
    "meeting_minutes": {
        "description": "Meeting minutes are connected to referenced documents and extracted action items.",
    },
    "metadata_similarity": {
        "description": "When no exact reference exists, project, discipline, and topic similarity are used.",
        "maximum_confidence": 0.82,
    },
}


@dataclass(frozen=True)
class Match:
    value: str
    snippet: str


def normalize_identifier(value: str) -> str:
    """Normalize document identifiers to a stable uppercase hyphen format."""
    value = value.upper().strip()
    value = re.sub(r"[\s:_/]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value.strip("-.")


def extract_document_identifiers(document: dict[str, Any]) -> list[str]:
    """Extract the document's own number plus useful filename aliases.

    References found only in the body are intentionally excluded so a referenced
    drawing number is not incorrectly treated as the RFI's own identifier.
    """
    filename = str(document.get("filename") or "")
    title = str(document.get("document_title") or "")
    content = str(document.get("content_text") or document.get("text_preview") or "")

    identifiers = {
        normalize_identifier(match.group(1))
        for match in LABELED_IDENTIFIER_RE.finditer(content)
    }
    header_text = "\n".join((filename, title, content[:350]))
    header_matches = [normalize_identifier(match.group(0)) for match in DOCUMENT_IDENTIFIER_RE.finditer(header_text)]
    if header_matches:
        identifiers.add(header_matches[0])

    if filename:
        stem = Path(filename).stem
        if len(stem) >= 5:
            identifiers.add(stem.lower())
        identifiers.add(filename.lower())

    return sorted(item for item in identifiers if item)


def _find_reference(source_text: str, alias: str) -> Match | None:
    if not source_text or not alias:
        return None

    lowered = source_text.lower()
    candidates = {alias.lower(), alias.lower().replace("-", " "), alias.lower().replace("-", "_")}
    for candidate in sorted(candidates, key=len, reverse=True):
        if len(candidate) < 5:
            continue
        index = lowered.find(candidate)
        if index >= 0:
            start = max(0, index - 65)
            end = min(len(source_text), index + len(candidate) + 95)
            snippet = re.sub(r"\s+", " ", source_text[start:end]).strip()
            return Match(alias, snippet)
    return None


def _relationship_type(source_type: str, target_type: str, explicit: bool) -> str:
    source_lower = source_type.lower()
    target_lower = target_type.lower()

    if source_lower == "rfi":
        if "drawing" in target_lower:
            return "rfi_references_drawing" if explicit else "rfi_related_to_drawing"
        if target_lower == "specification":
            return "rfi_references_specification" if explicit else "rfi_related_to_specification"
    if source_lower == "meeting minutes":
        return "meeting_minutes_references_document" if explicit else "meeting_minutes_related_document"
    return "references_document" if explicit else "related_document"


def _tokens(value: str | None) -> set[str]:
    if not value:
        return set()
    return {token for token in TOKEN_RE.findall(value.lower()) if token not in STOP_WORDS}


def _similarity_score(source: dict[str, Any], target: dict[str, Any]) -> float:
    score = 0.0
    if source.get("project_name") and source.get("project_name") == target.get("project_name"):
        score += 0.48
    if source.get("discipline") and source.get("discipline") == target.get("discipline"):
        score += 0.18

    source_tokens = _tokens(
        " ".join(str(source.get(field) or "") for field in ("document_title", "content_text", "discipline"))
    )
    target_tokens = _tokens(
        " ".join(str(target.get(field) or "") for field in ("document_title", "content_text", "discipline"))
    )
    if source_tokens and target_tokens:
        overlap = len(source_tokens & target_tokens) / max(1, len(source_tokens | target_tokens))
        score += min(0.22, overlap * 0.8)

    return round(min(0.82, score), 3)


def _extract_action_items(text: str) -> list[dict[str, str | None]]:
    items: list[dict[str, str | None]] = []
    for match in ACTION_ITEM_RE.finditer(text or ""):
        raw = re.sub(r"\s+", " ", match.group(1)).strip(" .")
        if not raw:
            continue
        owner_match = OWNER_RE.search(raw)
        due_match = DUE_RE.search(raw)
        status_match = STATUS_RE.search(raw)

        owner = owner_match.group(1).strip() if owner_match else None
        due_date = None
        if due_match:
            date_match = DATE_RE.search(due_match.group(1))
            due_date = date_match.group(0) if date_match else due_match.group(1).strip()
        status = status_match.group(1).strip() if status_match else "Open"

        action_text = re.split(r"\b(?:Owner|Responsible|Assigned\s+To|Due\s*Date|Due|Status)\s*[:\-]", raw, maxsplit=1, flags=re.IGNORECASE)[0]
        action_text = action_text.strip(" .|-")
        if action_text:
            items.append(
                {
                    "action_text": action_text,
                    "owner": owner,
                    "due_date": due_date,
                    "status": status,
                    "reference_text": raw,
                }
            )
    return items


def _full_documents(db_path: str | Path, latest_only: bool) -> list[dict[str, Any]]:
    summaries = list_documents(limit=10000, latest_only=latest_only, db_path=db_path)
    return [document for item in summaries if (document := get_document(item["id"], db_path=db_path))]


def build_document_relationships(
    db_path: str | Path = DATABASE_PATH,
    reset: bool = True,
    latest_only: bool = True,
) -> dict[str, Any]:
    """Scan registered documents, create relationship edges, and extract meeting actions."""
    documents = _full_documents(db_path, latest_only=latest_only)
    if reset:
        clear_relationship_data(db_path)

    aliases_by_id = {doc["id"]: extract_document_identifiers(doc) for doc in documents}
    explicit_targets_by_source: dict[int, set[int]] = {doc["id"]: set() for doc in documents}
    relationship_ids: list[int] = []

    # Exact references based on document identifiers, filename aliases, and full titles.
    for source in documents:
        source_text = "\n".join(
            str(value or "")
            for value in (source.get("content_text"), source.get("text_preview"), source.get("document_title"))
        )
        for target in documents:
            if source["id"] == target["id"]:
                continue

            aliases = list(aliases_by_id[target["id"]])
            title = str(target.get("document_title") or "").strip()
            if len(title) >= 12:
                aliases.append(title)

            match = None
            for alias in aliases:
                match = _find_reference(source_text, alias)
                if match:
                    break
            if not match:
                continue

            relation = save_relationship(
                source_document_id=source["id"],
                target_document_id=target["id"],
                relationship_type=_relationship_type(source["document_type"], target["document_type"], True),
                reference_text=match.snippet,
                confidence_score=0.98,
                detected_by="explicit_reference",
                db_path=db_path,
            )
            explicit_targets_by_source[source["id"]].add(target["id"])
            relationship_ids.append(relation["id"])

    # Inferred links for RFIs and meeting minutes when explicit references are unavailable.
    for source in documents:
        source_type = str(source.get("document_type") or "")
        if source_type not in {"RFI", "Meeting Minutes"}:
            continue

        target_type_groups: list[set[str]]
        if source_type == "RFI":
            target_type_groups = [{"Drawing", "Shop Drawing"}, {"Specification"}]
        else:
            target_type_groups = [
                {"RFI", "Drawing", "Shop Drawing", "Specification", "Method Statement", "Material Submittal"}
            ]

        for type_group in target_type_groups:
            already_has_group = any(
                target["id"] in explicit_targets_by_source[source["id"]]
                and target.get("document_type") in type_group
                for target in documents
            )
            if already_has_group:
                continue

            candidates: list[tuple[float, dict[str, Any]]] = []
            for target in documents:
                if target["id"] == source["id"] or target.get("document_type") not in type_group:
                    continue
                score = _similarity_score(source, target)
                if score >= 0.45:
                    candidates.append((score, target))

            candidates.sort(key=lambda item: (-item[0], item[1]["id"]))
            maximum = 1 if source_type == "RFI" else 3
            for score, target in candidates[:maximum]:
                relation = save_relationship(
                    source_document_id=source["id"],
                    target_document_id=target["id"],
                    relationship_type=_relationship_type(source_type, target["document_type"], False),
                    reference_text=(
                        f"Inferred from project '{source.get('project_name')}' and discipline "
                        f"'{source.get('discipline')}'."
                    ),
                    confidence_score=score,
                    detected_by="metadata_similarity",
                    db_path=db_path,
                )
                relationship_ids.append(relation["id"])

    # Extract action items from meeting minutes and link each action to a referenced document when possible.
    action_item_ids: list[int] = []
    all_aliases: list[tuple[int, str]] = [
        (doc_id, alias)
        for doc_id, aliases in aliases_by_id.items()
        for alias in aliases
        if len(alias) >= 5
    ]
    for meeting in documents:
        if meeting.get("document_type") != "Meeting Minutes":
            continue
        text = str(meeting.get("content_text") or meeting.get("text_preview") or "")
        for item in _extract_action_items(text):
            related_id = None
            for target_id, alias in all_aliases:
                if target_id == meeting["id"]:
                    continue
                if _find_reference(str(item["reference_text"]), alias):
                    related_id = target_id
                    break
            saved = save_action_item(
                meeting_document_id=meeting["id"],
                action_text=str(item["action_text"]),
                owner=item.get("owner"),
                due_date=item.get("due_date"),
                status=str(item.get("status") or "Open"),
                related_document_id=related_id,
                reference_text=item.get("reference_text"),
                db_path=db_path,
            )
            action_item_ids.append(saved["id"])

    explicit_count = 0
    inferred_count = 0
    from app.relationship_repository import list_relationships

    for relationship in list_relationships(limit=10000, db_path=db_path):
        if relationship["detected_by"] == "explicit_reference":
            explicit_count += 1
        else:
            inferred_count += 1

    return {
        "message": "Document relationships built successfully.",
        "documents_scanned": len(documents),
        "relationships_created": len(set(relationship_ids)),
        "explicit_relationships": explicit_count,
        "inferred_relationships": inferred_count,
        "action_items_created": len(set(action_item_ids)),
        "latest_only": latest_only,
    }


def get_relationship_rules() -> dict[str, Any]:
    """Return the transparent rules used by the relationship engine."""
    return RELATIONSHIP_RULES
