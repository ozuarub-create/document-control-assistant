from __future__ import annotations
from typing import Any, Dict, List


def detect_conflicts(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    conflicts = []
    for a in documents:
        for b in documents:
            if a.get("id") >= b.get("id"):
                continue
            if a.get("topic") and a.get("topic") == b.get("topic"):
                va, vb = a.get("position"), b.get("position")
                if va and vb and va != vb:
                    conflicts.append({
                        "topic": a["topic"],
                        "document_a": a["id"],
                        "document_b": b["id"],
                        "position_a": va,
                        "position_b": vb,
                    })
    return conflicts
