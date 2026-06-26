"""FastAPI API for the integrated AI Document Control Assistant platform."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.analytics import generate_platform_analytics
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

app = FastAPI(
    title="AI Document Control Assistant",
    description=(
        "Upload, register, classify, version, search, review, route, and report "
        "PDF/DOCX construction documents."
    ),
    version="4.0.0",
)


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., example="Find architectural drawings showing floor layout plans")
    limit: int = Field(10, ge=1, le=50)
    latest_only: bool = True


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(..., example="Show me the latest architectural drawings")
    limit: int = Field(10, ge=1, le=50)


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
        <div class="subtitle">Integrated Week 15, Week 16, Week 17, and Week 18 platform dashboard</div>
        <div class="links"><a href="/docs">API Docs</a><a href="/documents">Documents JSON</a><a href="/documents/analytics">Analytics JSON</a></div>
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
        "message": "AI Document Control Assistant is running.",
        "dashboard": "Open /dashboard for the web interface.",
        "docs": "Open /docs to test the APIs.",
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
        saved = save_processed_document(processed)
        saved_review = save_review_report(review_report, document_id=saved["id"])
        workflow_result = apply_review_workflow(saved["id"], review_report)

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
    return {
        "message": "Sample document register built successfully.",
        "documents_loaded": len(documents),
        "reset_database": reset,
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


@app.get("/documents/{document_id}")
def document_detail(document_id: int) -> dict[str, Any]:
    item = get_document(document_id)
    if not item:
        raise HTTPException(status_code=404, detail="Document not found.")
    return item
