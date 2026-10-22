# Week 29 - AI Application Security Layer

Standalone security layer protecting AI/document workflows against unauthorized access, prompt injection, unsafe tool execution, sensitive-data leakage, and malicious inputs.

## Features

- RBAC permissions
- Document-level access control
- Tool-level permissions
- Input validation
- Output validation/redaction
- Prompt-injection detection and mitigation
- Audit logging
- 25 adversarial attack fixtures
- Before/after security benchmark
- FastAPI endpoint

## Run

```bash
python -m pip install -r requirements_week29.txt
python demo_week29.py
pytest
```

## API

Run:

```bash
uvicorn app.security_api:app --reload
```

Open `/docs` for Swagger API documentation.
