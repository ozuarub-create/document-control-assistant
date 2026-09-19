from __future__ import annotations
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .evaluation_engine import EvaluationEngine
from .evaluation_models import CONFIGS
from .evaluation_repository import EvaluationRepository

app = FastAPI(title='Week 25 AI Evaluation Framework', version='1.0.0')

class RunRequest(BaseModel):
    configuration: str

@app.get('/evaluation/configurations')
def configurations():
    return list(CONFIGS)

@app.post('/evaluation/run')
def run_eval(req: RunRequest):
    if req.configuration not in CONFIGS:
        raise HTTPException(404, 'Unknown configuration')
    dataset = json.loads(Path('benchmark_data/week25_benchmark.json').read_text())
    result = EvaluationEngine(CONFIGS[req.configuration]).run(dataset)
    EvaluationRepository().append(result)
    return result

@app.get('/evaluation/history')
def history():
    return EvaluationRepository().history()
