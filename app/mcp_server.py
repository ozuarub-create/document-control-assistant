from __future__ import annotations
from typing import Any
from .mcp_auth import validate_api_key, AccessDenied
from .mcp_logging import log_tool_call
from .mcp_tools import TOOLS

TOOL_SCHEMAS = {
    "search_documents": {"description": "Search documents by text query", "required": ["query"]},
    "get_document_metadata": {"description": "Retrieve metadata for a document", "required": ["doc_id"]},
    "get_document_content": {"description": "Retrieve document content", "required": ["doc_id"]},
    "search_knowledge_base": {"description": "Search the existing knowledge base", "required": ["query"]},
    "compare_document_revisions": {"description": "Compare two document revisions", "required": ["doc_id_a", "doc_id_b"]},
    "get_related_documents": {"description": "Retrieve related documents", "required": ["doc_id"]},
    "validate_document": {"description": "Run document validation", "required": ["doc_id"]},
    "generate_document_summary": {"description": "Generate a concise document summary", "required": ["doc_id"]},
}

class MCPServer:
    def list_tools(self) -> list[dict]:
        return [{"name": name, **schema} for name, schema in TOOL_SCHEMAS.items()]

    def call_tool(self, name: str, arguments: dict[str, Any], api_key: str | None) -> dict:
        try:
            validate_api_key(api_key)
            if name not in TOOLS:
                raise KeyError(f"Unknown tool '{name}'")
            schema = TOOL_SCHEMAS[name]
            missing = [k for k in schema["required"] if not arguments.get(k)]
            if missing:
                raise ValueError(f"Missing required arguments: {', '.join(missing)}")
            data = TOOLS[name](**arguments)
            log_tool_call(name, arguments, True)
            return {"ok": True, "tool": name, "data": data}
        except AccessDenied as e:
            log_tool_call(name, arguments, False, str(e))
            return {"ok": False, "tool": name, "error": {"type": "access_denied", "message": str(e)}}
        except FileNotFoundError as e:
            log_tool_call(name, arguments, False, str(e))
            return {"ok": False, "tool": name, "error": {"type": "not_found", "message": str(e)}}
        except (ValueError, KeyError, TypeError) as e:
            log_tool_call(name, arguments, False, str(e))
            return {"ok": False, "tool": name, "error": {"type": "invalid_request", "message": str(e)}}
        except Exception as e:
            log_tool_call(name, arguments, False, str(e))
            return {"ok": False, "tool": name, "error": {"type": "internal_error", "message": str(e)}}

server = MCPServer()
