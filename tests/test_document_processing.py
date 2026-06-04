from __future__ import annotations

import json
from pathlib import Path

from app.document_processor import process_file

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_documents"


def test_dataset_contains_at_least_50_documents() -> None:
    files = list(SAMPLE_DIR.glob("sample_*.pdf")) + list(SAMPLE_DIR.glob("sample_*.docx"))
    assert len(files) >= 50


def test_sample_documents_classify_correctly() -> None:
    manifest = json.loads((SAMPLE_DIR / "dataset_manifest.json").read_text(encoding="utf-8"))

    for item in manifest:
        file_path = SAMPLE_DIR / item["filename"]
        result = process_file(file_path)

        assert result["classification"]["document_type"] == item["expected_document_type"]
        assert result["classification"]["confidence_score"] >= 0.70
        assert result["metadata"]["document_title"]
        assert result["metadata"]["project_name"]
        assert result["metadata"]["contractor"]
        assert result["metadata"]["consultant"]
        assert result["metadata"]["submission_date"]
        assert result["metadata"]["discipline"]
