from pathlib import Path

from app.analytics import generate_platform_analytics
from app.database import reset_database
from app.repository import ingest_document, search_documents
from app.workflow import get_document_workflow, get_workflow_summary, update_workflow_state

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_documents"


def test_week18_workflow_state_and_history(tmp_path):
    db_path = tmp_path / "workflow.db"
    reset_database(db_path)
    document = ingest_document(SAMPLE_DIR / "sample_001_drawing.pdf", db_path=db_path)

    under_review = update_workflow_state(
        document["id"],
        "under_review",
        action="submit_for_review",
        db_path=db_path,
    )
    approved = update_workflow_state(
        document["id"],
        "approved",
        action="approve_document",
        db_path=db_path,
    )
    workflow = get_document_workflow(document["id"], db_path=db_path)

    assert under_review["workflow_state"] == "under_review"
    assert approved["workflow_state"] == "approved"
    assert workflow["current_state"] == "approved"
    assert len(workflow["history"]) == 2


def test_week18_search_can_filter_by_workflow_state(tmp_path):
    db_path = tmp_path / "search_workflow.db"
    reset_database(db_path)
    document = ingest_document(SAMPLE_DIR / "sample_001_drawing.pdf", db_path=db_path)
    update_workflow_state(document["id"], "under_review", db_path=db_path)

    results = search_documents(workflow_state="under_review", db_path=db_path)

    assert len(results) == 1
    assert results[0]["workflow_state"] == "under_review"


def test_week18_analytics_report_contains_required_sections(tmp_path):
    db_path = tmp_path / "analytics.db"
    reset_database(db_path)
    drawing = ingest_document(SAMPLE_DIR / "sample_001_drawing.pdf", db_path=db_path)
    ingest_document(SAMPLE_DIR / "sample_007_specification.pdf", db_path=db_path)
    update_workflow_state(drawing["id"], "under_review", db_path=db_path)

    report = generate_platform_analytics(db_path=db_path)
    summary = get_workflow_summary(db_path=db_path)

    assert report["document_totals"]["latest_documents"] == 2
    assert "Drawing" in report["classification"]["by_document_type"]
    assert report["workflow"]["by_state"]["under_review"] == 1
    assert summary["under_review"] == 1
