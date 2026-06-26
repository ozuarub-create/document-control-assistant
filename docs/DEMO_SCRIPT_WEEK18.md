# Week 18 End-to-End Demo Script

## 1. Start the API

```bash
source .venv/bin/activate
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## 2. Open Dashboard

Open:

```text
http://127.0.0.1:8000/dashboard
```

Show the dashboard cards, workflow state counts, and latest documents table.

## 3. Rebuild Register

In Swagger UI, run:

```text
POST /documents/rebuild-sample-register
```

This loads the 50 sample documents.

## 4. Upload and Review a Document

Run:

```text
POST /documents/review-upload
```

Upload a PDF or DOCX file from `sample_documents/`.

Show:

- Classification result
- Extracted metadata
- Review status
- Quality score
- Warnings
- Recommendations

## 5. Search Documents

Run:

```text
GET /documents/search
```

Example filters:

- document_type = Drawing
- discipline = Architectural

## 6. Semantic Search

Run:

```text
POST /documents/semantic-search
```

Example query:

```text
layout drawings with architectural plans
```

## 7. Natural Language Query

Run:

```text
POST /documents/query
```

Example:

```text
Show me the latest architectural drawings
```

## 8. Workflow

Run:

```text
GET /documents/workflow
GET /documents/{document_id}/workflow
POST /documents/{document_id}/workflow
```

Show lifecycle states such as registered, under_review, approved, and archived.

## 9. Analytics

Run:

```text
GET /documents/analytics
```

Show document totals, workflow states, review quality, and classification counts.

## 10. Command-Line Demo

Run:

```bash
python demo_week18.py
```

Expected result:

```text
Week 18 Demo Complete
Integrated platform: working
Dashboard API: working
Workflow states: working
Analytics/reporting: working
End-to-end demonstration: working
```
