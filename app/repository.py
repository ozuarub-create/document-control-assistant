"""Metadata repository and version tracking for project documents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database, reset_database
from app.document_processor import process_file
from app.embeddings import create_embedding


def _clean_key_part(value: str | None) -> str:
    value = value or "unknown"
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "unknown"


def make_document_key(metadata: dict[str, Any], filename: str = "") -> str:
    """Create a stable key so revised uploads become new versions."""
    project = _clean_key_part(metadata.get("project_name"))
    title = _clean_key_part(metadata.get("document_title") or Path(filename).stem)
    return f"{project}::{title}"


def row_to_dict(row: Any, include_text: bool = False, include_embedding: bool = False) -> dict[str, Any]:
    item = dict(row)
    item["is_latest"] = bool(item.get("is_latest"))

    for json_field in ("matched_keywords_json", "scores_json", "embedding_json"):
        value = item.pop(json_field, None)
        target_name = json_field.replace("_json", "")
        if json_field == "embedding_json" and not include_embedding:
            continue
        try:
            item[target_name] = json.loads(value) if value else ([] if json_field == "matched_keywords_json" else {})
        except json.JSONDecodeError:
            item[target_name] = value

    if not include_text:
        item.pop("content_text", None)
    return item


def save_processed_document(
    processed: dict[str, Any],
    file_path: str | Path | None = None,
    db_path: str | Path = DATABASE_PATH,
    workflow_state: str = "registered",
) -> dict[str, Any]:
    """Save classification, metadata, text, embedding, version, and workflow data."""
    initialize_database(db_path)

    metadata = processed["metadata"]
    classification = processed["classification"]
    content_text = processed.get("content_text") or processed.get("text_preview") or ""
    filename = processed["filename"]
    document_key = make_document_key(metadata, filename)

    searchable_text = "\n".join(
        str(value)
        for value in [
            filename,
            classification.get("document_type"),
            metadata.get("document_title"),
            metadata.get("project_name"),
            metadata.get("contractor"),
            metadata.get("consultant"),
            metadata.get("discipline"),
            content_text,
        ]
        if value
    )
    embedding = create_embedding(searchable_text)

    with get_connection(db_path) as connection:
        latest_row = connection.execute(
            "SELECT COALESCE(MAX(version), 0) AS max_version FROM documents WHERE document_key = ?",
            (document_key,),
        ).fetchone()
        next_version = int(latest_row["max_version"] or 0) + 1

        connection.execute(
            "UPDATE documents SET is_latest = 0 WHERE document_key = ?",
            (document_key,),
        )

        cursor = connection.execute(
            """
            INSERT INTO documents (
                document_key, filename, file_type, file_path, document_type,
                confidence_score, matched_keywords_json, scores_json,
                document_title, revision_number, project_name, contractor,
                consultant, submission_date, discipline, version, is_latest,
                content_text, text_preview, embedding_json, workflow_state,
                last_workflow_action, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                document_key,
                filename,
                processed["file_type"],
                str(file_path) if file_path else None,
                classification.get("document_type", "Unknown"),
                float(classification.get("confidence_score", 0.0)),
                json.dumps(classification.get("matched_keywords", [])),
                json.dumps(classification.get("scores", {})),
                metadata.get("document_title"),
                metadata.get("revision_number"),
                metadata.get("project_name"),
                metadata.get("contractor"),
                metadata.get("consultant"),
                metadata.get("submission_date"),
                metadata.get("discipline"),
                next_version,
                content_text,
                processed.get("text_preview", ""),
                json.dumps(embedding),
                workflow_state,
                "document_registered",
            ),
        )
        connection.commit()
        document_id = cursor.lastrowid

        row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return row_to_dict(row)


def ingest_document(
    file_path: str | Path,
    filename: str | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    processed = process_file(file_path, filename, include_text=True)
    return save_processed_document(processed, file_path=file_path, db_path=db_path)


def ingest_folder(
    folder_path: str | Path,
    db_path: str | Path = DATABASE_PATH,
    reset: bool = False,
) -> list[dict[str, Any]]:
    if reset:
        reset_database(db_path)
    else:
        initialize_database(db_path)

    folder = Path(folder_path)
    files = sorted(folder.glob("*.pdf")) + sorted(folder.glob("*.docx"))
    return [ingest_document(path, db_path=db_path) for path in files]


def get_document(document_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return row_to_dict(row, include_text=True) if row else None


def list_documents(
    limit: int = 50,
    latest_only: bool = True,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    query = "SELECT * FROM documents"
    params: list[Any] = []
    if latest_only:
        query += " WHERE is_latest = 1"
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
        return [row_to_dict(row) for row in rows]


def search_documents(
    document_type: str | None = None,
    project_name: str | None = None,
    contractor: str | None = None,
    consultant: str | None = None,
    discipline: str | None = None,
    revision_number: str | None = None,
    workflow_state: str | None = None,
    q: str | None = None,
    latest_only: bool = True,
    limit: int = 20,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Traditional metadata search using SQL filters."""
    initialize_database(db_path)
    where: list[str] = []
    params: list[Any] = []

    def add_like(field: str, value: str | None) -> None:
        if value:
            where.append(f"LOWER({field}) LIKE ?")
            params.append(f"%{value.lower()}%")

    if latest_only:
        where.append("is_latest = 1")
    if document_type:
        where.append("LOWER(document_type) = ?")
        params.append(document_type.lower())
    if workflow_state:
        where.append("LOWER(workflow_state) = ?")
        params.append(workflow_state.lower())
    add_like("project_name", project_name)
    add_like("contractor", contractor)
    add_like("consultant", consultant)
    add_like("discipline", discipline)
    if revision_number:
        where.append("LOWER(revision_number) = ?")
        params.append(revision_number.lower())

    if q:
        where.append(
            "("
            "LOWER(filename) LIKE ? OR LOWER(document_title) LIKE ? OR "
            "LOWER(project_name) LIKE ? OR LOWER(contractor) LIKE ? OR "
            "LOWER(consultant) LIKE ? OR LOWER(discipline) LIKE ? OR "
            "LOWER(content_text) LIKE ? OR LOWER(workflow_state) LIKE ?"
            ")"
        )
        like_value = f"%{q.lower()}%"
        params.extend([like_value] * 8)

    query = "SELECT * FROM documents"
    if where:
        query += " WHERE " + " AND ".join(where)
    query += " ORDER BY created_at DESC, id DESC LIMIT ?"
    params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(query, params).fetchall()
        return [row_to_dict(row) for row in rows]


def get_version_history(document_id: int, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        current = connection.execute("SELECT document_key FROM documents WHERE id = ?", (document_id,)).fetchone()
        if not current:
            return []
        rows = connection.execute(
            "SELECT * FROM documents WHERE document_key = ? ORDER BY version DESC",
            (current["document_key"],),
        ).fetchall()
        return [row_to_dict(row) for row in rows]
