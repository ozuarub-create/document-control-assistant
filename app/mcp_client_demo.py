from __future__ import annotations
from .mcp_server import server

API_KEY = "week27-demo-key"

def run_client_request(user_request: str) -> dict:
    text = user_request.lower()
    if "compare" in text and "rev" in text:
        return server.call_tool("compare_document_revisions", {"doc_id_a": "drawing_a_rev01", "doc_id_b": "drawing_a_rev02"}, API_KEY)
    if "summary" in text or "summarize" in text:
        return server.call_tool("generate_document_summary", {"doc_id": "drawing_a_rev02"}, API_KEY)
    if "validate" in text:
        return server.call_tool("validate_document", {"doc_id": "drawing_a_rev02"}, API_KEY)
    return server.call_tool("search_documents", {"query": user_request}, API_KEY)
