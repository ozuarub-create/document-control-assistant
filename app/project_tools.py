from __future__ import annotations
from typing import Any, Dict, List


def search_documents(documents: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = query.lower()
    scored = []
    for doc in documents:
        hay = " ".join(str(doc.get(k, "")) for k in ["title","type","content","status","references"]).lower()
        score = sum(1 for token in q.split() if token in hay)
        if score:
            scored.append((score, doc))
    return [d for _, d in sorted(scored, key=lambda x: x[0], reverse=True)]


def get_document(documents: List[Dict[str, Any]], doc_id: str) -> Dict[str, Any] | None:
    return next((d for d in documents if d.get("id") == doc_id), None)


def related_documents(documents: List[Dict[str, Any]], doc_id: str) -> List[Dict[str, Any]]:
    target = get_document(documents, doc_id)
    if not target:
        return []
    refs = set(target.get("references", []))
    out = []
    for doc in documents:
        if doc.get("id") in refs or doc_id in set(doc.get("references", [])):
            out.append(doc)
    return out


def unresolved_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    unresolved = {"open", "pending", "overdue", "rejected", "unresolved"}
    return [d for d in documents if str(d.get("status", "")).lower() in unresolved]


def overdue_actions(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for doc in documents:
        for action in doc.get("actions", []):
            if str(action.get("status", "")).lower() == "overdue":
                out.append({"document_id": doc.get("id"), **action})
    return out
