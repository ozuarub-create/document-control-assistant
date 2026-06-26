# Week 18 Technical Documentation

## Purpose

This project is a complete AI-powered document control assistant for construction project documents. It supports the full document lifecycle from upload to classification, registration, review, workflow routing, search, analytics, and reporting.

## Core Capabilities

### 1. Document Ingestion

The system accepts PDF and DOCX files through FastAPI upload endpoints. Uploaded files are processed locally and temporary files are removed after processing.

### 2. Classification and Metadata Extraction

Documents are classified into the following types:

- Drawing
- Specification
- Method Statement
- Material Submittal
- Shop Drawing
- Inspection Report
- Contract
- Meeting Minutes
- RFI

The system extracts:

- Document Title
- Revision Number
- Project Name
- Contractor
- Consultant
- Submission Date
- Discipline

### 3. Document Register

All processed documents are stored in the SQLite register. The register tracks metadata, classification confidence, extracted text, local embeddings, and version information.

### 4. Version Tracking

Documents with the same project and title are treated as versions of the same document. The latest version is marked using `is_latest`.

### 5. Search

The platform supports:

- Traditional metadata search
- Semantic search using local embeddings
- Natural language document queries

### 6. Review and Validation

The review engine checks:

- Missing metadata
- Document-type-specific validation rules
- Duplicate or similar submissions
- Classification confidence
- Readable text quality

It generates:

- Review status
- Quality score
- AI-style summary
- Warnings
- Recommendations
- Full review report

### 7. Workflow States

Documents move through lifecycle states:

- registered
- under_review
- needs_revision
- approved
- rejected
- archived

Workflow history is stored in `workflow_history`.

### 8. Analytics and Reporting

The analytics module reports:

- Total documents
- Latest documents
- Older versions
- Document counts by type
- Document counts by discipline
- Workflow state counts
- Review status counts
- Average confidence score
- Average review quality score
- Duplicate review count

## API Endpoints

### Main

- `GET /`
- `GET /health`
- `GET /dashboard`

### Upload and Review

- `POST /upload`
- `POST /documents/review-upload`

### Document Register

- `POST /documents/rebuild-sample-register`
- `GET /documents`
- `GET /documents/{document_id}`
- `GET /documents/{document_id}/versions`

### Search

- `GET /documents/search`
- `POST /documents/semantic-search`
- `POST /documents/query`

### Review Reports

- `GET /documents/reviews`
- `GET /documents/{document_id}/review`

### Workflow

- `GET /documents/workflow`
- `GET /documents/{document_id}/workflow`
- `POST /documents/{document_id}/workflow`

### Analytics

- `GET /documents/analytics`

## Running the Project

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

Dashboard:

```text
http://127.0.0.1:8000/dashboard
```
