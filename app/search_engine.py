"""Traditional, semantic, and natural-language document search helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.classifier import DOCUMENT_CATEGORIES
from app.database import DATABASE_PATH, get_connection, initialize_database
from app.embeddings import cosine_similarity, create_embedding
from app.repository import row_to_dict, search_documents

DISCIPLINES = [
    "Architectural", "Structural", "Civil", "Mechanical", "Electrical", "QA/QC", "Contracts"
]

CATEGORY_ALIASES = {
    "drawings": "Drawing",
    "drawing": "Drawing",
    "plans": "Drawing",
    "specs": "Specification",
    "specifications": "Specification",
    "method statements": "Method Statement",
    "method statement": "Method Statement",
    "material submittals": "Material Submittal",
    "material submittal": "Material Submittal",
    "shop drawings": "Shop Drawing",
    "shop drawing": "Shop Drawing",
    "inspection reports": "Inspection Report",
    "inspection report": "Inspection Report",
    "contracts": "Contract",
    "contract": "Contract",
    "meeting minutes": "Meeting Minutes",
    "minutes": "Meeting Minutes",
    "rfi": "RFI",
    "rfis": "RFI",
    "request for information": "RFI",
}


def semantic_search(
    query: str,
    limit: int = 10,
    latest_only: bool = True,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """AI-powered semantic search using local embeddings and cosine similarity."""
    initialize_database(db_path)
    query_embedding = create_embedding(query)

    sql = "SELECT * FROM documents"
    params: list[Any] = []
    if latest_only:
        sql += " WHERE is_latest = 1"
    sql += " ORDER BY id DESC"

    results: list[dict[str, Any]] = []
    with get_connection(db_path) as connection:
        rows = connection.execute(sql, params).fetchall()
        for row in rows:
            try:
                document_embedding = json.loads(row["embedding_json"] or "{}")
            except json.JSONDecodeError:
                document_embedding = {}
            score = cosine_similarity(query_embedding, document_embedding)
            item = row_to_dict(row)
            item["semantic_score"] = score
            results.append(item)

    results.sort(key=lambda item: item["semantic_score"], reverse=True)
    return [item for item in results if item["semantic_score"] > 0][:limit]


def parse_natural_language_query(question: str) -> dict[str, Any]:
    """Extract simple metadata filters from a natural-language request."""
    lowered = question.lower()
    filters: dict[str, Any] = {
        "document_type": None,
        "discipline": None,
        "project_name": None,
        "contractor": None,
        "consultant": None,
        "latest_only": "latest" in lowered or "current" in lowered or "newest" in lowered,
    }

    for category in DOCUMENT_CATEGORIES:
        if category.lower() in lowered:
            filters["document_type"] = category
            break

    if filters["document_type"] is None:
        for alias, category in CATEGORY_ALIASES.items():
            if alias in lowered:
                filters["document_type"] = category
                break

    for discipline in DISCIPLINES:
        if discipline.lower().replace("/", "") in lowered.replace("/", ""):
            filters["discipline"] = discipline
            break

    # The sample dataset uses these project names. This keeps natural language
    # matching easy and transparent for the assignment demonstration.
    known_projects = [
        "Campus Innovation Building",
        "Al Ain Mixed Use Development",
        "Sustainable Site Infrastructure Project",
        "UAEU Smart Construction Training Project",
    ]
    for project in known_projects:
        words = project.lower().split()
        if project.lower() in lowered or all(word in lowered for word in words[:2]):
            filters["project_name"] = project
            break

    return filters


def natural_language_search(
    question: str,
    limit: int = 10,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Support natural-language document queries.

    It first extracts obvious metadata filters, then ranks the matching set using
    semantic embeddings.
    """
    filters = parse_natural_language_query(question)

    metadata_matches = search_documents(
        document_type=filters.get("document_type"),
        project_name=filters.get("project_name"),
        discipline=filters.get("discipline"),
        latest_only=filters.get("latest_only", False),
        limit=100,
        db_path=db_path,
    )

    semantic_matches = semantic_search(
        question,
        limit=100,
        latest_only=filters.get("latest_only", False),
        db_path=db_path,
    )

    metadata_ids = {item["id"] for item in metadata_matches}
    combined: list[dict[str, Any]] = []
    for item in semantic_matches:
        if metadata_ids and item["id"] not in metadata_ids:
            continue
        combined.append(item)

    if not combined:
        combined = metadata_matches[:limit]
    else:
        combined = combined[:limit]

    return {
        "question": question,
        "interpreted_filters": filters,
        "answer": f"Found {len(combined)} matching document(s).",
        "results": combined,
    }
