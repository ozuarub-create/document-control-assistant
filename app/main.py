"""FastAPI API for the Document Control Assistant and Document Register."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from app.document_processor import SUPPORTED_EXTENSIONS, process_file
from app.repository import (
    get_document,
    get_version_history,
    ingest_folder,
    list_documents,
    save_processed_document,
    search_documents,
)
from app.search_engine import natural_language_search, semantic_search

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DOCUMENTS_DIR = ROOT_DIR / "sample_documents"

app = FastAPI(
    title="AI Document Control Assistant",
    description="Upload, register, classify, version, and search PDF/DOCX construction documents.",
    version="2.0.0",
)


class SemanticSearchRequest(BaseModel):
    query: str = Field(..., example="Find architectural drawings showing floor layout plans")
    limit: int = Field(10, ge=1, le=50)
    latest_only: bool = True


class NaturalLanguageQueryRequest(BaseModel):
    question: str = Field(..., example="Show me the latest architectural drawings")
    limit: int = Field(10, ge=1, le=50)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "AI Document Control Assistant and Document Register is running.",
        "docs": "Open /docs to test the APIs.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload one document, classify it, extract metadata, and store it in the register."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        processed = process_file(temp_path, file.filename, include_text=True)
        saved = save_processed_document(processed)
        processed.pop("content_text", None)
        processed["register"] = {
            "document_id": saved["id"],
            "version": saved["version"],
            "is_latest": saved["is_latest"],
            "document_key": saved["document_key"],
        }
        return processed
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
    q: str | None = None,
    latest_only: bool = True,
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Traditional search using stored metadata fields."""
    results = search_documents(
        document_type=document_type,
        project_name=project_name,
        contractor=contractor,
        consultant=consultant,
        discipline=discipline,
        revision_number=revision_number,
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


@app.get("/documents/{document_id}/versions")
def document_versions(document_id: int) -> dict[str, Any]:
    results = get_version_history(document_id)
    if not results:
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"document_id": document_id, "versions": results}


@app.get("/documents/{document_id}")
def document_detail(document_id: int) -> dict[str, Any]:
    item = get_document(document_id)
    if not item:
        raise HTTPException(status_code=404, detail="Document not found.")
    return item
