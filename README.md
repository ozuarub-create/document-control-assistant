# Week 18 – AI Document Control Assistant Platform

## Overview

This project is a complete AI-powered Document Control Assistant for construction projects. It manages documents throughout their lifecycle by integrating document classification, metadata extraction, document registration, search, review, validation, analytics, and reporting into a single platform.

## Features

* PDF and DOCX document upload
* Automatic document classification
* Metadata extraction
* Document register
* Version tracking
* Traditional metadata search
* Semantic search
* Natural language document queries
* Document validation
* Missing information detection
* Duplicate submission detection
* AI-generated document summaries
* Warnings and recommendations
* Review report generation
* Document workflow management
* Analytics and reporting dashboard

## Document Workflow

Documents move through the following workflow:

1. Upload
2. Classification
3. Metadata Extraction
4. Validation
5. Review
6. Approval
7. Archive

## API Endpoints

### Document Management

* POST `/upload`
* GET `/documents`
* GET `/documents/{document_id}`

### Search

* GET `/documents/search`
* POST `/documents/semantic-search`
* POST `/documents/query`

### Review & Validation

* POST `/documents/review-upload`
* GET `/documents/reviews`
* GET `/documents/{document_id}/review`

### Workflow

* GET `/documents/{document_id}/versions`

## Project Structure

```text
app/
docs/
tests/

demo.py
demo_week18.py

README.md
requirements.txt
```

## Demonstration

The project demonstrates:

* Complete document lifecycle
* AI document classification
* Intelligent document search
* Document review and validation
* Workflow management
* Analytics and reporting

## Testing

Run:

```bash
pytest
```

Expected result:

```text
All tests passed
```

## Run the Application

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Deliverables

* Fully integrated AI Document Control Assistant
* Web interface / dashboard
* Document workflow management
* Architecture documentation
* Analytics and reporting
* Technical documentation
* Demo presentation

## Author

Omar Zuarub

United Arab Emirates University
