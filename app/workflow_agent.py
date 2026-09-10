"""Week 24 standalone document workflow agent orchestration."""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.workflow_agent_tools import TOOLS, ToolContext, read_document_text


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_KB_PATH = ROOT_DIR / "workflow_test_documents" / "knowledge_base.json"
DEFAULT_HISTORY_PATH = ROOT_DIR / "workflow_agent_history.jsonl"


@dataclass
class Decision:
    step: int
    tool: str
    reason: str
    status: str = "planned"
    result: dict[str, Any] | None = None


class RuleBasedPlanner:
    """Deterministic planner used for offline operation and repeatable tests.

    It chooses a tool subset based on task intent and a lightweight preview.  It
    intentionally does not execute every tool for every document.
    """

    def plan(self, *, task: str, filename: str, text_preview: str) -> list[Decision]:
        q = task.lower()
        preview = f"{filename} {text_preview[:2000]}".lower()
        decisions: list[Decision] = []

        def add(tool: str, reason: str) -> None:
            if tool not in [d.tool for d in decisions]:
                decisions.append(Decision(len(decisions) + 1, tool, reason))

        add("classify_document", "Document type is needed to choose downstream validation and routing.")
        add("extract_metadata", "Core identifiers and revision metadata support document-control decisions.")

        if any(term in q for term in ["previous", "revision", "compare", "latest"]) or "rev" in preview:
            add("detect_previous_revisions", "Task or document indicates revision history may affect the next action.")
        if any(term in q for term in ["knowledge", "related", "search", "reference", "linked"]):
            add("search_knowledge_base", "Task asks for related project knowledge or references.")
        if any(term in q for term in ["complete", "validate", "approval", "review", "next action", "process", "workflow"]):
            add("check_completeness", "Workflow/review task requires a completeness gate.")
        if any(term in q for term in ["summary", "summarize", "overview", "brief"]):
            add("generate_summary", "Task explicitly requests a concise document summary.")
        if any(term in q for term in ["review", "comment", "finding", "issue", "approval"]):
            add("generate_review_comments", "Task requests review findings or approval support.")
        if any(term in q for term in ["next", "action", "route", "workflow", "process", "review", "approval"]):
            add("recommend_next_action", "Task requires a recommended workflow action.")

        if len(decisions) == 2:
            add("generate_summary", "No special intent detected; summary is the minimum useful document outcome.")
        return decisions


class OpenAIPlanner:
    """Optional model-backed planner. Falls back cleanly when no API key is set."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("WEEK24_AGENT_MODEL", "gpt-5-mini")

    def plan(self, *, task: str, filename: str, text_preview: str) -> list[Decision]:
        from openai import OpenAI

        client = OpenAI()
        tool_names = list(TOOLS)
        prompt = f"""You are a document-control workflow planner. Select only the tools necessary for the task.
Available tools: {tool_names}
Return JSON only: {{\"steps\":[{{\"tool\":\"...\",\"reason\":\"...\"}}]}}
Always include classify_document and extract_metadata. Include recommend_next_action when the user asks what should happen next.
Filename: {filename}
Task: {task}
Document preview:\n{text_preview[:4000]}"""
        response = client.responses.create(model=self.model, input=prompt)
        payload = json.loads(response.output_text)
        decisions: list[Decision] = []
        for item in payload.get("steps", []):
            tool = item.get("tool")
            if tool in TOOLS and tool not in [d.tool for d in decisions]:
                decisions.append(Decision(len(decisions) + 1, tool, str(item.get("reason") or "Model selected tool.")))
        if not decisions:
            return RuleBasedPlanner().plan(task=task, filename=filename, text_preview=text_preview)
        return decisions


def load_knowledge_base(path: str | Path | None = None) -> list[dict[str, Any]]:
    target = Path(path or DEFAULT_KB_PATH)
    if not target.exists():
        return []
    return json.loads(target.read_text(encoding="utf-8"))


def _choose_planner(provider: str):
    provider = provider.lower()
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required when provider=openai")
        return OpenAIPlanner()
    if provider == "auto" and os.getenv("OPENAI_API_KEY"):
        return OpenAIPlanner()
    return RuleBasedPlanner()


def run_agent(
    document_path: str | Path,
    *,
    task: str = "Review this document and recommend the next workflow action.",
    provider: str = "fixture",
    knowledge_base_path: str | Path | None = None,
    history_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(document_path)
    if not path.exists():
        raise FileNotFoundError(path)
    text = read_document_text(path)
    planner = _choose_planner(provider)
    plan = planner.plan(task=task, filename=path.name, text_preview=text)
    ctx = ToolContext(path=path, text=text, task=task, knowledge_base=load_knowledge_base(knowledge_base_path), memory={})

    execution_log: list[dict[str, Any]] = []
    for decision in plan:
        started = datetime.now(timezone.utc).isoformat()
        try:
            result = TOOLS[decision.tool](ctx)
            decision.status = "completed"
            decision.result = result
        except Exception as exc:  # fail one tool without hiding the audit trail
            decision.status = "failed"
            decision.result = {"error": str(exc)}
        execution_log.append({**asdict(decision), "timestamp": started})

    output = {
        "agent_run_id": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "document": path.name,
        "task": task,
        "planner": planner.__class__.__name__,
        "available_tools": list(TOOLS),
        "tools_selected": [d.tool for d in plan],
        "tool_count": len(plan),
        "execution_log": execution_log,
        "final": {
            "document_type": ctx.memory.get("document_type"),
            "metadata": ctx.memory.get("metadata"),
            "summary": ctx.memory.get("summary"),
            "review_comments": ctx.memory.get("review_comments"),
            "recommended_next_action": ctx.memory.get("next_action"),
        },
    }

    target = Path(history_path or DEFAULT_HISTORY_PATH)
    try:
        with target.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(output, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return output


def read_history(path: str | Path | None = None, limit: int = 50) -> list[dict[str, Any]]:
    target = Path(path or DEFAULT_HISTORY_PATH)
    if not target.exists():
        return []
    rows = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
    return rows[-limit:]
