# Week 25 – AI Evaluation and Benchmarking

## Goal
Build a standalone evaluation framework that measures AI quality rather than assuming it.

## Capabilities
- Benchmark dataset with realistic construction-document scenarios
- Retrieval accuracy
- Answer correctness
- Citation accuracy
- Hallucination rate
- Metadata extraction accuracy
- Classification accuracy
- Response latency
- Token usage and estimated cost
- Comparison of at least two configurations
- Historical result storage
- Generated comparison report
- FastAPI evaluation endpoints

## Run
```bash
python demo_week25.py
pytest
```

## API
```bash
python -m uvicorn app.evaluation_api:app --reload
```
Open `http://127.0.0.1:8000/docs`.

## Deliverables
- Automated evaluation framework
- Benchmark dataset
- Model/prompt comparison capability
- Evaluation report
- Historical results
- Metrics and methodology documentation

## Author
Omar Zuarub
