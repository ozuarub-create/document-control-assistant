from __future__ import annotations

from pathlib import Path

import pytest

from app.auth_service import (
    ensure_default_admin,
    get_user_for_token,
    hash_password,
    login_user,
    logout_user,
    register_user,
    set_user_active,
    verify_password,
)
from app.database import reset_database
from app.production import production_manifest, production_readiness


def test_password_hash_round_trip() -> None:
    stored = hash_password("StrongPassword123!")
    assert stored.startswith("pbkdf2_sha256$")
    assert verify_password("StrongPassword123!", stored) is True
    assert verify_password("WrongPassword", stored) is False


def test_register_login_and_token_validation(tmp_path: Path) -> None:
    db_path = tmp_path / "auth.db"
    reset_database(db_path)
    user = register_user("controller", "Controller123!", "Document Controller", db_path=db_path)
    login = login_user("controller", "Controller123!", db_path=db_path)
    current = get_user_for_token(login["access_token"], db_path=db_path)

    assert user["role"] == "user"
    assert login["token_type"] == "bearer"
    assert current is not None
    assert current["username"] == "controller"


def test_duplicate_user_and_invalid_login_are_rejected(tmp_path: Path) -> None:
    db_path = tmp_path / "invalid_auth.db"
    reset_database(db_path)
    register_user("reviewer", "Reviewer123!", "Project Reviewer", db_path=db_path)

    with pytest.raises(ValueError, match="already exists"):
        register_user("reviewer", "Another123!", "Other Reviewer", db_path=db_path)
    with pytest.raises(ValueError, match="Invalid username or password"):
        login_user("reviewer", "wrong-password", db_path=db_path)


def test_admin_can_deactivate_user_and_logout_revokes_token(tmp_path: Path) -> None:
    db_path = tmp_path / "management.db"
    reset_database(db_path)
    admin = ensure_default_admin(db_path=db_path, username="admin", password="Admin123!")
    user = register_user("engineer", "Engineer123!", "Project Engineer", db_path=db_path)
    login = login_user("engineer", "Engineer123!", db_path=db_path)

    assert logout_user(login["access_token"], db_path=db_path) is True
    assert get_user_for_token(login["access_token"], db_path=db_path) is None

    updated = set_user_active(user["id"], False, actor_id=admin["id"], db_path=db_path)
    assert updated["is_active"] is False


def test_production_readiness_and_manifest(tmp_path: Path) -> None:
    db_path = tmp_path / "readiness.db"
    reset_database(db_path)
    ensure_default_admin(db_path=db_path, username="admin", password="Admin123!")

    readiness = production_readiness(db_path=db_path)
    manifest = production_manifest()

    assert readiness["status"] in {"ready", "ready_with_warnings"}
    assert readiness["summary"]["failed"] == 0
    assert manifest["version"] == "8.0.0"
    assert "authentication and user management" in manifest["modules"]
