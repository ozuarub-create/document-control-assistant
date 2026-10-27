from __future__ import annotations
import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from .project_intelligence_agent import ProjectIntelligenceAgent

app = FastAPI(title="Week 30 Project Intelligence Agent")
DATA = Path(__file__).resolve().parents[1] / "project_dataset" / "simulated_project.json"

class InvestigateRequest(BaseModel):
    request: str = "Analyze this project and identify the major outstanding issues, risks, overdue actions and items requiring management attention."

@app.get("/project-intelligence/health")
def health():
    return {"status": "ok"}

@app.post("/project-intelligence/investigate")
def investigate(payload: InvestigateRequest):
    documents = json.loads(DATA.read_text())
    return ProjectIntelligenceAgent(documents).investigate(payload.request)
