"""Multimodal PDF analysis orchestration for Week 23."""

from __future__ import annotations

import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.pdf_visualizer import extract_text_only_fields, render_pdf_pages
from app.vision_provider import VisionProvider, get_vision_provider


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = ROOT_DIR / "multimodal_outputs"


EMPTY_TITLE_BLOCK = {
    "document_title": None,
    "document_type": None,
    "document_number": None,
    "revision": None,
    "project_name": None,
    "discipline": None,
    "date": None,
    "status": None,
    "confidence": 0.0,
    "evidence": "",
}


def _bounded_confidence(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 3)
    except (TypeError, ValueError):
        return 0.0


def _normalize_item(item: Any, defaults: dict[str, Any]) -> dict[str, Any]:
    result = dict(defaults)
    if isinstance(item, dict):
        result.update(item)
    if "confidence" in result:
        result["confidence"] = _bounded_confidence(result.get("confidence"))
    return result


def normalize_visual_result(value: dict[str, Any]) -> dict[str, Any]:
    """Normalize model output into the Week 23 structured schema."""

    result = dict(value or {})
    title_block = _normalize_item(result.get("title_block"), EMPTY_TITLE_BLOCK)
    tables = [
        _normalize_item(
            item,
            {"name": "", "headers": [], "rows": [], "confidence": 0.0, "evidence": ""},
        )
        for item in result.get("tables", [])
        if isinstance(item, dict)
    ]
    notes = [
        _normalize_item(item, {"text": "", "confidence": 0.0, "evidence": ""})
        for item in result.get("drawing_notes", [])
        if isinstance(item, dict)
    ]
    stamps = [
        _normalize_item(
            item,
            {"text": "", "status": "", "confidence": 0.0, "evidence": ""},
        )
        for item in result.get("stamps", [])
        if isinstance(item, dict)
    ]
    revisions = [
        _normalize_item(
            item,
            {"revision": "", "date": "", "description": "", "confidence": 0.0, "evidence": ""},
        )
        for item in result.get("revision_information", [])
        if isinstance(item, dict)
    ]
    symbols = [
        _normalize_item(
            item,
            {"symbol": "", "meaning": "", "confidence": 0.0, "evidence": ""},
        )
        for item in result.get("symbols_and_annotations", [])
        if isinstance(item, dict)
    ]
    visual_only = [
        _normalize_item(
            item,
            {
                "field": "",
                "value": "",
                "reason_text_extraction_misses_it": "",
                "confidence": 0.0,
                "evidence": "",
            },
        )
        for item in result.get("visual_only_findings", [])
        if isinstance(item, dict)
    ]
    return {
        "page_summary": str(result.get("page_summary") or ""),
        "title_block": title_block,
        "tables": tables,
        "drawing_notes": notes,
        "stamps": stamps,
        "revision_information": revisions,
        "symbols_and_annotations": symbols,
        "visual_only_findings": visual_only,
        "overall_confidence": _bounded_confidence(result.get("overall_confidence")),
        "provider_note": str(result.get("provider_note") or ""),
    }


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _visual_field_map(visual: dict[str, Any]) -> dict[str, Any]:
    title_block = visual.get("title_block", {})
    fields = {
        "document_title": title_block.get("document_title"),
        "document_type": title_block.get("document_type"),
        "document_number": title_block.get("document_number"),
        "revision": title_block.get("revision"),
        "project_name": title_block.get("project_name"),
        "discipline": title_block.get("discipline"),
        "date": title_block.get("date"),
        "status": title_block.get("status"),
        "tables": visual.get("tables", []),
        "drawing_notes": visual.get("drawing_notes", []),
        "stamps": visual.get("stamps", []),
        "revision_information": visual.get("revision_information", []),
        "symbols_and_annotations": visual.get("symbols_and_annotations", []),
    }
    return fields


def compare_text_and_visual(text_only: dict[str, Any], visual: dict[str, Any]) -> dict[str, Any]:
    text_fields = text_only.get("fields", {})
    visual_fields = _visual_field_map(visual)
    comparable_names = [
        "document_title",
        "document_type",
        "document_number",
        "revision",
        "project_name",
        "date",
    ]
    text_found = [name for name in comparable_names if _has_value(text_fields.get(name))]
    visual_found = [name for name, value in visual_fields.items() if _has_value(value)]
    visual_only = [
        name
        for name, value in visual_fields.items()
        if _has_value(value) and (name not in comparable_names or not _has_value(text_fields.get(name)))
    ]

    disagreements: list[dict[str, Any]] = []
    for name in comparable_names:
        text_value = text_fields.get(name)
        visual_value = visual_fields.get(name)
        if _has_value(text_value) and _has_value(visual_value):
            if str(text_value).strip().lower() != str(visual_value).strip().lower():
                disagreements.append(
                    {"field": name, "text_only": text_value, "multimodal": visual_value}
                )

    return {
        "text_only_fields_found": len(text_found),
        "multimodal_fields_found": len(visual_found),
        "text_only_field_names": text_found,
        "multimodal_field_names": visual_found,
        "visual_only_field_names": visual_only,
        "visual_only_count": len(visual_only),
        "disagreements": disagreements,
        "multimodal_added_value": bool(visual_only),
        "explanation": (
            "Multimodal analysis found information in page imagery, layout, stamps, tables, or annotations "
            "that was absent from the PDF text layer."
            if visual_only
            else "The PDF text layer and visual analysis found similar information on this page."
        ),
    }


