# MCP Client Guide

Use `app.mcp_server.server` as the standalone tool server abstraction.

Demo API key: `week27-demo-key` (override with `MCP_API_KEY` in real deployment).

Example tool call:

```python
from app.mcp_server import server
result = server.call_tool(
    "compare_document_revisions",
    {"doc_id_a": "drawing_a_rev01", "doc_id_b": "drawing_a_rev02"},
    "week27-demo-key",
)
```

For a production MCP SDK integration, map `server.list_tools()` to the client's tool discovery call and `server.call_tool()` to tool execution.
