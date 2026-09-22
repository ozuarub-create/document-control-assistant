# API Guide

Run:

```bash
uvicorn app.gateway_api:app --reload
```

Open `http://127.0.0.1:8000/docs`.

Default demo API key: `demo-key` using the `X-API-Key` header.

Main endpoint: `POST /v1/ai`

Example body:

```json
{"task_type":"reasoning","prompt":"Review this document and recommend next action","max_tokens":512}
```

Usage endpoint: `GET /v1/usage`.
