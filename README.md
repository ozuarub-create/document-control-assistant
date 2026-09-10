# Week 24 - Document Workflow Agent

## Overview

Week 24 adds an agentic document-control orchestration layer. The system does not blindly execute every capability. Instead, a planner inspects the requested task and document context, selects only the tools required, executes them in sequence, records every decision, and returns a recommended workflow outcome.

## Goal

Build a standalone Document Workflow Agent that can analyse an uploaded document, determine what needs to happen next, and execute the appropriate document-control tools.

## Available Agent Tools

1. `classify_document`
2. `extract_metadata`
3. `search_knowledge_base`
4. `check_completeness`
5. `detect_previous_revisions`
6. `generate_summary`
7. `generate_review_comments`
8. `recommend_next_action`

## Agent Orchestration

The planner always establishes document type and metadata, then selectively adds downstream tools according to task intent. A summary-only request does not run review or routing tools. A revision task adds revision detection. A review/approval task adds completeness checks, review comments, and next-action recommendation.

Every run records a structured execution log containing step number, selected tool, decision reason, status, timestamp, and result.

## API

Standalone service:

```bash
uvicorn app.workflow_agent_standalone:app --reload --port 8024
```

Swagger UI:

```text
http://127.0.0.1:8024/docs
```

Endpoints:

- `GET /workflow-agent/capabilities`
- `POST /workflow-agent/run`
- `GET /workflow-agent/history`
- `GET /health`

The main project can also include `app.workflow_agent_api.router` in its existing FastAPI application.

## Planner Modes

- `fixture`: deterministic offline planner used for repeatable testing and demonstration.
- `openai`: optional model-backed planner using `OPENAI_API_KEY`.
- `auto`: uses the model-backed planner when a key is available; otherwise uses the deterministic planner.

## Demonstration

```bash
python demo_week24.py
```

The demo runs 10 realistic project scenarios and proves that different tasks select different tool sequences.

## Testing

```bash
pytest
```

## Deliverables

- Standalone agent orchestration service
- 8 available AI tools/functions
- Agent execution history and logging
- API for submitting documents/tasks
- 10 realistic test scenarios
- Architecture diagram and technical documentation
- Working demonstration

## Author

Omar Zuarub
