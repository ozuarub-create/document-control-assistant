# AI Document Control Assistant

This repository contains a complete AI-powered document control system for construction project documents. The system supports document upload, classification, metadata extraction, document registration, version tracking, traditional search, semantic search, and natural language document queries.

## Week 15 – Document Classification & Metadata Extraction

### Features

* PDF and DOCX document upload
* Automatic document classification
* Metadata extraction
* Confidence score generation
* Construction document processing

### Supported Document Types

* Drawing
* Specification
* Method Statement
* Material Submittal
* Shop Drawing
* Inspection Report
* Contract
* Meeting Minutes
* RFI

### Extracted Metadata

* Document Title
* Revision Number
* Project Name
* Contractor
* Consultant
* Submission Date
* Discipline

---

## Week 16 – Intelligent Document Register & Search

### Features

* Document database schema
* Metadata repository
* Document version tracking
* Traditional metadata search
* Semantic search using embeddings
* Natural language document queries
* Search API endpoints

### Search Capabilities

#### Traditional Search

Search documents using:

* Document Type
* Project Name
* Contractor
* Consultant
* Discipline
* Revision Number

#### Semantic Search

Find relevant documents using meaning-based search queries.

Example:

```text
layout plans and architectural drawings
```

#### Natural Language Queries

Example:

```text
Show me the latest architectural drawings
```

---

## API Endpoints

### Document Processing

* POST `/upload`

### Document Register

* POST `/documents/rebuild-sample-register`
* GET `/documents`
* GET `/documents/{document_id}`
* GET `/documents/{document_id}/versions`

### Search API

* GET `/documents/search`
* POST `/documents/semantic-search`
* POST `/documents/query`

---

## Project Structure

```text
app/
tests/
sample_documents/

database.py
document_repository.py
search_engine.py
embeddings.py

demo.py
demo_week16.py

document_register.db

README.md
requirements.txt
```

---

## Demonstration Results

### Week 15

* 50 sample documents processed
* Classification successful
* Metadata extraction successful
* Confidence scoring implemented

### Week 16

* Metadata repository created
* Version tracking implemented
* Traditional search implemented
* Semantic search implemented
* Natural language queries implemented

---

## Testing

Run all tests:

```bash
pytest
```

Expected result:

```text
4 passed
```

---

## Run the Application

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

---

## Week 17 – AI Document Review & Validation Assistant

### Features
- Validation rules for common document types
- Missing information detection
- Duplicate submission detection
- AI-generated document summaries
- Warnings and recommendations
- Review report generation

### API Endpoints
- POST /documents/review-upload
- GET /documents/reviews
- GET /documents/{document_id}/review

### Demonstration Results
- Validation engine working
- Duplicate detection working
- AI summary generation working
- Review report generation working
- Automated tests passed
## Author

Omar Zuarub
