from pathlib import Path
from app.mcp_server import server

KEY = "week27-demo-key"

def test_minimum_six_tools():
    assert len(server.list_tools()) >= 6

def test_search_documents():
    r = server.call_tool("search_documents", {"query": "drawing"}, KEY)
    assert r["ok"] and len(r["data"]["results"]) >= 1

def test_metadata():
    r = server.call_tool("get_document_metadata", {"doc_id": "drawing_a_rev02"}, KEY)
    assert r["ok"] and r["data"]["revision"] == "02"

def test_content():
    r = server.call_tool("get_document_content", {"doc_id": "specification_01"}, KEY)
    assert r["ok"] and "Concrete" in r["data"]["content"]

def test_kb_search():
    r = server.call_tool("search_knowledge_base", {"query": "revision approval"}, KEY)
    assert r["ok"] and r["data"]["matches"]

def test_compare_revisions():
    r = server.call_tool("compare_document_revisions", {"doc_id_a": "drawing_a_rev01", "doc_id_b": "drawing_a_rev02"}, KEY)
    assert r["ok"] and r["data"]["change_count"] > 0

def test_related():
    r = server.call_tool("get_related_documents", {"doc_id": "drawing_a_rev02"}, KEY)
    assert r["ok"] and len(r["data"]["related"]) >= 1

def test_validation():
    r = server.call_tool("validate_document", {"doc_id": "drawing_a_rev02"}, KEY)
    assert r["ok"] and r["data"]["valid"] is True

def test_summary():
    r = server.call_tool("generate_document_summary", {"doc_id": "specification_01"}, KEY)
    assert r["ok"] and r["data"]["summary"]

def test_authentication_failure():
    r = server.call_tool("search_documents", {"query": "drawing"}, "bad-key")
    assert not r["ok"] and r["error"]["type"] == "access_denied"

def test_input_validation():
    r = server.call_tool("search_documents", {}, KEY)
    assert not r["ok"] and r["error"]["type"] == "invalid_request"
