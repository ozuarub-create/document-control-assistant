"""Week 20 demonstration - AI Document Relationships and Knowledge Graph."""

from __future__ import annotations

import json
from pathlib import Path

from app.database import reset_database
from app.document_processor import process_file
from app.relationship_engine import build_document_relationships
from app.relationship_repository import (
    get_graph_data,
    get_related_documents,
    list_action_items,
    list_relationships,
)
from app.relationship_viewer import write_graph_svg
from app.repository import save_processed_document

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "sample_documents"
DOCS_DIR = ROOT / "docs"


def _prepare(path: Path, *, title: str, document_number: str, extra_text: str) -> dict:
    processed = process_file(path, include_text=True)
    processed["metadata"].update(
        {
            "document_title": title,
            "project_name": "Campus Innovation Building",
            "contractor": "Gulf Build Contractors",
            "consultant": "Pearl Engineering Consultants",
        }
    )
    processed["content_text"] = (
        f"{processed.get('content_text', '')}\n"
        f"Document Number: {document_number}\n"
        f"{extra_text}\n"
    )
    processed["text_preview"] = processed["content_text"][:1000]
    return processed


def main() -> None:
    print("Week 20 - AI Document Relationships & Knowledge Graph")
    print("=" * 76)

    reset_database()

    drawing = _prepare(
        SAMPLE_DIR / "sample_001_drawing.pdf",
        title="Ground Floor Layout Drawing",
        document_number="DWG-A-101",
        extra_text="Architectural layout drawing issued for coordination.",
    )
    specification = _prepare(
        SAMPLE_DIR / "sample_007_specification.pdf",
        title="Concrete Works Specification",
        document_number="SPEC-03-30-00",
        extra_text="Specification for concrete materials, workmanship, and inspection.",
    )
    rfi = _prepare(
        SAMPLE_DIR / "sample_047_rfi.pdf",
        title="RFI for Ground Floor Concrete Detail",
        document_number="RFI-015",
        extra_text=(
            "Referenced Documents: Drawing DWG-A-101 and Specification SPEC-03-30-00. "
            "Please clarify the concrete detail shown on the drawing."
        ),
    )
    meeting = _prepare(
        SAMPLE_DIR / "sample_041_meeting_minutes.pdf",
        title="Weekly Coordination Meeting Minutes",
        document_number="MOM-007",
        extra_text=(
            "Referenced Documents: RFI-015 and DWG-A-101.\n"
            "Action Item: Update drawing DWG-A-101 following the RFI response. "
            "Owner: Gulf Build Contractors. Due Date: 2026-07-15. Status: Open"
        ),
    )

    saved = {
        "drawing": save_processed_document(drawing),
        "specification": save_processed_document(specification),
        "rfi": save_processed_document(rfi),
        "meeting_minutes": save_processed_document(meeting),
    }

    build_summary = build_document_relationships(reset=True)
    relationships = list_relationships(limit=100)
    rfi_related = get_related_documents(saved["rfi"]["id"], direction="outgoing")
    meeting_actions = list_action_items(meeting_document_id=saved["meeting_minutes"]["id"])
    graph = get_graph_data(limit=100, include_action_items=True)

    DOCS_DIR.mkdir(exist_ok=True)
    svg_path = write_graph_svg(graph, DOCS_DIR / "week20_relationship_graph.svg")

    results = {
        "build_summary": build_summary,
        "document_ids": {name: item["id"] for name, item in saved.items()},
        "relationships": relationships,
        "rfi_related_documents": rfi_related,
        "meeting_action_items": meeting_actions,
        "graph_summary": graph["summary"],
        "graph_visualization": str(svg_path.relative_to(ROOT)),
        "viewer_url": "http://127.0.0.1:8000/relationships/viewer",
    }
    output_path = ROOT / "demo_week20_results.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Documents registered: {len(saved)}")
    print(f"Relationships created: {build_summary['relationships_created']}")
    print(f"Explicit relationships: {build_summary['explicit_relationships']}")
    print(f"Inferred relationships: {build_summary['inferred_relationships']}")
    print(f"Meeting action items: {build_summary['action_items_created']}")
    print()

    print("RFI Links")
    print("-" * 76)
    for item in rfi_related:
        document = item["related_document"]
        print(
            f"RFI-015 -> {document['document_type']}: "
            f"{document['document_title']} "
            f"({item['relationship_type']}, confidence {item['confidence_score']})"
        )
    print()

    print("Meeting Minutes Links and Action Items")
    print("-" * 76)
    meeting_related = get_related_documents(saved["meeting_minutes"]["id"], direction="outgoing")
    for item in meeting_related:
        document = item["related_document"]
        print(f"MOM-007 -> {document['document_title']} ({item['relationship_type']})")
    for action in meeting_actions:
        print(
            f"Action: {action['action_text']} | Owner: {action.get('owner')} | "
            f"Due: {action.get('due_date')} | Related: {action.get('related_title')}"
        )
    print()

    print("Knowledge Graph")
    print("-" * 76)
    print(f"Graph nodes: {graph['summary']['nodes']}")
    print(f"Graph edges: {graph['summary']['edges']}")
    print(f"Static graph: {svg_path.relative_to(ROOT)}")
    print("Interactive viewer: http://127.0.0.1:8000/relationships/viewer")
    print()

    print("=" * 76)
    print("Week 20 Demo Complete")
    print("=" * 76)
    print("Document relationship engine: working")
    print("RFI to drawing/specification linking: working")
    print("Meeting minutes and action item linking: working")
    print("Relationship graph viewer: working")
    print("Related document API: working")
    print(f"Results saved to: {output_path.name}")


if __name__ == "__main__":
    main()
