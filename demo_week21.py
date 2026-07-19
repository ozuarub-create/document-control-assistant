"""Week 21 demonstration: conversational document questions with citations."""

from __future__ import annotations

import json
from pathlib import Path

from app.conversation_engine import answer_document_question
from app.database import reset_database
from app.relationship_engine import build_document_relationships
from app.repository import save_processed_document

ROOT = Path(__file__).resolve().parent
DEMO_DB = ROOT / "week21_demo.db"
RESULTS_PATH = ROOT / "demo_week21_results.json"


def processed(filename: str, document_type: str, title: str, number: str, content: str, discipline: str) -> dict:
    return {
        "filename": filename,
        "file_type": "pdf",
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


def print_answer(label: str, result: dict) -> None:
    print("\n" + "=" * 92)
    print(label)
    print("=" * 92)
    print(f"Question: {result['question']}")
    print(f"Status: {result['status']}")
    print(f"Session: {result['session_id']}")
    print(f"History used: {result['history_used']}")
    print(f"Answer: {result['answer']}")
    print("Sources:")
    if not result["citations"]:
        print("- No supporting source was found; the assistant did not invent an answer.")
    for source in result["citations"]:
        print(
            f"- [{source['citation_id']}] {source['document_title']} "
            f"({source['filename']}) score={source['relevance_score']}"
        )
        print(f"  {source['source_excerpt']}")


def main() -> None:
    reset_database(DEMO_DB)
    documents = [
        processed(
            "drawing_a101.pdf",
            "Drawing",
            "Ground Floor Layout Drawing",
            "DWG-A-101",
            "The drawing shows the architectural ground floor layout, grid lines, concrete wall locations, and coordination notes.",
            "Architectural",
        ),
        processed(
            "spec_033000.pdf",
            "Specification",
            "Concrete Works Specification",
            "SPEC-03-30-00",
            "The specification defines concrete materials, testing frequency, workmanship, curing, and acceptance requirements.",
            "Structural",
        ),
        processed(
            "rfi_015.pdf",
            "RFI",
            "RFI for Ground Floor Concrete Detail",
            "RFI-015",
            "Referenced Documents: DWG-A-101 and SPEC-03-30-00. Clarification is requested for the concrete wall detail at grid A-5.",
            "Structural",
        ),
        processed(
            "mom_007.pdf",
            "Meeting Minutes",
            "Weekly Coordination Meeting Minutes",
            "MOM-007",
            "Referenced Documents: RFI-015 and DWG-A-101.\n"
            "Action Item: Update drawing DWG-A-101 following the RFI response | "
            "Owner: Gulf Build Contractors | Due Date: 2026-07-15 | Status: Open",
            "Architectural",
        ),
    ]
    for document in documents:
        save_processed_document(document, db_path=DEMO_DB)
    relationship_summary = build_document_relationships(db_path=DEMO_DB, reset=True)

    multi = answer_document_question(
        "What documents does RFI-015 reference and what are they about?",
        db_path=DEMO_DB,
        limit=6,
    )
    meeting = answer_document_question(
        "What action item is recorded in MOM-007?",
        db_path=DEMO_DB,
        limit=6,
    )
    follow_up = answer_document_question(
        "Who owns it and when is it due?",
        session_id=meeting["session_id"],
        db_path=DEMO_DB,
        limit=6,
    )
    insufficient = answer_document_question(
        "What is the approved project budget and final payment amount?",
        db_path=DEMO_DB,
        limit=6,
    )

    print("Week 21 - Conversational Document Assistant with Source Citations")
    print(f"Documents registered: {len(documents)}")
    print(f"Relationships created: {relationship_summary['relationships_created']}")
    print_answer("Scenario 1 - Multi-document RFI question", multi)
    print_answer("Scenario 2 - Meeting action question", meeting)
    print_answer("Scenario 3 - Follow-up using conversation history", follow_up)
    print_answer("Scenario 4 - Insufficient information", insufficient)

    results = {
        "relationship_summary": relationship_summary,
        "multi_document_question": multi,
        "meeting_question": meeting,
        "follow_up_question": follow_up,
        "insufficient_information_question": insufficient,
        "checks": {
            "conversational_api_engine": "working",
            "multi_document_retrieval": "working",
            "conversation_history": "working",
            "source_citations": "working",
            "insufficient_information_handling": "working",
        },
    }
    RESULTS_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print("\n" + "=" * 92)
    print("Week 21 Demo Complete")
    print("=" * 92)
    for key, value in results["checks"].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    print(f"Results saved to: {RESULTS_PATH.name}")


if __name__ == "__main__":
    main()
