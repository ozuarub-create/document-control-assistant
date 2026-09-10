from __future__ import annotations

import json
from pathlib import Path

from app.workflow_agent import run_agent

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "workflow_test_documents"
SCENARIOS = [
    ("scenario_01_drawing_r2.txt", "Review this drawing, check previous revisions, and recommend the next action"),
    ("scenario_02_open_rfi.txt", "Review this RFI and recommend the next workflow action"),
    ("scenario_03_incomplete_submittal.txt", "Check completeness and recommend next action"),
    ("scenario_04_specification.txt", "Search related knowledge and summarize this specification"),
    ("scenario_05_meeting_minutes.txt", "Summarize this document"),
    ("scenario_06_inspection.txt", "Generate review comments and recommend next action"),
    ("scenario_07_method_statement.txt", "Review for approval and recommend next action"),
    ("scenario_08_material_submittal.txt", "Find previous revision and recommend next action"),
    ("scenario_09_drawing_r0.txt", "Classify and extract metadata"),
    ("scenario_10_rfi_closed.txt", "Summarize this RFI"),
]

results = []
print("Week 24 - Document Workflow Agent Demo")
print("=" * 72)
print("Available agent tools: 8")
print("Test scenarios: 10")
for index, (filename, task) in enumerate(SCENARIOS, 1):
    result = run_agent(DOCS / filename, task=task, provider="fixture", history_path=ROOT / "workflow_agent_history_demo.jsonl")
    results.append(result)
    print(f"\n[{index:02d}] {filename}")
    print(f"Task: {task}")
    print("Selected tools:", " -> ".join(result["tools_selected"]))
    action = result["final"].get("recommended_next_action")
    print("Next action:", action["recommended_action"] if action else "not requested")
    print("Execution log steps:", len(result["execution_log"]))

selective = sum(1 for row in results if row["tool_count"] < len(row["available_tools"]))
with (ROOT / "demo_week24_results.json").open("w", encoding="utf-8") as handle:
    json.dump(results, handle, indent=2)

summary = {
    "scenarios": len(results),
    "available_tools": 8,
    "selective_runs": selective,
    "all_runs_logged": all(bool(r["execution_log"]) for r in results),
    "result_file": "demo_week24_results.json",
}
(ROOT / "agent_evaluation_week24.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print("\n" + "=" * 72)
print("Week 24 Demo Complete")
print("- Standalone agent orchestration: working")
print("- Available tools/functions: 8")
print(f"- Realistic test scenarios: {len(results)}")
print(f"- Selective tool-use runs: {selective}/{len(results)}")
print("- Execution history and decision logging: working")
print("- Structured results saved to: demo_week24_results.json")
