# Technical Documentation - Week 30

## Purpose
A standalone Project Intelligence Agent that investigates a simulated construction project and produces an evidence-backed management report.

## Key components
- Investigation planner
- Project search and relationship tools
- Conflict detector
- Evidence/citation engine
- Evidence sufficiency check
- Executive report generator
- Execution trace
- Evaluation dataset

## Safety / quality rule
Every significant fact must contain a source citation. Inferences and recommendations are labelled explicitly and retain the citations that support them.

## Run
```bash
python demo_week30.py
pytest
```

## API
```bash
python -m uvicorn app.project_intelligence_api:app --reload
```
Then open `http://127.0.0.1:8000/docs`.
