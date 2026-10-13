# Week 28 API Guide

Run:

```bash
uvicorn app.approval_api:app --reload
```

Endpoints:
- `GET /health`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `GET /approvals/pending`
- `POST /approvals/review`

Review decisions: `approve`, `reject`, `modify`.
For `modify`, send `modified_action`.
