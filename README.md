# Week 23 - Multimodal Document Intelligence

## Overview

This project is a standalone multimodal document intelligence prototype for construction PDF documents. It renders PDF pages as images, analyzes the visual page content with a vision-capable AI model, compares the result with normal PDF text extraction, and returns structured JSON with confidence, page number, and evidence.

## Features

- Accept PDF uploads
- Convert selected PDF pages to PNG images
- Analyze pages using a vision-capable AI model
- Extract title blocks
- Extract tables
- Extract drawing notes
- Detect approval and review stamps
- Extract revision information
- Detect symbols and visual annotations
- Compare text-only extraction with multimodal extraction
- Identify information missed by the PDF text layer
- Return structured JSON with confidence and evidence
- Include 20 synthetic construction test PDF pages

## Vision Providers

### OpenAI vision provider

The production path uses an OpenAI vision-capable model through the Responses API.

Set these values in `.env`:

```text
OPENAI_API_KEY=your-key-here
OPENAI_VISION_MODEL=gpt-4.1-mini
```

The model name is configurable.

### Offline fixture provider

The repository also includes a deterministic fixture provider for the bundled 20 synthetic test PDFs. This is used for repeatable automated tests and offline demonstration only. It is not a replacement for a real vision model.

## Structured Output

Each analyzed page returns:

- Page number
- Rendered image information
- Text-only extraction result
- Multimodal extraction result
- Title-block fields
- Tables
- Notes
- Stamps
- Revisions
- Symbols and annotations
- Confidence scores
- Evidence descriptions
- Visual-only findings
- Text-only versus multimodal comparison

## API Endpoints

- `POST /multimodal/analyze`
- `POST /multimodal/compare`
- `GET /multimodal/capabilities`
- `GET /multimodal/accuracy-report`
- `GET /multimodal/test-documents`

## Install the Week 23 Update

From the extracted Week 23 package, run:

```bash
python3 install_week23.py ~/Desktop/document-control-assistant
```

Then enter the project:

```bash
cd ~/Desktop/document-control-assistant
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the Standalone Service

```bash
python -m uvicorn app.multimodal_standalone:app --reload --port 8001
```

Open:

```text
http://127.0.0.1:8001/docs
```

## Run Inside the Main Platform

The installer adds the Week 23 router to the main FastAPI application.

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Demonstration

Offline repeatable demonstration using all 20 pages:

```bash
python demo_week23.py --provider fixture --limit 20
```

Real vision-model demonstration:

```bash
python demo_week23.py --provider openai --limit 3
```

The real model command requires `OPENAI_API_KEY`.

## Testing

```bash
pytest
```

The Week 23 test file verifies:

- Minimum 20 PDF pages
- PDF-to-image conversion
- Text-only baseline behavior
- Structured visual extraction
- Confidence and evidence
- Text-versus-multimodal comparison
- API route registration

## Accuracy Report

The included benchmark demonstrates:

- 20 PDF test pages
- Image-only and hybrid PDF pages
- Text-only field recall
- Multimodal field recall
- Visual-category extraction
- Cases where stamps, symbols, revision clouds, and title blocks are missed by text extraction

See:

```text
accuracy_report_week23.json
docs/ACCURACY_AND_LIMITATIONS_WEEK23.md
```

## Important Limitation

The bundled fixture benchmark verifies the pipeline, data structure, and comparison logic. Production vision-model accuracy must be measured separately using real project documents and the configured vision model.

## Deliverables

- Working multimodal PDF processing service
- Structured extraction API
- 20 test PDF pages
- Text-only versus multimodal comparison
- Accuracy report
- Limitations report
- Working demonstration

## Author

Omar Zuarub

United Arab Emirates University
