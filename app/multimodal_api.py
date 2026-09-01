"""FastAPI routes for Week 23 multimodal document intelligence."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.multimodal_engine import analyze_pdf
from app.pdf_visualizer import parse_page_numbers
from app.vision_provider import DEFAULT_MODEL


ROOT_DIR = Path(__file__).resolve().parent.parent
TEST_DOCUMENTS_DIR = ROOT_DIR / "multimodal_test_documents"
ACCURACY_REPORT_PATH = ROOT_DIR / "accuracy_report_week23.json"

router = APIRouter(prefix="/multimodal", tags=["Week 23 Multimodal Intelligence"])


def _save_upload(file: UploadFile) -> str:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported by the Week 23 service.")
    return suffix


@router.get("/capabilities")
def multimodal_capabilities() -> dict[str, Any]:
    """Describe the visual and text extraction capabilities."""

    return {
        "service": "Week 23 Multimodal Document Intelligence",
        "accepted_file_types": ["pdf"],
        "page_rendering": "PyMuPDF PNG rendering",
        "production_vision_provider": "OpenAI Responses API image input",
        "default_vision_model": DEFAULT_MODEL,
        "offline_test_provider": "Deterministic fixtures for bundled synthetic pages only",
        "extracts": [
            "title_blocks",
            "tables",
            "drawing_notes",
            "stamps",
            "revision_information",
            "symbols_and_visual_annotations",
        ],
        "comparison": "PDF text layer versus visual page analysis",
        "structured_output": ["page_number", "confidence", "evidence", "visual_only_findings"],
    }


@router.post("/analyze")
async def multimodal_analyze(
    file: UploadFile = File(...),
    provider: str = Query("auto", pattern="^(auto|openai|fixture)$"),
    model: str | None = Query(None, description="Optional vision model override"),
    page_numbers: str | None = Query(None, description="Comma-separated 1-based page numbers, e.g. 1,3"),
    max_pages: int = Query(5, ge=1, le=50),
    dpi: int = Query(150, ge=72, le=300),
    keep_images: bool = Query(False),
) -> dict[str, Any]:
    """Analyze uploaded PDF pages visually and textually and return structured JSON."""

    suffix = _save_upload(file)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            selected_pages = parse_page_numbers(page_numbers)
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return analyze_pdf(
            temp_path,
            original_filename=file.filename,
            provider=provider,
            model=model,
            page_numbers=selected_pages,
            max_pages=max_pages,
            dpi=dpi,
            keep_images=keep_images,
        )
    except HTTPException:
        raise
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multimodal analysis failed: {exc}") from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.post("/compare")
async def multimodal_compare(
    file: UploadFile = File(...),
    provider: str = Query("auto", pattern="^(auto|openai|fixture)$"),
    max_pages: int = Query(5, ge=1, le=50),
) -> dict[str, Any]:
    """Return a compact text-only versus multimodal comparison."""

    suffix = _save_upload(file)
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded PDF is empty.")
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        result = analyze_pdf(
            temp_path,
            original_filename=file.filename,
            provider=provider,
            max_pages=max_pages,
        )
        return {
            "filename": result["filename"],
            "provider": result["provider"],
            "model": result["model"],
            "summary": result["summary"],
            "pages": [
                {
                    "page_number": page["page_number"],
                    "text_only": page["text_only"],
                    "multimodal_confidence": page["multimodal"]["overall_confidence"],
                    "comparison": page["comparison"],
                    "visual_only_findings": page["multimodal"]["visual_only_findings"],
                }
                for page in result["pages"]
            ],
        }
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


@router.get("/accuracy-report")
def multimodal_accuracy_report() -> dict[str, Any]:
    """Return the saved Week 23 benchmark report."""

    if not ACCURACY_REPORT_PATH.exists():
        raise HTTPException(status_code=404, detail="Accuracy report has not been generated yet.")
    return json.loads(ACCURACY_REPORT_PATH.read_text(encoding="utf-8"))


@router.get("/test-documents")
def multimodal_test_documents() -> dict[str, Any]:
    """List the bundled minimum 20 benchmark PDF pages."""

    documents = sorted(path.name for path in TEST_DOCUMENTS_DIR.glob("*.pdf"))
    return {
        "count": len(documents),
        "minimum_required": 20,
        "documents": documents,
        "note": "Synthetic image-only and hybrid PDF pages for repeatable testing.",
    }