def analyze_pdf(
    pdf_path: str | Path,
    *,
    original_filename: str | None = None,
    provider: str = "auto",
    model: str | None = None,
    page_numbers: Iterable[int] | None = None,
    max_pages: int = 5,
    dpi: int = 150,
    keep_images: bool = False,
    output_dir: str | Path | None = None,
    vision_provider: VisionProvider | None = None,
) -> dict[str, Any]:
    """Render and analyze a PDF page-by-page using text and vision."""

    source = Path(pdf_path)
    if source.suffix.lower() != ".pdf":
        raise ValueError("Week 23 multimodal analysis accepts PDF files only.")
    if not source.exists():
        raise FileNotFoundError(source)

    temporary_directory: tempfile.TemporaryDirectory[str] | None = None
    if keep_images:
        base = Path(output_dir or DEFAULT_OUTPUT_DIR)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        render_dir = base / f"{source.stem}_{timestamp}"
        render_dir.mkdir(parents=True, exist_ok=True)
    else:
        temporary_directory = tempfile.TemporaryDirectory(prefix="week23_pages_")
        render_dir = Path(temporary_directory.name)

    selected_provider = vision_provider or get_vision_provider(provider, pdf_path=source, model=model)
    try:
        rendered_pages = render_pdf_pages(
            source,
            render_dir,
            page_numbers=page_numbers,
            max_pages=max_pages,
            dpi=dpi,
        )
        page_results: list[dict[str, Any]] = []
        for page in rendered_pages:
            text_only = extract_text_only_fields(page["text"])
            raw_visual = selected_provider.analyze_page(
                page["image_path"],
                pdf_path=source,
                page_number=page["page_number"],
                text_context=page["text"],
            )
            visual = normalize_visual_result(raw_visual)
            comparison = compare_text_and_visual(text_only, visual)
            page_results.append(
                {
                    "page_number": page["page_number"],
                    "rendered_image": {
                        "path": page["image_path"] if keep_images else None,
                        "width": page["width"],
                        "height": page["height"],
                        "dpi": page["dpi"],
                    },
                    "text_only": text_only,
                    "multimodal": visual,
                    "comparison": comparison,
                    "evidence": {
                        "text_layer_preview": text_only["raw_text_preview"],
                        "visual_evidence_count": (
                            len(visual["tables"])
                            + len(visual["drawing_notes"])
                            + len(visual["stamps"])
                            + len(visual["revision_information"])
                            + len(visual["symbols_and_annotations"])
                        ),
                    },
                }
            )

        visual_advantage_pages = [
            item["page_number"]
            for item in page_results
            if item["comparison"]["multimodal_added_value"]
        ]
        average_confidence = (
            sum(item["multimodal"]["overall_confidence"] for item in page_results) / len(page_results)
            if page_results
            else 0.0
        )
        return {
            "filename": original_filename or source.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "provider": selected_provider.name,
            "model": selected_provider.model_name,
            "pages_analyzed": len(page_results),
            "page_numbers": [item["page_number"] for item in page_results],
            "pages": page_results,
            "summary": {
                "average_multimodal_confidence": round(average_confidence, 3),
                "pages_where_visual_understanding_added_information": visual_advantage_pages,
                "visual_advantage_page_count": len(visual_advantage_pages),
                "total_visual_only_fields": sum(
                    item["comparison"]["visual_only_count"] for item in page_results
                ),
                "text_only_total_fields": sum(
                    item["comparison"]["text_only_fields_found"] for item in page_results
                ),
                "multimodal_total_fields": sum(
                    item["comparison"]["multimodal_fields_found"] for item in page_results
                ),
            },
        }
    finally:
        if temporary_directory is not None:
            temporary_directory.cleanup()


def write_analysis_json(result: dict[str, Any], output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return destination


def clear_multimodal_outputs(output_dir: str | Path | None = None) -> None:
    target = Path(output_dir or DEFAULT_OUTPUT_DIR)
    if target.exists():
        shutil.rmtree(target)
