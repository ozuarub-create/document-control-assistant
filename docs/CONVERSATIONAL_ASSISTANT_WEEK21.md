# Week 21 – Conversational Document Assistant

## Purpose

The Week 21 module answers questions about registered construction documents while returning structured citations for every supported answer.

## Main Capabilities

- Hybrid retrieval using metadata, exact references, lexical matching, semantic embeddings, document relationships, and conversation context.
- Multi-document questions with multiple cited sources.
- Persistent conversation history stored in SQLite.
- Follow-up question support using the previous questions and previously cited documents.
- Graceful insufficient-information responses without invented facts.

## API

### Ask a question

`POST /conversation/ask`

Example body:

```json
{
  "question": "What documents does RFI-015 reference?",
  "session_id": null,
  "limit": 6,
  "latest_only": true
}
```

The response includes:

- `session_id`
- `answer`
- `status`
- `citations`
- retrieval diagnostics
- whether conversation history was used

### Retrieve conversation history

`GET /conversation/{session_id}`

### List sessions

`GET /conversation/sessions`

### Delete a conversation

`DELETE /conversation/{session_id}`

### View assistant capabilities

`GET /conversation/capabilities`

## Citation Structure

Each citation contains the source document ID, filename, title, type, project, revision, source excerpt, relevance score, and retrieval reason.

## Insufficient Information

When no registered document provides enough evidence, the assistant returns `status: insufficient_information`, an empty citation list, and a clear request for a more specific document number, title, project, discipline, or type. It does not fabricate an answer.
