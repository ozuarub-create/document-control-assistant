from __future__ import annotations

from pathlib import Path

from app.database import reset_database
from app.relationship_engine import build_document_relationships, extract_document_identifiers
from app.relationship_repository import get_graph_data, get_related_documents, list_action_items, list_relationships
from app.repository import save_processed_document


def _processed(
    filename: str,
    document_type: str,
    title: str,
    document_number: str,
    content: str,
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
            "discipline": "Architectural",
        },
        "content_text": f"Document Number: {document_number}\n{content}",
        "text_preview": f"Document Number: {document_number}\n{content}",
    }


def _build_fixture(db_path: Path) -> dict[str, dict]:
    reset_database(db_path)
    documents = {
        "drawing": _processed(
            "drawing_a101.pdf",
            "Drawing",
            "Ground Floor Layout Drawing",
            "DWG-A-101",
            "Architectural ground floor layout.",
        ),
        "specification": _processed(
            "spec_033000.pdf",
            "Specification",
            "Concrete Works Specification",
            "SPEC-03-30-00",
            "Concrete materials and workmanship requirements.",
        ),
        "rfi": _processed(
            "rfi_015.pdf",
            "RFI",
            "RFI for Concrete Detail",
            "RFI-015",
            "Referenced Documents: DWG-A-101 and SPEC-03-30-00. Clarify the concrete detail.",
        ),
        "meeting": _processed(
            "mom_007.pdf",
            "Meeting Minutes",
            "Weekly Coordination Meeting Minutes",
            "MOM-007",
            "Referenced Documents: RFI-015 and DWG-A-101.\n"
            "Action Item: Update DWG-A-101 after the RFI response. "
            "Owner: Main Contractor. Due Date: 2026-07-15. Status: Open",
        ),
    }
    return {name: save_processed_document(item, db_path=db_path) for name, item in documents.items()}


def test_identifier_extraction_returns_own_document_number() -> None:
    document = _processed(
        "rfi_015.pdf",
        "RFI",
        "RFI for Concrete Detail",
        "RFI-015",
        "References DWG-A-101 and SPEC-03-30-00.",
    )
    identifiers = extract_document_identifiers(
        {
            "filename": document["filename"],
            "document_title": document["metadata"]["document_title"],
            "content_text": document["content_text"],
        }
    )
    assert "RFI-015" in identifiers
    assert "DWG-A-101" not in identifiers


def test_rfi_links_to_drawing_and_specification(tmp_path: Path) -> None:
    db_path = tmp_path / "relationships.db"
    saved = _build_fixture(db_path)
    summary = build_document_relationships(db_path=db_path, reset=True)
    related = get_related_documents(saved["rfi"]["id"], direction="outgoing", db_path=db_path)
    relationship_types = {item["relationship_type"] for item in related}
    target_types = {item["related_document"]["document_type"] for item in related}

    assert summary["explicit_relationships"] >= 4
    assert "rfi_references_drawing" in relationship_types
    assert "rfi_references_specification" in relationship_types
    assert {"Drawing", "Specification"}.issubset(target_types)


def test_meeting_minutes_create_action_item_and_document_links(tmp_path: Path) -> None:
    db_path = tmp_path / "meeting_relationships.db"
    saved = _build_fixture(db_path)
    build_document_relationships(db_path=db_path, reset=True)

    action_items = list_action_items(meeting_document_id=saved["meeting"]["id"], db_path=db_path)
    meeting_related = get_related_documents(saved["meeting"]["id"], direction="outgoing", db_path=db_path)

    assert len(action_items) == 1
    assert action_items[0]["owner"] == "Main Contractor"
    assert action_items[0]["due_date"] == "2026-07-15"
    assert action_items[0]["related_document_id"] == saved["drawing"]["id"]
    assert any(item["related_document"]["id"] == saved["rfi"]["id"] for item in meeting_related)


def test_graph_data_contains_documents_actions_and_edges(tmp_path: Path) -> None:
    db_path = tmp_path / "graph.db"
    _build_fixture(db_path)
    build_document_relationships(db_path=db_path, reset=True)
    graph = get_graph_data(limit=100, include_action_items=True, db_path=db_path)
    relationships = list_relationships(limit=100, db_path=db_path)

    assert graph["summary"]["document_nodes"] == 4
    assert graph["summary"]["action_item_nodes"] == 1
    assert graph["summary"]["edges"] >= len(relationships) + 1
    assert any(edge["label"] == "action_references_document" for edge in graph["edges"])
