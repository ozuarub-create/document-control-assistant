from pathlib import Path

from app.workflow_agent import RuleBasedPlanner, run_agent
from app.workflow_agent_tools import TOOLS

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "workflow_test_documents"


def test_minimum_five_tools_available():
    assert len(TOOLS) >= 5
    assert len(TOOLS) == 8


def test_planner_is_selective_for_summary_task():
    plan = RuleBasedPlanner().plan(task="Summarize this document", filename="x.txt", text_preview="drawing")
    names = [step.tool for step in plan]
    assert "generate_summary" in names
    assert "recommend_next_action" not in names
    assert len(names) < len(TOOLS)


def test_review_task_selects_workflow_tools():
    plan = RuleBasedPlanner().plan(task="Review and recommend next action", filename="x.txt", text_preview="Drawing Rev R2")
    names = [step.tool for step in plan]
    assert "check_completeness" in names
    assert "generate_review_comments" in names
    assert "recommend_next_action" in names


def test_agent_execution_log_and_action(tmp_path):
    result = run_agent(
        DOCS / "scenario_01_drawing_r2.txt",
        task="Review this drawing and recommend the next action",
        provider="fixture",
        history_path=tmp_path / "history.jsonl",
    )
    assert result["execution_log"]
    assert all(row["status"] == "completed" for row in result["execution_log"])
    assert result["final"]["recommended_next_action"]
    assert (tmp_path / "history.jsonl").exists()


def test_revision_detection(tmp_path):
    result = run_agent(
        DOCS / "scenario_01_drawing_r2.txt",
        task="Find previous revision and recommend next action",
        provider="fixture",
        history_path=tmp_path / "h.jsonl",
    )
    row = next(x for x in result["execution_log"] if x["tool"] == "detect_previous_revisions")
    assert row["result"]["count"] >= 1


def test_incomplete_document_returns_for_completion(tmp_path):
    result = run_agent(
        DOCS / "scenario_03_incomplete_submittal.txt",
        task="Check completeness and recommend next action",
        provider="fixture",
        history_path=tmp_path / "h.jsonl",
    )
    assert result["final"]["recommended_next_action"]["recommended_action"] == "return_for_information_completion"


def test_open_rfi_routes_for_response(tmp_path):
    result = run_agent(
        DOCS / "scenario_02_open_rfi.txt",
        task="Review and recommend next action",
        provider="fixture",
        history_path=tmp_path / "h.jsonl",
    )
    assert result["final"]["recommended_next_action"]["recommended_action"] == "route_to_responsible_engineer_for_response"


def test_knowledge_search_selected_only_when_requested(tmp_path):
    result = run_agent(
        DOCS / "scenario_04_specification.txt",
        task="Search related knowledge and summarize references",
        provider="fixture",
        history_path=tmp_path / "h.jsonl",
    )
    assert "search_knowledge_base" in result["tools_selected"]
    assert "recommend_next_action" not in result["tools_selected"]


def test_ten_realistic_scenarios_present():
    files = sorted(DOCS.glob("scenario_*.txt"))
    assert len(files) >= 10
