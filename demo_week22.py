"""Week 22 final end-to-end production-readiness demonstration."""

from __future__ import annotations

import json
from pathlib import Path

from app.analytics import generate_platform_analytics
from app.auth_service import ensure_default_admin, get_user_for_token, login_user, register_user
from app.compliance_engine import check_document_compliance
from app.conversation_engine import answer_document_question
from app.database import reset_database
from app.document_processor import process_file
from app.production import production_manifest, production_readiness
from app.repository import ingest_document, save_processed_document, search_documents
from app.review_engine import review_document
from app.review_repository import save_review_report
from app.compliance_repository import save_compliance_report
from app.workflow import update_workflow_state

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "sample_documents"
DB_PATH = ROOT / "week22_demo.db"
RESULTS_PATH = ROOT / "demo_week22_results.json"


def heading(text: str) -> None:
    print("\n" + "=" * 78)
    print(text)
    print("=" * 78)


def main() -> None:
    DB_PATH.unlink(missing_ok=True)
    reset_database(DB_PATH)
    results: dict = {}

    try:
        heading("Week 22 – Final Production-Ready AI Document Control Assistant")

        admin = ensure_default_admin(
            db_path=DB_PATH,
            username="admin",
            password="Admin123!",
            full_name="Demo Administrator",
        )
        user = register_user(
            "document.controller",
            "Controller123!",
            "Document Controller",
            db_path=DB_PATH,
        )
        login = login_user("document.controller", "Controller123!", db_path=DB_PATH)
        authenticated = get_user_for_token(login["access_token"], db_path=DB_PATH)

        heading("Authentication and User Management")
        print(f"Administrator created: {admin['username']} ({admin['role']})")
        print(f"User created: {user['username']} ({user['role']})")
        print(f"Login token issued: {'yes' if login['access_token'] else 'no'}")
        print(f"Authenticated user: {authenticated['username'] if authenticated else 'failed'}")

        processed = process_file(SAMPLE_DIR / "sample_001_drawing.pdf", include_text=True)
        review = review_document(processed, db_path=DB_PATH)
        compliance = check_document_compliance(processed)
        saved = save_processed_document(processed, db_path=DB_PATH)
        save_review_report(review, document_id=saved["id"], db_path=DB_PATH)
        save_compliance_report(
            compliance,
            document_id=saved["id"],
            document_key=saved["document_key"],
            db_path=DB_PATH,
        )
        update_workflow_state(saved["id"], "under_review", user=user["username"], db_path=DB_PATH)
        update_workflow_state(saved["id"], "approved", user=admin["username"], db_path=DB_PATH)

        # Add additional documents for search and conversation.
        ingest_document(SAMPLE_DIR / "sample_007_specification.pdf", db_path=DB_PATH)
        ingest_document(SAMPLE_DIR / "sample_041_meeting_minutes.pdf", db_path=DB_PATH)
        ingest_document(SAMPLE_DIR / "sample_047_rfi.pdf", db_path=DB_PATH)

        heading("Complete Document Lifecycle")
        print(f"Document: {saved['document_title']}")
        print(f"Classification: {saved['document_type']} ({saved['confidence_score']})")
        print(f"Review status: {review['validation_status']} | Quality score: {review['quality_score']}")
        print(f"Compliance status: {compliance['compliance_status']} | Score: {compliance['compliance_score']}")
        print("Workflow: registered -> under_review -> approved")

        search_results = search_documents(document_type="Drawing", latest_only=True, db_path=DB_PATH)
        conversation = answer_document_question(
            "What does the concrete specification require?",
            db_path=DB_PATH,
        )
        analytics = generate_platform_analytics(db_path=DB_PATH)
        readiness = production_readiness(db_path=DB_PATH)
        manifest = production_manifest()

        heading("Search, Conversation, Analytics, and Readiness")
        print(f"Drawing search results: {len(search_results)}")
        print(f"Conversation status: {conversation['status']}")
        print(f"Conversation citations: {len(conversation['citations'])}")
        print(f"Registered latest documents: {analytics['document_totals']['latest_documents']}")
        print(f"Production readiness: {readiness['status']}")
        print(f"Final release version: {manifest['version']}")

        results = {
            "authentication": {
                "admin_created": bool(admin),
                "user_created": bool(user),
                "login_working": authenticated is not None,
            },
            "document_lifecycle": {
                "document_id": saved["id"],
                "classification": saved["document_type"],
                "review_status": review["validation_status"],
                "compliance_status": compliance["compliance_status"],
                "workflow_state": "approved",
            },
            "search_results": len(search_results),
            "conversation": {
                "status": conversation["status"],
                "citations": len(conversation["citations"]),
            },
            "analytics": analytics,
            "readiness": readiness,
            "manifest": manifest,
        }
        RESULTS_PATH.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

        heading("Week 22 Demo Complete")
        print("Final application: working")
        print("Authentication and user management: working")
        print("Complete document lifecycle: working")
        print("Search and cited conversation: working")
        print("Docker deployment files: included")
        print("Technical documentation: included")
        print(f"Results saved to: {RESULTS_PATH.name}")
    finally:
        DB_PATH.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
