from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path("results/mcp_tool_calls.jsonl")

def log_tool_call(tool: str, args: dict, ok: bool, detail: str = "") -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool,
        "args": args,
        "ok": ok,
        "detail": detail,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
