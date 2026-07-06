# Week 19 – AI Document Compliance Checker

## Overview

This project is an AI-powered Document Compliance Checker for construction documents. It automatically reviews uploaded documents against predefined compliance requirements and highlights missing or inconsistent information before submission.

## Features

* Configurable validation rules
* Metadata validation
* Mandatory section checking
* Missing signature detection
* Missing revision detection
* Missing approval detection
* Missing date detection
* Missing document number detection
* Compliance scoring
* Detailed findings
* JSON compliance reports
* PDF compliance reports

## Compliance Checks

The system validates:

* Document metadata
* Document number
* Revision number
* Approval information
* Signature blocks
* Submission date
* Mandatory sections
* Required construction document fields

## Compliance Score

Each document receives:

* Compliance status
* Compliance score
* Validation findings
* Warnings
* Recommendations

## Reports

The system automatically generates:

* JSON validation report
* PDF validation report

Reports are saved in:

```text
compliance_reports/
```

## Demonstration

The demonstration includes multiple construction document types including:

* Drawing
* Method Statement
* RFI

The demo shows:

* Compliance checking
* Validation results
* Missing information detection
* Compliance scoring
* JSON report generation
* PDF report generation

## API

Main endpoints:

* POST `/documents/compliance-check`
* GET `/documents/compliance-report`
* GET `/documents/compliance-history`

## Testing

Run:

```bash
pytest
```

Expected result:

```text
15 passed
```

## Run

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Deliverables

* Compliance checking engine
* Validation report (JSON)
* Validation report (PDF)
* Demonstration using multiple document types

## Author

Omar Zuarub
