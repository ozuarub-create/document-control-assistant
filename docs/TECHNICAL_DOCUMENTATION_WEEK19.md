# Week 19 Technical Documentation

## Purpose

Week 19 adds an AI Document Compliance Checker to the existing AI Document Control Assistant platform.

## Main Modules

- `app/compliance_engine.py` - configurable validation rules and compliance scoring
- `app/compliance_pdf.py` - JSON and PDF validation report generation
- `app/compliance_repository.py` - database storage for compliance reports
- `app/main.py` - API endpoints for compliance checks

## API Endpoints

- `POST /documents/compliance-check`
- `GET /documents/compliance-rules`
- `GET /documents/compliance-reports`
- `GET /documents/{document_id}/compliance`
- `GET /documents/{document_id}/compliance/pdf`

## Demonstration

Run:

```bash
python demo_week19.py
```

The demo checks multiple document types and creates:

- JSON validation reports
- PDF validation reports
- `demo_week19_results.json`

## Testing

Run:

```bash
pytest
```

The Week 19 tests verify:

- Configurable rules
- High score for compliant documents
- Missing information detection
- JSON report generation
- PDF report generation
