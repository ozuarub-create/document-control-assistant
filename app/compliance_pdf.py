"""Small built-in PDF writer for Week 19 compliance reports.

The project avoids adding a new PDF dependency. This writer creates a simple,
valid, text-based PDF report using built-in Python only.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any


def _safe_pdf_text(value: Any) -> str:
    text = str(value)
    text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    # Keep text simple for PDF base fonts.
    return text.encode("latin-1", "replace").decode("latin-1")


def _flatten_report(report: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.append("Week 19 Compliance Validation Report")
    lines.append("=" * 44)
    lines.append(f"Filename: {report.get('filename')}")
    lines.append(f"Document Type: {report.get('document_type')}")
    lines.append(f"Compliance Status: {report.get('compliance_status')}")
    lines.append(f"Compliance Score: {report.get('compliance_score')}")
    lines.append(f"Generated At: {report.get('generated_at')}")
    lines.append("")
    lines.append("Summary")
    lines.append("-" * 20)
    for key, value in (report.get("summary") or {}).items():
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    lines.append("")
    lines.append("Metadata")
    lines.append("-" * 20)
    for key, value in (report.get("metadata") or {}).items():
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    lines.append("")
    lines.append("Failed Findings")
    lines.append("-" * 20)
    failed = [item for item in report.get("findings", []) if not item.get("passed")]
    if not failed:
        lines.append("No failed findings.")
    for item in failed:
        lines.append(f"[{item.get('severity', '').upper()}] {item.get('message')}")
        lines.append(f"Recommendation: {item.get('recommendation')}")
    lines.append("")
    lines.append("Structured Review")
    lines.append("-" * 20)
    for key, value in (report.get("structured_review") or {}).items():
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    return lines


def write_pdf_report(report: dict[str, Any], output_path: str | Path) -> Path:
    """Write a text-based PDF compliance report."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    raw_lines = _flatten_report(report)
    wrapped: list[str] = []
    for line in raw_lines:
        if not line:
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(line, width=92) or [""])

    lines_per_page = 48
    pages = [wrapped[i : i + lines_per_page] for i in range(0, len(wrapped), lines_per_page)] or [[""]]

    objects: list[bytes] = []
    # 1: catalog, 2: pages, then for each page: page object and stream object.
    page_object_numbers: list[int] = []
    stream_object_numbers: list[int] = []

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"")  # placeholder for pages object

    next_obj = 3
    for page in pages:
        page_object_numbers.append(next_obj)
        stream_object_numbers.append(next_obj + 1)
        next_obj += 2

        commands = ["BT", "/F1 10 Tf", "50 760 Td", "14 TL"]
        for line in page:
            commands.append(f"({_safe_pdf_text(line)}) Tj")
            commands.append("T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1", "replace")

        page_obj = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents {stream_object_numbers[-1]} 0 R >>".encode("latin-1")
        stream_obj = b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream"
        objects.append(page_obj)
        objects.append(stream_obj)

    kids = " ".join(f"{num} 0 R" for num in page_object_numbers)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_object_numbers)} >>".encode("latin-1")

    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_start = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode("ascii"))

    output.write_bytes(bytes(pdf))
    return output


def write_json_report(report: dict[str, Any], output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return output
