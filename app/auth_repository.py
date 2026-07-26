"""SQLite persistence for users, authentication sessions, and audit events."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database


def _row(row: Any) -> dict[str, Any] | None:
    return dict(row) if row else None


def create_user_record(
    username: str,
    full_name: str,
    password_hash: str,
    role: str = "user",
    is_active: bool = True,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, full_name, password_hash, role, is_active, updated_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (username, full_name, password_hash, role, int(is_active)),
        )
        connection.commit()
        return dict(connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone())


def get_user_by_username(username: str, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        return _row(connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone())


def get_user_by_id(user_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        return _row(connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def count_users(db_path: str | Path = DATABASE_PATH) -> int:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM users").fetchone()
        return int(row["total"])


def list_user_records(limit: int = 100, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM users ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def update_user_active(user_id: int, is_active: bool, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE users SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (int(is_active), user_id),
        )
        if not is_active:
            connection.execute(
                "UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE user_id = ? AND revoked_at IS NULL",
                (user_id,),
            )
        connection.commit()
        return _row(connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())


def create_auth_session(
    user_id: int,
    token_hash: str,
    expires_at: str,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO auth_sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user_id, token_hash, expires_at),
        )
        connection.commit()
        return dict(connection.execute("SELECT * FROM auth_sessions WHERE id = ?", (cursor.lastrowid,)).fetchone())


def get_auth_session(token_hash: str, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT s.*, u.username, u.full_name, u.role, u.is_active
            FROM auth_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
    return _row(row)


def revoke_auth_session(token_hash: str, db_path: str | Path = DATABASE_PATH) -> bool:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            "UPDATE auth_sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ? AND revoked_at IS NULL",
            (token_hash,),
        )
        connection.commit()
        return cursor.rowcount > 0


def record_audit_event(
    action: str,
    user_id: int | None = None,
    details: dict[str, Any] | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO audit_events (user_id, action, details_json) VALUES (?, ?, ?)",
            (user_id, action, json.dumps(details or {}, sort_keys=True)),
        )
        connection.commit()


def list_audit_events(limit: int = 100, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT a.*, u.username
            FROM audit_events a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.created_at DESC, a.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["details"] = json.loads(item.pop("details_json") or "{}")
        except json.JSONDecodeError:
            item["details"] = {}
        results.append(item)
    return results
