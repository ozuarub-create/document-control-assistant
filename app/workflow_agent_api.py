"""FastAPI router for Week 24 Document Workflow Agent."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.workflow_agent import read_history, run_agent
from app.workflow_agent_tools import TOOLS

router = APIRouter(prefix="/workflow-agent", tags=["Week 24 Document Workflow Agent"])


@router.get("/capabilities")
def capabilities() -> dict[str, Any]:
    return {
        "service": "Week 24 Document Workflow Agent",
        "available_tools": list(TOOLS),
        "tool_count": len(TOOLS),
        "accepted_files": ["pdf", "txt", "md"],
        "planner_modes": ["fixture", "openai", "auto"],
        "audit_log": True,
    }


@router.post("/run")
async def run_workflow_agent(
    file: UploadFile = File(...),
    task: str = Form("Review this document and recommend the next workflow action."),
    provider: str = Query("fixture", pattern="^(fixture|openai|auto)$"),
) -> dict[str, Any]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and MD files are supported.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as handle:
            handle.write(content)
            temp_path = handle.name
        result = run_agent(temp_path, task=task, provider=provider)
        result["document"] = file.filename
        return result
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.get("/history")
def history(limit: int = Query(20, ge=1, le=200)) -> dict[str, Any]:
    rows = read_history(limit=limit)
    return {"count": len(rows), "runs": rows}
