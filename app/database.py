"""SQLite database setup for the intelligent document register."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = ROOT_DIR / "document_register.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_key TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_path TEXT,
    document_type TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    matched_keywords_json TEXT,
    scores_json TEXT,
    document_title TEXT,
    revision_number TEXT,
    project_name TEXT,
    contractor TEXT,
    consultant TEXT,
    submission_date TEXT,
    discipline TEXT,
    version INTEGER NOT NULL,
    is_latest INTEGER NOT NULL DEFAULT 1,
    content_text TEXT NOT NULL,
    text_preview TEXT,
    embedding_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_project ON documents(project_name);
CREATE INDEX IF NOT EXISTS idx_documents_contractor ON documents(contractor);
CREATE INDEX IF NOT EXISTS idx_documents_consultant ON documents(consultant);
CREATE INDEX IF NOT EXISTS idx_documents_discipline ON documents(discipline);
CREATE INDEX IF NOT EXISTS idx_documents_key ON documents(document_key);
CREATE INDEX IF NOT EXISTS idx_documents_latest ON documents(is_latest);
"""


def get_connection(db_path: str | Path = DATABASE_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: str | Path = DATABASE_PATH) -> None:
    with get_connection(db_path) as connection:
        connection.executescript(SCHEMA_SQL)
        connection.commit()


def reset_database(db_path: str | Path = DATABASE_PATH) -> None:
    with get_connection(db_path) as connection:
        connection.execute("DROP TABLE IF EXISTS documents")
        connection.commit()
    initialize_database(db_path)
