"""Standalone Week 24 FastAPI application.

Run with:
    uvicorn app.workflow_agent_standalone:app --reload --port 8024
"""
from fastapi import FastAPI
from app.workflow_agent_api import router

app = FastAPI(
    title="Week 24 Document Workflow Agent",
    version="1.0.0",
    description="Agentic document-control orchestration with selective tool use and auditable execution logs.",
)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "week": 24}
