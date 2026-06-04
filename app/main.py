"""FastAPI upload API for the Document Control Assistant."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.document_processor import SUPPORTED_EXTENSIONS, process_file

app = FastAPI(
    title="AI Document Control Assistant",
    description="Upload PDF or DOCX construction documents and classify them with extracted metadata.",
    version="1.0.0",
)


@app.get("/")
def home() -> dict[str, str]:
    return {
        "message": "AI Document Control Assistant is running.",
        "docs": "Open /docs to test the upload API.",
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)) -> dict:
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

        return process_file(temp_path, file.filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
