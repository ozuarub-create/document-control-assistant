from __future__ import annotations
import os

DEFAULT_KEY = os.getenv("MCP_API_KEY", "week27-demo-key")

class AccessDenied(Exception):
    pass

def validate_api_key(api_key: str | None) -> None:
    if not api_key or api_key != DEFAULT_KEY:
        raise AccessDenied("Invalid or missing MCP API key")
