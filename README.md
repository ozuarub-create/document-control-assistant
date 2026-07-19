# Week 21 – Conversational Document Assistant with Citations

## Overview

This project adds a conversational assistant to the AI Document Control platform. It answers questions about registered construction documents and always returns structured source citations when the documents support an answer.

## Features

- Improved hybrid retrieval quality
- Multi-document question answering
- Persistent conversation history
- Follow-up question support
- Structured source citations
- Inline citation markers such as `[S1]`
- Graceful insufficient-information handling
- No fabricated answers when evidence is missing

## Conversational API

- `POST /conversation/ask`
- `GET /conversation/capabilities`
- `GET /conversation/sessions`
- `GET /conversation/{session_id}`
- `DELETE /conversation/{session_id}`

## Example Request

```json
{
  "question": "What documents does RFI-015 reference and what are they about?",
  "session_id": null,
  "limit": 6,
  "latest_only": true
}
```

## Citation Support

Every supported answer includes:

- Document ID
- Filename
- Document title and type
- Project and revision
- Relevant source excerpt
- Relevance score
- Retrieval reason

## Demonstration Scenarios

- Multi-document RFI question
- Meeting-minutes action-item question
- Follow-up question using history
- Insufficient-information question

Run:

```bash
python demo_week21.py
```

## Testing

```bash
pytest
```

## Run the API

```bash
python -m uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Deliverables

- Conversational API
- Source citation support
- Realistic project scenario demonstration

## Author

Omar Zuarub

United Arab Emirates University
