"""Production-readiness diagnostics and final release manifest."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from app.auth_service import user_count
from app.config import get_settings
from app.database import DATABASE_PATH, get_connection, initialize_database

ROOT_DIR = Path(__file__).resolve().parent.parent


def production_readiness(db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    settings = get_settings()
    checks: list[dict[str, Any]] = []

    try:
        initialize_database(db_path)
        with get_connection(db_path) as connection:
            connection.execute("SELECT 1").fetchone()
        checks.append({"name": "database", "status": "pass", "detail": str(Path(db_path))})
    except Exception as exc:  # pragma: no cover - defensive diagnostic
        checks.append({"name": "database", "status": "fail", "detail": str(exc)})

    for folder_name in ("docs", "sample_documents", "compliance_reports"):
        folder = ROOT_DIR / folder_name
        try:
            folder.mkdir(parents=True, exist_ok=True)
            probe = folder / ".write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            checks.append({"name": f"directory_{folder_name}", "status": "pass", "detail": str(folder)})
        except OSError as exc:
            checks.append({"name": f"directory_{folder_name}", "status": "fail", "detail": str(exc)})

    docker_files = all((ROOT_DIR / name).exists() for name in ("Dockerfile", "docker-compose.yml", ".dockerignore"))
    checks.append({"name": "docker_files", "status": "pass" if docker_files else "warn", "detail": "Docker deployment files present" if docker_files else "Docker files not found"})

    docs_present = all(
        (ROOT_DIR / "docs" / name).exists()
        for name in ("USER_GUIDE_WEEK22.md", "ARCHITECTURE_WEEK22.md", "DOCKER_DEPLOYMENT_WEEK22.md")
    )
    checks.append({"name": "technical_documentation", "status": "pass" if docs_present else "warn", "detail": "Week 22 documentation set"})

    secret_status = "warn" if settings.using_default_secret else "pass"
    checks.append({"name": "secret_key", "status": secret_status, "detail": "Change APP_SECRET_KEY before public deployment" if secret_status == "warn" else "Custom secret configured"})

    admin_status = "warn" if settings.using_default_admin_password else "pass"
    checks.append({"name": "admin_password", "status": admin_status, "detail": "Change DEFAULT_ADMIN_PASSWORD before public deployment" if admin_status == "warn" else "Custom administrator password configured"})

    checks.append({"name": "authentication", "status": "pass" if settings.auth_required else "warn", "detail": f"AUTH_REQUIRED={settings.auth_required}"})
    checks.append({"name": "users", "status": "pass", "detail": f"{user_count(db_path=db_path)} user account(s)"})

    failures = [item for item in checks if item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] == "warn"]
    return {
        "status": "not_ready" if failures else ("ready_with_warnings" if warnings else "ready"),
        "environment": settings.environment,
        "version": settings.app_version,
        "authentication_required": settings.auth_required,
        "checks": checks,
        "summary": {"passed": sum(item["status"] == "pass" for item in checks), "warnings": len(warnings), "failed": len(failures)},
    }


def production_manifest() -> dict[str, Any]:
    settings = get_settings()
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "release": "Week 22 final standalone application",
        "modules": [
            "document ingestion and classification",
            "metadata extraction and register",
            "version control and workflow",
            "traditional and semantic search",
            "review, validation, and compliance",
            "document relationships and knowledge graph",
            "cited conversational assistant",
            "authentication and user management",
            "analytics dashboard",
        ],
        "deployment": {
            "local": "python -m uvicorn app.main:app --reload",
            "docker": "docker compose up --build",
            "port": int(os.getenv("PORT", "8000")),
        },
        "documentation": [
            "docs/USER_GUIDE_WEEK22.md",
            "docs/ARCHITECTURE_WEEK22.md",
            "docs/DOCKER_DEPLOYMENT_WEEK22.md",
            "docs/DEMO_RECORDING_GUIDE_WEEK22.md",
        ],
    }
