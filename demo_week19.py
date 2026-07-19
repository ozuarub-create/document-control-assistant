"""Week 19 demonstration - AI Document Compliance Checker.

The demo checks several document types, generates JSON and PDF reports, and
shows compliance scores with detailed findings.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from app.compliance_engine import check_document_compliance
from app.compliance_pdf import write_json_report, write_pdf_report
from app.compliance_repository import save_compliance_report
from app.document_processor import process_file
from app.repository import ingest_folder, save_processed_document

ROOT = Path(__file__).resolve().parent
SAMPLE_DIR = ROOT / "sample_documents"
REPORT_DIR = ROOT / "compliance_reports"


def _find_sample(patterns: list[str]) -> Path:
    for pattern in patterns:
        matches = sorted(SAMPLE_DIR.glob(pattern))
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No sample document found for patterns: {patterns}")


def _print_report(report: dict) -> None:
    failed = [item for item in report["findings"] if not item["passed"]]
    print(f"File: {report['filename']}")
    print(f"Type: {report['document_type']}")
    print(f"Compliance Status: {report['compliance_status']}")
    print(f"Compliance Score: {report['compliance_score']}")
    print(f"Rules Checked: {report['summary']['total_rules_checked']}")
    print(f"Failed Findings: {report['summary']['failed_rules']}")
    print("Top Findings:")
    for finding in failed[:5]:
        print(f"- {finding['severity'].upper()}: {finding['message']}")
    if not failed:
        print("- No failed findings.")
    print("Recommendations:")
    for recommendation in report.get("recommendations", [])[:5]:
        print(f"- {recommendation}")
    if not report.get("recommendations"):
        print("- No recommendations.")
    print()


def main() -> None:
    print("Week 19 - AI Document Compliance Checker")
    print("=" * 72)

    REPORT_DIR.mkdir(exist_ok=True)

    # Load sample register so the platform has metadata available.
    if SAMPLE_DIR.exists():
        loaded = ingest_folder(SAMPLE_DIR, reset=True)
        print(f"Sample register loaded: {len(loaded)} documents")
    else:
        print("Sample register folder not found; continuing with direct file checks.")

    sample_files = [
        _find_sample(["sample_001_drawing.pdf", "*drawing*.pdf", "*drawing*.docx"]),
        _find_sample(["sample_013_method_statement.pdf", "*method_statement*.pdf", "*method_statement*.docx"]),
        _find_sample(["sample_047_rfi.pdf", "*rfi*.pdf", "*rfi*.docx"]),
    ]

    reports: list[dict] = []
    output_paths: list[dict[str, str]] = []

    for index, path in enumerate(sample_files, start=1):
        print("-" * 72)
        print(f"Compliance Report {index}")
        print("-" * 72)
        processed = process_file(path, include_text=True)
        report = check_document_compliance(processed)
        saved_document = save_processed_document(processed, file_path=path)

        json_path = REPORT_DIR / f"week19_compliance_{index}_{path.stem}.json"
        pdf_path = REPORT_DIR / f"week19_compliance_{index}_{path.stem}.pdf"
        write_json_report(report, json_path)
        write_pdf_report(report, pdf_path)
        saved_report = save_compliance_report(
            report,
            document_id=saved_document["id"],
            document_key=saved_document["document_key"],
            json_report_path=json_path,
            pdf_report_path=pdf_path,
        )
        report["stored_compliance_id"] = saved_report["id"]

        _print_report(report)
        reports.append(report)
        output_paths.append({"json": str(json_path), "pdf": str(pdf_path)})

    summary = {
        "reports_generated": len(reports),
        "average_compliance_score": round(mean(report["compliance_score"] for report in reports), 2),
        "statuses": {status: sum(1 for report in reports if report["compliance_status"] == status) for status in sorted({report["compliance_status"] for report in reports})},
        "json_and_pdf_reports": output_paths,
    }

    results = {
        "summary": summary,
        "reports": reports,
    }
    results_path = ROOT / "demo_week19_results.json"
    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 72)
    print("Week 19 Demo Complete")
    print("=" * 72)
    print(f"Compliance checking engine: working")
    print(f"JSON reports generated: {len(output_paths)}")
    print(f"PDF reports generated: {len(output_paths)}")
    print(f"Average compliance score: {summary['average_compliance_score']}")
    print(f"Results saved to: {results_path.name}")
    print(f"Report folder: {REPORT_DIR}")


if __name__ == "__main__":
    main()
