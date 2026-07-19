from __future__ import annotations

from pathlib import Path

from app.conversation_engine import answer_document_question
from app.conversation_repository import get_conversation_session
from app.database import reset_database
from app.relationship_engine import build_document_relationships
from app.repository import save_processed_document


def _processed(
    filename: str,
    document_type: str,
    title: str,
    number: str,
    content: str,
    discipline: str = "Architectural",
) -> dict:
    return {
        "filename": filename,
        "file_type": Path(filename).suffix.lstrip(".") or "pdf",
        "classification": {
            "document_type": document_type,
            "confidence_score": 0.98,
            "matched_keywords": [],
            "scores": {document_type: 1.0},
        },
        "metadata": {
            "document_title": title,
            "revision_number": "R1",
            "project_name": "Campus Innovation Building",
            "contractor": "Gulf Build Contractors",
            "consultant": "Pearl Engineering Consultants",
            "submission_date": "2026-07-01",
            "discipline": discipline,
        },
        "content_text": f"Document Number: {number}\n{content}",
        "text_preview": f"Document Number: {number}\n{content}",
    }


def _fixture(db_path: Path) -> dict[str, dict]:
    reset_database(db_path)
    documents = {
        "drawing": _processed(
            "drawing_a101.pdf",
            "Drawing",
            "Ground Floor Layout Drawing",
            "DWG-A-101",
            "The drawing shows the architectural ground floor layout, grid lines, and concrete wall detail.",
        ),
        "spec": _processed(
            "spec_033000.pdf",
            "Specification",
            "Concrete Works Specification",
            "SPEC-03-30-00",
            "The specification defines concrete materials, testing, workmanship, and acceptance requirements.",
            "Structural",
        ),
        "rfi": _processed(
            "rfi_015.pdf",
            "RFI",
            "RFI for Ground Floor Concrete Detail",
            "RFI-015",
            "Referenced Documents: DWG-A-101 and SPEC-03-30-00. Clarification is requested for the ground floor concrete detail.",
            "Structural",
        ),
        "meeting": _processed(
            "mom_007.pdf",
            "Meeting Minutes",
            "Weekly Coordination Meeting Minutes",
            "MOM-007",
            "Referenced Documents: RFI-015 and DWG-A-101.\n"
            "Action Item: Update drawing DWG-A-101 following the RFI response | "
            "Owner: Gulf Build Contractors | Due Date: 2026-07-15 | Status: Open",
        ),
    }
    saved = {name: save_processed_document(data, db_path=db_path) for name, data in documents.items()}
    build_document_relationships(db_path=db_path, reset=True)
    return saved


def test_answer_includes_source_citations(tmp_path: Path) -> None:
    db_path = tmp_path / "conversation.db"
    _fixture(db_path)
    result = answer_document_question(
        "What does the concrete specification require?",
        db_path=db_path,
    )

    assert result["status"] == "answered"
    assert result["citations"]
    assert "[S1]" in result["answer"]
    assert result["citations"][0]["filename"]
    assert result["citations"][0]["source_excerpt"]


def test_multi_document_question_uses_multiple_sources(tmp_path: Path) -> None:
    db_path = tmp_path / "multi.db"
    _fixture(db_path)
    result = answer_document_question(
        "What documents does RFI-015 reference and what are they about?",
        db_path=db_path,
        limit=6,
    )

    cited_types = {item["document_type"] for item in result["citations"]}
    assert result["status"] == "answered"
    assert len(result["citations"]) >= 2
    assert "Drawing" in cited_types
    assert "Specification" in cited_types


def test_follow_up_question_uses_conversation_history(tmp_path: Path) -> None:
    db_path = tmp_path / "history.db"
    _fixture(db_path)
    first = answer_document_question(
        "What action item is recorded in MOM-007?",
        db_path=db_path,
    )
    follow_up = answer_document_question(
        "Who owns it and when is it due?",
        session_id=first["session_id"],
        db_path=db_path,
    )

    assert follow_up["history_used"] is True
    assert "Gulf Build Contractors" in follow_up["answer"]
    assert "2026-07-15" in follow_up["answer"]
    assert follow_up["citations"]

    stored = get_conversation_session(first["session_id"], db_path=db_path)
    assert stored is not None
    assert stored["message_count"] == 4


def test_insufficient_information_is_handled_without_fabrication(tmp_path: Path) -> None:
    db_path = tmp_path / "insufficient.db"
    _fixture(db_path)
    result = answer_document_question(
        "What is the approved project budget and final payment amount?",
        db_path=db_path,
    )

    assert result["status"] == "insufficient_information"
    assert result["insufficient_information"] is True
    assert result["citations"] == []
    assert "could not find enough information" in result["answer"].lower()
