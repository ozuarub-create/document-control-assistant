# Week 20 Technical Documentation

## Purpose

The Week 20 module adds document relationships and a lightweight knowledge graph to the AI Document Control Assistant.

## Main Components

### `app/relationship_engine.py`

- Extracts document identifiers such as `RFI-015`, `DWG-A-101`, and `SPEC-03-30-00`.
- Detects exact references in document text.
- Links RFIs to drawings, shop drawings, and specifications.
- Uses project, discipline, and topic similarity when an exact reference is unavailable.
- Extracts action items, owners, due dates, and status from meeting minutes.

### `app/relationship_repository.py`

Stores and retrieves:

- Document-to-document relationships.
- Meeting action items.
- Graph nodes and edges.
- Incoming and outgoing related documents.

### `app/relationship_viewer.py`

Provides:

- A browser-based interactive SVG relationship viewer.
- A standalone SVG writer for the demonstration.

## Database Tables

### `document_relationships`

| Field | Purpose |
|---|---|
| `source_document_id` | Document containing the reference |
| `target_document_id` | Referenced or related document |
| `relationship_type` | Type of link |
| `reference_text` | Text evidence or inference explanation |
| `confidence_score` | Relationship confidence |
| `detected_by` | Exact reference or metadata similarity |

### `document_action_items`

| Field | Purpose |
|---|---|
| `meeting_document_id` | Source meeting minutes |
| `action_text` | Extracted task |
| `owner` | Responsible party |
| `due_date` | Required completion date |
| `status` | Current action status |
| `related_document_id` | Document mentioned in the action |

## API Endpoints

- `POST /relationships/rebuild`
- `GET /relationships`
- `GET /relationships/graph-data`
- `GET /relationships/rules`
- `GET /relationships/viewer`
- `GET /documents/{document_id}/related`
- `GET /documents/{document_id}/action-items`

## Relationship Types

- `rfi_references_drawing`
- `rfi_references_specification`
- `rfi_related_to_drawing`
- `rfi_related_to_specification`
- `meeting_minutes_references_document`
- `meeting_minutes_related_document`
- `references_document`
- `related_document`
- `contains_action_item`
- `action_references_document`

## Run the Demo

```bash
python demo_week20.py
```

## Run the API

```bash
python -m uvicorn app.main:app --reload
```

Open the graph viewer:

```text
http://127.0.0.1:8000/relationships/viewer
```
