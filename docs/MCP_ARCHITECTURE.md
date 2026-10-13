# Week 27 MCP Architecture

```text
MCP-compatible AI Client
        |
        v
 Authentication / Access Control
        |
        v
 Standalone MCP Server
        |
        +--> Tool Registry / Schemas
        +--> Input Validation
        +--> Structured Error Handling
        +--> Tool-call Logging
        |
        v
 Document + Knowledge Repositories
```

The client selects only the required tool for the user's task. Business data is stored outside tool code in repository files/configuration.
