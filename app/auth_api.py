"""FastAPI routes and dependencies for authentication and user management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth_repository import list_audit_events
from app.auth_service import (
    get_user_for_token,
    list_users,
    login_user,
    logout_user,
    register_user,
    set_user_active,
)
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
bearer_scheme = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=40, example="document.controller")
    password: str = Field(..., min_length=8, example="StrongPassword123!")
    full_name: str = Field(..., min_length=2, max_length=100, example="Document Controller")


class LoginRequest(BaseModel):
    username: str = Field(..., example="admin")
    password: str = Field(..., example="Admin123!")


class UserStatusRequest(BaseModel):
    is_active: bool


def _token(credentials: HTTPAuthorizationCredentials | None) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    token = _token(credentials)
    user = get_user_for_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def admin_user(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user


@router.get("/status")
def authentication_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "authentication_available": True,
        "authentication_required": settings.auth_required,
        "environment": settings.environment,
        "token_type": "Bearer",
        "login_endpoint": "/auth/login",
        "login_page": "/auth/login-page",
    }


@router.get("/login-page", response_class=HTMLResponse)
def login_page() -> str:
    return """
    <!doctype html><html><head><title>Document Control Login</title>
    <style>body{font-family:Arial;background:#eef2ff;margin:0;display:grid;place-items:center;height:100vh}.box{background:white;padding:30px;border-radius:12px;box-shadow:0 8px 30px #0002;width:340px}input,button{box-sizing:border-box;width:100%;padding:11px;margin:7px 0;border-radius:7px;border:1px solid #ccd}button{background:#2563eb;color:white;border:0;font-weight:bold}pre{white-space:pre-wrap;background:#111827;color:white;padding:12px;border-radius:7px}</style></head>
    <body><div class='box'><h2>AI Document Control Assistant</h2><p>Sign in to obtain an API token.</p>
    <input id='u' placeholder='Username' value='admin'><input id='p' type='password' placeholder='Password'><button onclick='login()'>Sign in</button><pre id='result'>Token will appear here.</pre>
    <script>async function login(){const r=await fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:u.value,password:p.value})});const d=await r.json();if(d.access_token){localStorage.setItem('document_control_token',d.access_token);result.textContent='Signed in as '+d.user.username+'\n\nBearer '+d.access_token;}else{result.textContent=JSON.stringify(d,null,2);}}</script></div></body></html>
    """


@router.post("/register", status_code=201)
def register(request: RegisterRequest) -> dict[str, Any]:
    try:
        user = register_user(request.username, request.password, request.full_name)
        return {"message": "User registered.", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login")
def login(request: LoginRequest) -> dict[str, Any]:
    try:
        return login_user(request.username, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me")
def me(user: dict[str, Any] = Depends(current_user)) -> dict[str, Any]:
    return {"user": user}


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user: dict[str, Any] = Depends(current_user),
) -> dict[str, Any]:
    token = _token(credentials)
    logout_user(token)
    return {"message": "Logged out.", "username": user["username"]}


@router.get("/users")
def users(
    limit: int = Query(100, ge=1, le=500),
    _: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    results = list_users(limit=limit)
    return {"count": len(results), "results": results}


@router.patch("/users/{user_id}/active")
def user_active_status(
    user_id: int,
    request: UserStatusRequest,
    admin: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    try:
        user = set_user_active(user_id, request.is_active, actor_id=int(admin["id"]))
        return {"message": "User status updated.", "user": user}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/audit")
def audit_log(
    limit: int = Query(100, ge=1, le=500),
    _: dict[str, Any] = Depends(admin_user),
) -> dict[str, Any]:
    results = list_audit_events(limit=limit)
    return {"count": len(results), "results": results}
