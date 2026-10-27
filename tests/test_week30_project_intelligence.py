import json
from pathlib import Path
from app.project_intelligence_agent import ProjectIntelligenceAgent
from app.project_tools import related_documents
from app.conflict_detector import detect_conflicts

ROOT = Path(__file__).resolve().parents[1]
DOCS = json.loads((ROOT/'project_dataset'/'simulated_project.json').read_text())

def test_agent_generates_report():
    report = ProjectIntelligenceAgent(DOCS).investigate("Analyze project risks")
    assert report["executive_summary"]
    assert report["execution_trace"]

def test_unresolved_rfi_identified():
    report = ProjectIntelligenceAgent(DOCS).investigate("Analyze project risks")
    assert any("RFI-015" in x["statement"] for x in report["unresolved_items"])

def test_overdue_action_identified():
    report = ProjectIntelligenceAgent(DOCS).investigate("Analyze project risks")
    assert any("Close RFI-015" in x["statement"] for x in report["outstanding_actions"])

def test_conflict_detected():
    conflicts = detect_conflicts(DOCS)
    assert any(c["topic"] == "concrete_strength" for c in conflicts)

def test_relationship_following():
    ids = {d["id"] for d in related_documents(DOCS, "RFI-015")}
    assert "DRW-S-102" in ids and "SPEC-021" in ids

def test_citations_present():
    report = ProjectIntelligenceAgent(DOCS).investigate("Analyze project risks")
    sig = report["major_risks"] + report["outstanding_actions"] + report["commercial_issues"]
    assert sig and all(x.get("citations") for x in sig)

def test_fact_inference_recommendation_separation():
    report = ProjectIntelligenceAgent(DOCS).investigate("Analyze project risks")
    assert all(x["kind"] == "Fact" for x in report["major_risks"])
    assert all(x["kind"] == "Inference" for x in report["potential_delays"])
    assert all(x["kind"] == "Recommendation" for x in report["recommendations"])

def test_minimum_project_dataset_size():
    assert len(DOCS) >= 8

def test_evaluation_dataset_size():
    data = json.loads((ROOT/'evaluation'/'week30_eval_dataset.json').read_text())
    assert len(data) >= 10
