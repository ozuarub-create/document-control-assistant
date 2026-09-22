# Week 26 – Centralized AI Gateway

## Goal
Build a standalone AI Gateway that gives applications one standardized interface for multiple AI models/providers.

## Features
- Unified AI request API
- Config-driven multi-model/provider support
- Task-based routing
- API-key authentication
- Rate limiting
- Request and usage logging
- Token and cost tracking
- Error handling
- Retry/fallback logic
- Quality/cost/latency-aware routing compatible with Week 25 evaluation results
- FastAPI documentation
- Docker deployment

## Demo
```bash
python demo_week26.py
```

## Test
```bash
pytest
```

## API
```bash
uvicorn app.gateway_api:app --reload
```
Open `http://127.0.0.1:8000/docs`.
