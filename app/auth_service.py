"""Password hashing, login sessions, and basic user-management services."""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.auth_repository import (
    count_users,
    create_auth_session,
    create_user_record,
    get_auth_session,
    get_user_by_id,
    get_user_by_username,
    list_user_records,
    record_audit_event,
    revoke_auth_session,
    update_user_active,
)
from app.config import get_settings
from app.database import DATABASE_PATH

PASSWORD_ITERATIONS = 150_000
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,40}$")
VALID_ROLES = {"admin", "user"}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _public_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(user["id"]),
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "is_active": bool(user["is_active"]),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }


def hash_password(password: str, salt: bytes | None = None) -> str:
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt_value, digest_value = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_value.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    secret = get_settings().secret_key.encode("utf-8")
    return hmac.new(secret, token.encode("utf-8"), hashlib.sha256).hexdigest()


def register_user(
    username: str,
    password: str,
    full_name: str,
    role: str = "user",
    allow_admin: bool = False,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    username = username.strip().lower()
    full_name = full_name.strip()
    role = role.strip().lower()
    if not USERNAME_RE.fullmatch(username):
        raise ValueError("Username must be 3-40 characters using letters, numbers, dot, dash, or underscore.")
    if not full_name:
        raise ValueError("Full name is required.")
    if role not in VALID_ROLES:
        raise ValueError("Role must be admin or user.")
    if role == "admin" and not allow_admin:
        raise ValueError("Only an administrator can create another administrator.")
    if get_user_by_username(username, db_path=db_path):
        raise ValueError("Username already exists.")

    user = create_user_record(
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        db_path=db_path,
    )
    record_audit_event("user_registered", user_id=int(user["id"]), details={"role": role}, db_path=db_path)
    return _public_user(user)


def login_user(username: str, password: str, db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    username = username.strip().lower()
    user = get_user_by_username(username, db_path=db_path)
    if not user or not bool(user["is_active"]) or not verify_password(password, user["password_hash"]):
        record_audit_event("login_failed", details={"username": username}, db_path=db_path)
        raise ValueError("Invalid username or password.")

    settings = get_settings()
    token = secrets.token_urlsafe(36)
    expires_at = _utc_now() + timedelta(minutes=settings.token_ttl_minutes)
    create_auth_session(
        int(user["id"]),
        _token_hash(token),
        expires_at.isoformat(),
        db_path=db_path,
    )
    record_audit_event("login_success", user_id=int(user["id"]), db_path=db_path)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_seconds": settings.token_ttl_minutes * 60,
        "expires_at": expires_at.isoformat(),
        "user": _public_user(user),
    }


def get_user_for_token(token: str, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    if not token:
        return None
    session = get_auth_session(_token_hash(token), db_path=db_path)
    if not session or session.get("revoked_at") or not bool(session.get("is_active")):
        return None
    try:
        expires_at = datetime.fromisoformat(str(session["expires_at"]))
    except ValueError:
        return None
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= _utc_now():
        return None
    return {
        "id": int(session["user_id"]),
        "username": session["username"],
        "full_name": session["full_name"],
        "role": session["role"],
        "is_active": bool(session["is_active"]),
        "session_id": int(session["id"]),
        "expires_at": session["expires_at"],
    }


def logout_user(token: str, db_path: str | Path = DATABASE_PATH) -> bool:
    user = get_user_for_token(token, db_path=db_path)
    revoked = revoke_auth_session(_token_hash(token), db_path=db_path)
    if revoked:
        record_audit_event("logout", user_id=int(user["id"]) if user else None, db_path=db_path)
    return revoked


def list_users(limit: int = 100, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    return [_public_user(user) for user in list_user_records(limit=limit, db_path=db_path)]


def set_user_active(user_id: int, is_active: bool, actor_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    if user_id == actor_id and not is_active:
        raise ValueError("You cannot deactivate your own account.")
    user = update_user_active(user_id, is_active, db_path=db_path)
    if not user:
        raise ValueError("User not found.")
    record_audit_event(
        "user_status_updated",
        user_id=actor_id,
        details={"target_user_id": user_id, "is_active": is_active},
        db_path=db_path,
    )
    return _public_user(user)


def get_public_user(user_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any] | None:
    user = get_user_by_id(user_id, db_path=db_path)
    return _public_user(user) if user else None


def ensure_default_admin(
    db_path: str | Path = DATABASE_PATH,
    username: str | None = None,
    password: str | None = None,
    full_name: str | None = None,
) -> dict[str, Any]:
    settings = get_settings()
    username = (username or settings.default_admin_username).strip().lower()
    existing = get_user_by_username(username, db_path=db_path)
    if existing:
        return _public_user(existing)
    return register_user(
        username=username,
        password=password or settings.default_admin_password,
        full_name=full_name or settings.default_admin_full_name,
        role="admin",
        allow_admin=True,
        db_path=db_path,
    )


def user_count(db_path: str | Path = DATABASE_PATH) -> int:
    return count_users(db_path=db_path)
