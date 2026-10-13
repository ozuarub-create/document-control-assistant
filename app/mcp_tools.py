from __future__ import annotations
from difflib import unified_diff
from typing import Any
from .document_repository import DocumentRepository
from .knowledge_repository import KnowledgeRepository

repo = DocumentRepository()
kb = KnowledgeRepository()

def search_documents(query: str) -> dict:
    if not query.strip():
        raise ValueError("query must not be empty")
    return {"query": query, "results": repo.search(query)}

def get_document_metadata(doc_id: str) -> dict:
    d = repo.load(doc_id)
    return {k: d.get(k) for k in ("id","title","type","revision","status","owner","date","tags")}

def get_document_content(doc_id: str) -> dict:
    d = repo.load(doc_id)
    return {"id": doc_id, "content": d.get("content", "")}

def search_knowledge_base(query: str) -> dict:
    if not query.strip():
        raise ValueError("query must not be empty")
    return {"query": query, "matches": kb.search(query)}

def compare_document_revisions(doc_id_a: str, doc_id_b: str) -> dict:
    a, b = repo.load(doc_id_a), repo.load(doc_id_b)
    a_lines = a.get("content", "").splitlines()
    b_lines = b.get("content", "").splitlines()
    diff = list(unified_diff(a_lines, b_lines, fromfile=doc_id_a, tofile=doc_id_b, lineterm=""))
    changed = [x for x in diff if x.startswith("+") or x.startswith("-")]
    return {"left": doc_id_a, "right": doc_id_b, "differences": diff, "change_count": len(changed)}

def get_related_documents(doc_id: str) -> dict:
    return {"doc_id": doc_id, "related": repo.related(doc_id)}

def validate_document(doc_id: str) -> dict:
    d = repo.load(doc_id)
    required = ["id","title","type","revision","status","content"]
    missing = [k for k in required if not d.get(k)]
    issues = []
    if missing:
        issues.append(f"Missing required fields: {', '.join(missing)}")
    if d.get("status") not in {"DRAFT","UNDER REVIEW","APPROVED","REJECTED"}:
        issues.append("Unsupported status")
    if not d.get("revision"):
        issues.append("Revision is required")
    return {"doc_id": doc_id, "valid": not issues, "issues": issues}

def generate_document_summary(doc_id: str) -> dict:
    d = repo.load(doc_id)
    content = d.get("content", "").strip().replace("\n", " ")
    words = content.split()
    summary = " ".join(words[:45]) + ("..." if len(words) > 45 else "")
    return {"doc_id": doc_id, "summary": summary, "word_count": len(words)}

TOOLS = {
    "search_documents": search_documents,
    "get_document_metadata": get_document_metadata,
    "get_document_content": get_document_content,
    "search_knowledge_base": search_knowledge_base,
    "compare_document_revisions": compare_document_revisions,
    "get_related_documents": get_related_documents,
    "validate_document": validate_document,
    "generate_document_summary": generate_document_summary,
}
