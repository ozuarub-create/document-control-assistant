"""Repository helpers for saving and retrieving document review reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database
from app.repository import make_document_key


def _review_row_to_dict(row: Any) -> dict[str, Any]:
    item = dict(row)
    try:
        item["report"] = json.loads(item.pop("report_json"))
    except (json.JSONDecodeError, TypeError):
        item["report"] = item.pop("report_json", None)
    return item


def save_review_report(
    report: dict[str, Any],
    document_id: int | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)
    metadata = report.get("metadata", {})
    filename = report.get("filename") or "unknown"
    document_key = report.get("duplicate_check", {}).get("document_key") or make_document_key(metadata, filename)

    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO document_reviews (
                document_id, filename, document_key, review_status,
                quality_score, duplicate_status, summary, report_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                filename,
                document_key,
                report.get("validation_status", "Needs Review"),
                int(report.get("quality_score", 0)),
                report.get("duplicate_check", {}).get("status", "No Duplicate Found"),
                report.get("summary", {}).get("summary_text", ""),
                json.dumps(report, ensure_ascii=False),
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM document_reviews WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _review_row_to_dict(row)


def get_latest_review_for_document(
    document_id: int,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM document_reviews
            WHERE document_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()
        return _review_row_to_dict(row) if row else None


def list_review_reports(
    limit: int = 50,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM document_reviews
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [_review_row_to_dict(row) for row in rows]
