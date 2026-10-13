# Week 27 - Model Context Protocol (MCP) Document Server

## Goal

Standalone MCP-style server exposing secure document-management tools to an AI assistant.

## Functional Tools

1. Search documents
2. Retrieve document metadata
3. Retrieve document content
4. Search knowledge base
5. Compare document revisions
6. Retrieve related documents
7. Run document validation
8. Generate document summary

## Technical Features

- Clear tool schemas
- Input validation
- API-key access-control concept
- Structured error handling
- Tool-call logging
- Repository-backed business data
- MCP-compatible client routing demonstration
- 10+ automated scenarios

## Run

```bash
python demo_mcp.py
pytest tests/test_week27_mcp_server.py
```

## Architecture

See `docs/MCP_ARCHITECTURE.md`.

## Client Guide

See `docs/MCP_CLIENT_GUIDE.md`.
