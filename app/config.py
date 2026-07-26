"""Environment-based configuration for the production-ready application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    auth_required: bool
    secret_key: str
    token_ttl_minutes: int
    default_admin_username: str
    default_admin_password: str
    default_admin_full_name: str
    database_path: Path

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def using_default_secret(self) -> bool:
        return self.secret_key == "change-this-secret-before-production"

    @property
    def using_default_admin_password(self) -> bool:
        return self.default_admin_password == "Admin123!"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    root_dir = Path(__file__).resolve().parent.parent
    return Settings(
        app_name=os.getenv("APP_NAME", "AI Document Control Assistant"),
        app_version=os.getenv("APP_VERSION", "8.0.0"),
        environment=os.getenv("APP_ENV", "development"),
        auth_required=_as_bool(os.getenv("AUTH_REQUIRED"), default=False),
        secret_key=os.getenv("APP_SECRET_KEY", "change-this-secret-before-production"),
        token_ttl_minutes=max(5, int(os.getenv("TOKEN_TTL_MINUTES", "480"))),
        default_admin_username=os.getenv("DEFAULT_ADMIN_USERNAME", "admin"),
        default_admin_password=os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123!"),
        default_admin_full_name=os.getenv("DEFAULT_ADMIN_FULL_NAME", "System Administrator"),
        database_path=Path(os.getenv("DOCUMENT_DB_PATH", str(root_dir / "document_register.db"))),
    )
