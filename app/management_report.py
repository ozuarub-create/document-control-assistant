from __future__ import annotations
from typing import Any, Dict, List


def render_markdown(report: Dict[str, Any]) -> str:
    lines = ["# Project Intelligence Executive Report", "", "## Executive Summary", report["executive_summary"], ""]
    sections = [
        ("Major Risks", "major_risks"),
        ("Outstanding Actions", "outstanding_actions"),
        ("Potential Delays", "potential_delays"),
        ("Contractual / Commercial Issues", "commercial_issues"),
        ("Unresolved RFIs / Submittals", "unresolved_items"),
        ("Conflicting Information", "conflicts"),
        ("Recommended Management Actions", "recommendations"),
    ]
    for title, key in sections:
        lines += [f"## {title}"]
        items = report.get(key, [])
        if not items:
            lines.append("- None identified.")
        else:
            for item in items:
                if isinstance(item, dict):
                    label = item.get("statement") or item.get("title") or str(item)
                    citations = " ".join(item.get("citations", []))
                    kind = item.get("kind", "Fact")
                    lines.append(f"- **{kind}:** {label} {citations}".rstrip())
                else:
                    lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)
