from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ToolResult:
    ok: bool
    tool: str
    data: Any = None
    error: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)
