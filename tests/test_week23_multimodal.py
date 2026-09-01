from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.multimodal_engine import analyze_pdf
from app.multimodal_standalone import app
from app.pdf_visualizer import extract_text_only_fields, render_pdf_pages
from app.vision_provider import get_vision_provider


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "multimodal_test_documents"


def test_dataset_contains_at_least_20_pdf_pages() -> None:
    assert len(list(DATASET.glob("*.pdf"))) >= 20


def test_pdf_page_is_rendered_to_png(tmp_path: Path) -> None:
    pdf_path = DATASET / "sample_01_drawing.pdf"
    pages = render_pdf_pages(pdf_path, tmp_path, max_pages=1, dpi=100)
    assert len(pages) == 1
    assert Path(pages[0]["image_path"]).exists()
    assert pages[0]["page_number"] == 1
    assert pages[0]["width"] > 500


def test_text_only_baseline_misses_image_only_title_block(tmp_path: Path) -> None:
    pdf_path = DATASET / "sample_01_drawing.pdf"
    page = render_pdf_pages(pdf_path, tmp_path, max_pages=1)[0]
    baseline = extract_text_only_fields(page["text"])
    assert baseline["characters_extracted"] == 0
    assert baseline["fields_found"] == 0


def test_fixture_multimodal_result_has_structured_evidence() -> None:
    pdf_path = DATASET / "sample_01_drawing.pdf"
    result = analyze_pdf(pdf_path, provider="fixture", max_pages=1)
    page = result["pages"][0]
    assert page["page_number"] == 1
    assert page["multimodal"]["title_block"]["document_number"] == "W23-DRA-001"
    assert page["multimodal"]["stamps"][0]["text"] == "APPROVED"
    assert page["multimodal"]["overall_confidence"] >= 0.9
    assert page["multimodal"]["title_block"]["evidence"]
    assert page["comparison"]["multimodal_added_value"] is True
    assert "stamps" in page["comparison"]["visual_only_field_names"]


def test_hybrid_page_compares_text_and_visual_information() -> None:
    pdf_path = DATASET / "sample_11_drawing.pdf"
    result = analyze_pdf(pdf_path, provider="fixture", max_pages=1)
    page = result["pages"][0]
    assert page["text_only"]["characters_extracted"] > 0
    assert page["text_only"]["fields_found"] >= 1
    assert page["comparison"]["multimodal_fields_found"] > page["comparison"]["text_only_fields_found"]
    assert page["comparison"]["visual_only_count"] >= 3


def test_week23_api_routes_are_registered() -> None:
    paths = {route.path for route in app.routes}
    assert "/multimodal/analyze" in paths
    assert "/multimodal/compare" in paths
    assert "/multimodal/capabilities" in paths
    assert "/multimodal/accuracy-report" in paths
    assert "/multimodal/test-documents" in paths


def test_openai_provider_requires_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        get_vision_provider("openai")
