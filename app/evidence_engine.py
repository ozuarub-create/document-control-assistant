from __future__ import annotations
from typing import Any, Dict, List


def evidence(doc: Dict[str, Any], excerpt: str, page: int = 1, confidence: float = 0.95) -> Dict[str, Any]:
    return {
        "document_id": doc.get("id"),
        "title": doc.get("title"),
        "page": page,
        "excerpt": excerpt,
        "confidence": confidence,
        "citation": f"[{doc.get('id')} p.{page}]",
    }


def cite_many(items: List[Dict[str, Any]]) -> List[str]:
    return [x["citation"] for x in items]
