# Week 15 - AI Document Classification & Metadata Extraction

This is a simple **AI Document Control Assistant** for construction documents. It accepts **PDF** and **DOCX** files, classifies the document type, extracts key metadata, and returns a confidence score.

## What is included

- Working document upload API using FastAPI
- Classification engine for:
  - Drawing
  - Specification
  - Method Statement
  - Material Submittal
  - Shop Drawing
  - Inspection Report
  - Contract
  - Meeting Minutes
  - RFI
- Metadata extraction engine for:
  - Document Title
  - Revision Number
  - Project Name
  - Contractor
  - Consultant
  - Submission Date
  - Discipline
- Confidence score for every classification
- 50 sample PDF/DOCX documents in `sample_documents/`
- Demo script and automated tests

## How to run on MacBook using VS Code

### 1. Open the project

Open this folder in Visual Studio Code.

### 2. Create a virtual environment

In the VS Code terminal, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install the required packages

```bash
pip install -r requirements.txt
```

### 4. Run the API

```bash
uvicorn app.main:app --reload
```

Open this link in your browser:

```text
http://127.0.0.1:8000/docs
```

Use the `/upload` endpoint, click **Try it out**, upload any PDF or DOCX from `sample_documents/`, and click **Execute**.

## Run the demo

```bash
python demo.py
```

The demo processes all 50 sample documents and creates `demo_results.json`.

## Run the tests

```bash
pytest
```

## Example API response

```json
{
  "filename": "sample_001_drawing.pdf",
  "file_type": "pdf",
  "classification": {
    "document_type": "Drawing",
    "confidence_score": 0.99,
    "matched_keywords": ["declared type: Drawing", "drawing", "layout", "plan"],
    "scores": {
      "Drawing": 45,
      "Specification": 0,
      "Method Statement": 0,
      "Material Submittal": 0,
      "Shop Drawing": 0,
      "Inspection Report": 0,
      "Contract": 0,
      "Meeting Minutes": 0,
      "RFI": 0
    }
  },
  "metadata": {
    "document_title": "Ground Floor Architectural Drawing",
    "revision_number": "R1",
    "project_name": "UAEU Smart Construction Training Project",
    "contractor": "Al Noor Contracting LLC",
    "consultant": "Future Design Consultants",
    "submission_date": "2026-05-01",
    "discipline": "Architectural"
  }
}
```

## GitHub submission steps

Create a new repository on GitHub, then run these commands inside this project folder:

```bash
git init
git add .
git commit -m "Week 15 document classification assignment"
git branch -M main
git remote add origin https://github.com/ozuarub-create/YOUR-REPOSITORY-NAME.git
git push -u origin main
```

Replace `YOUR-REPOSITORY-NAME` with the repository name you create on GitHub.

## Notes

This project uses a simple keyword-based classification method so it is easy to run locally and submit. It does not require an OpenAI API key or any paid service.
