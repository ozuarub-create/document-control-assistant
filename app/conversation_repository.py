"""SQLite repository for conversational sessions and message history."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database


def _loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def create_conversation_session(
    session_id: str | None = None,
    title: str | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Create a conversation session or return the existing session."""
    initialize_database(db_path)
    session_id = session_id or str(uuid.uuid4())
    title = (title or "Document conversation").strip()[:120]

    with get_connection(db_path) as connection:
        existing = connection.execute(
            "SELECT * FROM conversation_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if existing:
            return dict(existing)

        connection.execute(
            """
            INSERT INTO conversation_sessions (id, title, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (session_id, title),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM conversation_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        return dict(row)


def save_conversation_message(
    session_id: str,
    role: str,
    content: str,
    citations: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Store one user or assistant message."""
    initialize_database(db_path)
    if role not in {"user", "assistant"}:
        raise ValueError("role must be 'user' or 'assistant'")

    create_conversation_session(session_id=session_id, db_path=db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO conversation_messages (
                session_id, role, content, citations_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                role,
                content,
                json.dumps(citations or []),
                json.dumps(metadata or {}),
            ),
        )
        connection.execute(
            "UPDATE conversation_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (session_id,),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM conversation_messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()

    item = dict(row)
    item["citations"] = _loads(item.pop("citations_json", None), [])
    item["metadata"] = _loads(item.pop("metadata_json", None), {})
    return item


def get_conversation_history(
    session_id: str,
    limit: int = 50,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Return messages in chronological order."""
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM (
                SELECT * FROM conversation_messages
                WHERE session_id = ?
                ORDER BY id DESC
                LIMIT ?
            ) ORDER BY id ASC
            """,
            (session_id, limit),
        ).fetchall()

    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["citations"] = _loads(item.pop("citations_json", None), [])
        item["metadata"] = _loads(item.pop("metadata_json", None), {})
        results.append(item)
    return results


def get_conversation_session(
    session_id: str,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM conversation_sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
    if not row:
        return None
    session = dict(row)
    session["messages"] = get_conversation_history(session_id, db_path=db_path)
    session["message_count"] = len(session["messages"])
    return session


def list_conversation_sessions(
    limit: int = 50,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT s.*, COUNT(m.id) AS message_count
            FROM conversation_sessions s
            LEFT JOIN conversation_messages m ON m.session_id = s.id
            GROUP BY s.id
            ORDER BY s.updated_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_conversation_session(
    session_id: str,
    db_path: str | Path = DATABASE_PATH,
) -> bool:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM conversation_messages WHERE session_id = ?", (session_id,))
        cursor = connection.execute("DELETE FROM conversation_sessions WHERE id = ?", (session_id,))
        connection.commit()
        return cursor.rowcount > 0
