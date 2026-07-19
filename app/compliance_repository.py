"""Repository functions for Week 19 compliance reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database

COMPLIANCE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS document_compliance_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER,
    filename TEXT NOT NULL,
    document_key TEXT,
    document_type TEXT NOT NULL,
    compliance_status TEXT NOT NULL,
    compliance_score INTEGER NOT NULL,
    report_json TEXT NOT NULL,
    json_report_path TEXT,
    pdf_report_path TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);
CREATE INDEX IF NOT EXISTS idx_compliance_document_id ON document_compliance_reports(document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_status ON document_compliance_reports(compliance_status);
CREATE INDEX IF NOT EXISTS idx_compliance_type ON document_compliance_reports(document_type);
"""


def initialize_compliance_repository(db_path: str | Path = DATABASE_PATH) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.executescript(COMPLIANCE_TABLE_SQL)
        connection.commit()


def _row_to_report(row: Any) -> dict[str, Any]:
    item = dict(row)
    try:
        item["report"] = json.loads(item.pop("report_json") or "{}")
    except json.JSONDecodeError:
        item["report"] = {}
    return item


def save_compliance_report(
    report: dict[str, Any],
    document_id: int | None = None,
    document_key: str | None = None,
    json_report_path: str | Path | None = None,
    pdf_report_path: str | Path | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    initialize_compliance_repository(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO document_compliance_reports (
                document_id, filename, document_key, document_type, compliance_status,
                compliance_score, report_json, json_report_path, pdf_report_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                report.get("filename", "unknown"),
                document_key,
                report.get("document_type", "Unknown"),
                report.get("compliance_status", "Unknown"),
                int(report.get("compliance_score", 0)),
                json.dumps(report, ensure_ascii=False),
                str(json_report_path) if json_report_path else None,
                str(pdf_report_path) if pdf_report_path else None,
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM document_compliance_reports WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return _row_to_report(row)


def list_compliance_reports(limit: int = 50, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    initialize_compliance_repository(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM document_compliance_reports ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_report(row) for row in rows]


def get_latest_compliance_report_for_document(document_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_compliance_repository(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM document_compliance_reports
            WHERE document_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()
        return _row_to_report(row) if row else None
