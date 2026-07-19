"""FastAPI API for the integrated AI Document Control Assistant platform."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from app.analytics import generate_platform_analytics

from app.compliance_engine import check_document_compliance, get_compliance_rules
from app.compliance_pdf import write_json_report, write_pdf_report
from app.compliance_repository import (
    get_latest_compliance_report_for_document,
    list_compliance_reports,
    save_compliance_report,
)
from app.conversation_engine import answer_document_question, get_conversation_capabilities
from app.conversation_repository import (
    delete_conversation_session,
    get_conversation_session,
    list_conversation_sessions,
)
from app.document_processor import SUPPORTED_EXTENSIONS, process_file
from app.repository import (
    get_document,
    get_version_history,
    ingest_folder,
    list_documents,
    save_processed_document,
    search_documents,
)
from app.review_engine import review_document
from app.review_repository import get_latest_review_for_document, list_review_reports, save_review_report
from app.relationship_engine import build_document_relationships, get_relationship_rules
from app.relationship_repository import (
    get_graph_data,
    get_related_documents,
    list_action_items,
    list_relationships,
)
from app.relationship_viewer import relationship_viewer_html
from app.search_engine import natural_language_search, semantic_search
from app.workflow import (
    apply_review_workflow,
    get_document_workflow,
    get_workflow_states,
    get_workflow_summary,
    update_workflow_state,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DOCUMENTS_DIR = ROOT_DIR / "sample_documents"
COMPLIANCE_REPORTS_DIR = ROOT_DIR / "compliance_reports"

app = FastAPI(
    title="AI Document Control Assistant",
    description=(
        "Upload, register, classify, version, search, review, route, and report "
        "PDF/DOCX construction documents with compliance checking, relationship mapping, and cited conversations."
    ),
    version="7.0.0",
)


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., example="Find architectural drawings showing floor layout plans")
    limit: int = Field(10, ge=1, le=50)
    latest_only: bool = True


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(..., example="Show me the latest architectural drawings")
    limit: int = Field(10, ge=1, le=50)


class ConversationRequest(BaseModel):
    question: str = Field(..., min_length=2, example="What documents are referenced by RFI-015?")
    session_id: str | None = Field(None, example="optional-existing-session-id")
    limit: int = Field(6, ge=1, le=12)
    latest_only: bool = True


class WorkflowUpdateRequest(BaseModel):
    state: str = Field(..., example="approved")
    action: str | None = Field(None, example="manager_approved")
    user: str = Field("system", example="document-controller")
    comment: str | None = Field(None, example="Reviewed and accepted for submission")


async def _process_uploaded_file(file: UploadFile) -> tuple[dict[str, Any], str | None]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    temp_path = None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        processed = process_file(temp_path, file.filename, include_text=True)
        return processed, temp_path
    except Exception:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
        raise


def _remove_long_text(processed: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(processed)
    cleaned.pop("content_text", None)
    return cleaned




def _save_compliance_outputs(report: dict[str, Any], prefix: str = "compliance_report") -> dict[str, str]:
    COMPLIANCE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(str(report.get("filename", "document"))).stem.replace(" ", "_")
    timestamp = str(report.get("generated_at", "now")).replace(":", "-").replace("+", "_")[:32]
    base = f"{prefix}_{safe_name}_{timestamp}"
    json_path = COMPLIANCE_REPORTS_DIR / f"{base}.json"
    pdf_path = COMPLIANCE_REPORTS_DIR / f"{base}.pdf"
    write_json_report(report, json_path)
    write_pdf_report(report, pdf_path)
    return {"json_report_path": str(json_path), "pdf_report_path": str(pdf_path)}


def _dashboard_html() -> str:
    analytics = generate_platform_analytics()
    totals = analytics["document_totals"]
    classification = analytics["classification"]
    review_quality = analytics["review_quality"]
    workflow = analytics["workflow"]["by_state"]
    latest = analytics["latest_documents_preview"]

    def rows(items: list[dict[str, Any]]) -> str:
        if not items:
            return "<tr><td colspan='5'>No documents registered yet.</td></tr>"
        return "".join(
            f"<tr><td>{item.get('id')}</td><td>{item.get('filename')}</td>"
            f"<td>{item.get('document_type')}</td><td>{item.get('workflow_state')}</td>"
            f"<td>{item.get('project_name')}</td></tr>"
            for item in items
        )

    def cards(data: dict[str, Any]) -> str:
        return "".join(f"<div class='card'><b>{key.replace('_', ' ').title()}</b><span>{value}</span></div>" for key, value in data.items())

    return f"""
    <!doctype html>
    <html>
    <head>
        <title>AI Document Control Assistant Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 30px; background: #f5f7fb; color: #1f2937; }}
            h1 {{ margin-bottom: 5px; }}
            .subtitle {{ color: #6b7280; margin-bottom: 25px; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }}
            .card {{ background: white; border-radius: 10px; padding: 18px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
            .card b {{ display: block; font-size: 13px; color: #6b7280; margin-bottom: 8px; }}
            .card span {{ font-size: 26px; font-weight: bold; color: #111827; }}
            section {{ background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: left; font-size: 14px; }}
            th {{ background: #eef2ff; }}
            .links a {{ margin-right: 15px; color: #2563eb; text-decoration: none; }}
            pre {{ background: #111827; color: #f9fafb; padding: 15px; border-radius: 8px; overflow-x: auto; }}
        </style>
    </head>
    <body>
        <h1>AI Document Control Assistant</h1>
        <div class="subtitle">Integrated AI document lifecycle platform with Week 20 relationship mapping</div>
        <div class="links"><a href="/docs">API Docs</a><a href="/documents">Documents JSON</a><a href="/documents/analytics">Analytics JSON</a><a href="/relationships/viewer">Relationship Viewer</a></div>
        <h2>Platform Metrics</h2>
        <div class="grid">
            {cards(totals)}
            <div class='card'><b>Average Confidence</b><span>{classification['average_confidence_score']}</span></div>
            <div class='card'><b>Total Reviews</b><span>{review_quality['total_reviews']}</span></div>
            <div class='card'><b>Average Quality</b><span>{review_quality['average_quality_score']}</span></div>
            <div class='card'><b>Duplicate Reviews</b><span>{review_quality['duplicate_reviews']}</span></div>
        </div>
        <section>
            <h2>Workflow States</h2>
            <div class="grid">{cards(workflow)}</div>
        </section>
        <section>
            <h2>Latest Documents</h2>
            <table>
                <tr><th>ID</th><th>Filename</th><th>Type</th><th>Workflow State</th><th>Project</th></tr>
                {rows(latest)}
            </table>
        </section>
        <section>
            <h2>Document Types</h2>
            <pre>{classification['by_document_type']}</pre>
        </section>
    </body>
    </html>
    """


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "AI Document Control Assistant with cited conversational search is running.",
        "dashboard": "Open /dashboard for the web interface.",
        "docs": "Open /docs to test the APIs.",
        "relationships": "Open /relationships/viewer for the document graph.",
        "conversation": "POST questions to /conversation/ask and reuse the returned session_id.",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    """Simple web dashboard for document control analytics and lifecycle state."""
    return _dashboard_html()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload one document, classify it, extract metadata, review it, store it, and update workflow."""
    temp_path = None
    try:
        processed, temp_path = await _process_uploaded_file(file)
        review_report = review_document(processed)
        compliance_report = check_document_compliance(processed)
        compliance_paths = _save_compliance_outputs(compliance_report, prefix="upload_compliance")
        saved = save_processed_document(processed)
        saved_review = save_review_report(review_report, document_id=saved["id"])
        saved_compliance = save_compliance_report(
            compliance_report,
            document_id=saved["id"],
            document_key=saved["document_key"],
            json_report_path=compliance_paths["json_report_path"],
            pdf_report_path=compliance_paths["pdf_report_path"],
        )
        workflow_result = apply_review_workflow(saved["id"], review_report)
        relationship_summary = build_document_relationships(reset=True)

        response = _remove_long_text(processed)
        response["register"] = {
            "document_id": saved["id"],
            "version": saved["version"],
            "is_latest": saved["is_latest"],
            "document_key": saved["document_key"],
        }
        response["workflow"] = {
            "state": workflow_result.get("workflow_state"),
            "last_action": workflow_result.get("last_workflow_action"),
        }
        response["review_report"] = review_report
        response["review_report"]["stored_review_id"] = saved_review["id"]
        response["compliance_report"] = compliance_report
        response["compliance_report"]["stored_compliance_id"] = saved_compliance["id"]
        response["compliance_report_paths"] = compliance_paths
        response["relationship_update"] = relationship_summary
        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@app.post("/documents/review-upload")
async def review_uploaded_document(
    file: UploadFile = File(...),
    save_to_register: bool = False,
) -> dict[str, Any]:
    """Review an uploaded document before submission.

    Set save_to_register=true if you also want to store it in the document register.
    """
    temp_path = None
    try:
        processed, temp_path = await _process_uploaded_file(file)
        review_report = review_document(processed)
        response = _remove_long_text(processed)
        response["review_report"] = review_report

        if save_to_register:
            saved = save_processed_document(processed)
            saved_review = save_review_report(review_report, document_id=saved["id"])
            workflow_result = apply_review_workflow(saved["id"], review_report)
            relationship_summary = build_document_relationships(reset=True)
            response["register"] = {
                "document_id": saved["id"],
                "version": saved["version"],
                "is_latest": saved["is_latest"],
                "document_key": saved["document_key"],
            }
            response["workflow"] = {
                "state": workflow_result.get("workflow_state"),
                "last_action": workflow_result.get("last_workflow_action"),
            }
            response["review_report"]["stored_review_id"] = saved_review["id"]
            response["relationship_update"] = relationship_summary

        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@app.post("/documents/compliance-check")
async def compliance_check_uploaded_document(
    file: UploadFile = File(...),
    save_to_register: bool = False,
    generate_pdf: bool = True,
) -> dict[str, Any]:
    """Check an uploaded document against Week 19 compliance requirements.

    Returns a structured JSON report and, when generate_pdf=true, writes a PDF
    report to the local compliance_reports folder.
    """
    temp_path = None
    try:
        processed, temp_path = await _process_uploaded_file(file)
        compliance_report = check_document_compliance(processed)
        output_paths: dict[str, str] = {}
        if generate_pdf:
            output_paths = _save_compliance_outputs(compliance_report)

        response = _remove_long_text(processed)
        response["compliance_report"] = compliance_report
        response["compliance_report_paths"] = output_paths

        if save_to_register:
            saved = save_processed_document(processed)
            saved_compliance = save_compliance_report(
                compliance_report,
                document_id=saved["id"],
                document_key=saved["document_key"],
                json_report_path=output_paths.get("json_report_path"),
                pdf_report_path=output_paths.get("pdf_report_path"),
            )
            response["register"] = {
                "document_id": saved["id"],
                "version": saved["version"],
                "is_latest": saved["is_latest"],
                "document_key": saved["document_key"],
            }
            response["compliance_report"]["stored_compliance_id"] = saved_compliance["id"]
            response["relationship_update"] = build_document_relationships(reset=True)

        return response
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@app.post("/documents/rebuild-sample-register")
def rebuild_sample_register(reset: bool = True) -> dict[str, Any]:
    """Load the 50 sample documents into the SQLite metadata repository."""
    if not SAMPLE_DOCUMENTS_DIR.exists():
        raise HTTPException(status_code=404, detail="sample_documents folder not found.")
    documents = ingest_folder(SAMPLE_DOCUMENTS_DIR, reset=reset)
    relationship_summary = build_document_relationships(reset=True)
    return {
        "message": "Sample document register and relationship graph built successfully.",
        "documents_loaded": len(documents),
        "reset_database": reset,
        "relationship_summary": relationship_summary,
    }


@app.get("/documents")
def documents(limit: int = Query(50, ge=1, le=200), latest_only: bool = True) -> dict[str, Any]:
    items = list_documents(limit=limit, latest_only=latest_only)
    return {"count": len(items), "results": items}


@app.get("/documents/search")
def traditional_search(
    document_type: str | None = None,
    project_name: str | None = None,
    contractor: str | None = None,
    consultant: str | None = None,
    discipline: str | None = None,
    revision_number: str | None = None,
    workflow_state: str | None = None,
    q: str | None = None,
    latest_only: bool = True,
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Traditional search using stored metadata fields and workflow state."""
    results = search_documents(
        document_type=document_type,
        project_name=project_name,
        contractor=contractor,
        consultant=consultant,
        discipline=discipline,
        revision_number=revision_number,
        workflow_state=workflow_state,
        q=q,
        latest_only=latest_only,
        limit=limit,
    )
    return {"count": len(results), "results": results}


@app.post("/documents/semantic-search")
def semantic_search_api(request: SemanticSearchRequest) -> dict[str, Any]:
    """AI-powered semantic search using local embeddings."""
    results = semantic_search(
        request.query,
        limit=request.limit,
        latest_only=request.latest_only,
    )
    return {"query": request.query, "count": len(results), "results": results}


@app.post("/documents/query")
def natural_language_query(request: NaturalLanguageQueryRequest) -> dict[str, Any]:
    """Ask natural-language questions about the document register."""
    return natural_language_search(request.question, limit=request.limit)


@app.post("/conversation/ask")
def conversation_ask(request: ConversationRequest) -> dict[str, Any]:
    """Ask a document question. Answers include structured source citations."""
    try:
        return answer_document_question(
            request.question,
            session_id=request.session_id,
            limit=request.limit,
            latest_only=request.latest_only,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/conversation/capabilities")
def conversation_capabilities() -> dict[str, Any]:
    """Describe retrieval, citation, history, and safety behavior."""
    return get_conversation_capabilities()


@app.get("/conversation/sessions")
def conversation_sessions(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """List stored conversation sessions."""
    sessions = list_conversation_sessions(limit=limit)
    return {"count": len(sessions), "results": sessions}


@app.get("/conversation/{session_id}")
def conversation_history(session_id: str) -> dict[str, Any]:
    """Return one complete conversation with citations and message history."""
    session = get_conversation_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation session not found.")
    return session


@app.delete("/conversation/{session_id}")
def conversation_delete(session_id: str) -> dict[str, Any]:
    """Delete one conversation session and its messages."""
    deleted = delete_conversation_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation session not found.")
    return {"message": "Conversation deleted.", "session_id": session_id}


@app.get("/documents/compliance-rules")
def compliance_rules() -> dict[str, Any]:
    """Return configurable validation rules by document type."""
    return get_compliance_rules()


@app.get("/documents/analytics")
def analytics_report() -> dict[str, Any]:
    """Analytics and reporting for the full platform."""
    return generate_platform_analytics()


@app.get("/documents/workflow")
def workflow_states() -> dict[str, Any]:
    """List workflow states, allowed transitions, and current state counts."""
    result = get_workflow_states()
    result["summary"] = get_workflow_summary()
    return result


@app.get("/documents/reviews")
def review_reports(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """List stored document review reports."""
    reports = list_review_reports(limit=limit)
    return {"count": len(reports), "results": reports}


@app.get("/documents/compliance-reports")
def compliance_reports(limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
    """List stored compliance validation reports."""
    reports = list_compliance_reports(limit=limit)
    return {"count": len(reports), "results": reports}


@app.get("/relationships/viewer", response_class=HTMLResponse)
def relationship_viewer() -> str:
    """Interactive browser graph for documents, references, and meeting action items."""
    return relationship_viewer_html()


@app.post("/relationships/rebuild")
def rebuild_relationships(reset: bool = True, latest_only: bool = True) -> dict[str, Any]:
    """Scan registered documents and rebuild detected relationships."""
    return build_document_relationships(reset=reset, latest_only=latest_only)


@app.get("/relationships")
def relationships(
    relationship_type: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
) -> dict[str, Any]:
    """List detected document-to-document relationship edges."""
    results = list_relationships(limit=limit, relationship_type=relationship_type)
    return {"count": len(results), "results": results}


@app.get("/relationships/graph-data")
def relationship_graph_data(
    limit: int = Query(300, ge=1, le=1000),
    include_action_items: bool = True,
    include_isolated: bool = False,
) -> dict[str, Any]:
    """Return graph nodes and edges for the relationship viewer."""
    return get_graph_data(
        limit=limit,
        include_action_items=include_action_items,
        include_isolated=include_isolated,
    )


@app.get("/relationships/rules")
def relationship_rules() -> dict[str, Any]:
    """Show the transparent rules used to detect document relationships."""
    return get_relationship_rules()


@app.get("/documents/{document_id}/related")
def related_documents(
    document_id: int,
    direction: str = Query("both", pattern="^(both|incoming|outgoing)$"),
    relationship_type: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """Retrieve documents related to a selected document."""
    if not get_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        results = get_related_documents(
            document_id,
            direction=direction,
            relationship_type=relationship_type,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"document_id": document_id, "count": len(results), "results": results}


@app.get("/documents/{document_id}/action-items")
def document_action_items(
    document_id: int,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    """Retrieve action items extracted from one meeting-minutes document."""
    document = get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    results = list_action_items(meeting_document_id=document_id, limit=limit)
    return {"document_id": document_id, "count": len(results), "results": results}


@app.get("/documents/{document_id}/versions")
def document_versions(document_id: int) -> dict[str, Any]:
    results = get_version_history(document_id)
    if not results:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document_id": document_id, "versions": results}


@app.get("/documents/{document_id}/workflow")
def document_workflow(document_id: int) -> dict[str, Any]:
    try:
        return get_document_workflow(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/documents/{document_id}/workflow")
def update_document_workflow(document_id: int, request: WorkflowUpdateRequest) -> dict[str, Any]:
    """Move a document through its lifecycle workflow."""
    try:
        updated = update_workflow_state(
            document_id,
            request.state,
            action=request.action,
            user=request.user,
            comment=request.comment,
        )
        return {
            "message": "Workflow state updated.",
            "document_id": document_id,
            "workflow_state": updated.get("workflow_state"),
            "last_workflow_action": updated.get("last_workflow_action"),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/documents/{document_id}/review")
def document_review(document_id: int) -> dict[str, Any]:
    report = get_latest_review_for_document(document_id)
    if not report:
        raise HTTPException(status_code=404, detail="Review report not found for this document.")
    return report


@app.get("/documents/{document_id}/compliance")
def document_compliance(document_id: int) -> dict[str, Any]:
    report = get_latest_compliance_report_for_document(document_id)
    if not report:
        raise HTTPException(status_code=404, detail="Compliance report not found for this document.")
    return report


@app.get("/documents/{document_id}/compliance/pdf")
def document_compliance_pdf(document_id: int) -> FileResponse:
    report = get_latest_compliance_report_for_document(document_id)
    if not report:
        raise HTTPException(status_code=404, detail="Compliance report not found for this document.")
    pdf_path = report.get("pdf_report_path")
    if not pdf_path or not Path(str(pdf_path)).exists():
        report_data = report.get("report", {})
        output_paths = _save_compliance_outputs(report_data, prefix=f"document_{document_id}_compliance")
        pdf_path = output_paths["pdf_report_path"]
    return FileResponse(str(pdf_path), media_type="application/pdf", filename=Path(str(pdf_path)).name)


@app.get("/documents/{document_id}")
def document_detail(document_id: int) -> dict[str, Any]:
    item = get_document(document_id)
    if not item:
        raise HTTPException(status_code=404, detail="Document not found.")
    return item
