from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader

from app.compliance_engine import check_document_compliance, get_compliance_rules
from app.compliance_pdf import write_json_report, write_pdf_report


def _processed_document(document_type: str = "Drawing") -> dict:
    return {
        "filename": "sample.pdf",
        "file_type": "pdf",
        "classification": {
            "document_type": document_type,
            "confidence_score": 0.96,
        },
        "metadata": {
            "document_title": "Ground Floor Architectural Drawing",
            "revision_number": "R1",
            "project_name": "Campus Innovation Building",
            "contractor": "Gulf Build Contractors",
            "consultant": "Pearl Engineering Consultants",
            "submission_date": "2026-05-01",
            "discipline": "Architectural",
        },
        "content_text": "Document Number: DWG-AR-001 Drawing Number: DWG-AR-001 Revision R1 scale 1:100 layout plan grid elevation section approved by consultant signature prepared by engineer checked by manager.",
        "text_preview": "Document Number: DWG-AR-001 Drawing Number: DWG-AR-001 Revision R1 scale 1:100 layout plan grid elevation section approved by consultant signature prepared by engineer checked by manager.",
    }


def test_compliance_rules_are_configurable() -> None:
    rules = get_compliance_rules()
    assert "Drawing" in rules
    assert "RFI" in rules
    assert "mandatory_sections" in rules["Drawing"]


def test_compliant_document_scores_high() -> None:
    report = check_document_compliance(_processed_document("Drawing"))
    assert report["compliance_status"] == "Compliant"
    assert report["compliance_score"] >= 85
    assert report["structured_review"]["signature_present"] is True
    assert report["structured_review"]["document_number_present"] is True


def test_missing_information_is_detected() -> None:
    processed = _processed_document("RFI")
    processed["metadata"]["revision_number"] = None
    processed["metadata"]["submission_date"] = None
    processed["content_text"] = "RFI clarification question only."
    report = check_document_compliance(processed)
    messages = " ".join(item["message"] for item in report["findings"] if not item["passed"])
    assert "Revision" in messages
    assert "date" in messages.lower() or "Date" in messages
    assert report["compliance_score"] < 85


def test_json_and_pdf_reports_are_created(tmp_path: Path) -> None:
    report = check_document_compliance(_processed_document("Drawing"))
    json_path = write_json_report(report, tmp_path / "report.json")
    pdf_path = write_pdf_report(report, tmp_path / "report.pdf")
    assert json_path.exists()
    assert pdf_path.exists()
    reader = PdfReader(str(pdf_path))
    assert len(reader.pages) >= 1
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    assert "Compliance Validation Report" in text
