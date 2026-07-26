"""Optional production middleware that protects the application with Bearer tokens."""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.auth_service import get_user_for_token
from app.config import get_settings

PUBLIC_PATHS = {
    "/",
    "/health",
    "/production/readiness",
    "/production/manifest",
    "/auth/status",
    "/auth/login",
    "/auth/register",
    "/auth/login-page",
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        path = request.url.path.rstrip("/") or "/"
        if (
            not settings.auth_required
            or request.method == "OPTIONS"
            or path in PUBLIC_PATHS
            or path.startswith("/docs/")
        ):
            return await call_next(request)

        header = request.headers.get("Authorization", "")
        if not header.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required. Use Authorization: Bearer <token>."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = header.split(" ", 1)[1].strip()
        user = get_user_for_token(token)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired access token."},
                headers={"WWW-Authenticate": "Bearer"},
            )
        request.state.user = user
        return await call_next(request)
