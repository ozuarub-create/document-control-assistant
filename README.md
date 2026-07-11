# Week 20 – AI Document Relationships & Knowledge Graph

## Overview

This project is an AI-powered Document Relationships & Knowledge Graph system for construction documents. It identifies relationships between project documents and builds a document knowledge graph to help users understand how documents are connected.

## Features

- Automatic document relationship detection
- RFI to Drawing linking
- RFI to Specification linking
- Meeting Minutes to Action Items linking
- Meeting Minutes to referenced documents linking
- Document relationship graph generation
- Knowledge graph visualization
- Related document retrieval API
- Interactive relationship viewer

## Relationship Types

The system detects relationships including:

- RFI → Drawing
- RFI → Specification
- Meeting Minutes → Action Items
- Meeting Minutes → Referenced Documents
- Drawing → Specification
- Cross-document references

## Knowledge Graph

The knowledge graph includes:

- Document nodes
- Relationship edges
- Reference mapping
- Interactive graph viewer
- SVG graph export

## API Endpoints

- GET `/relationships`
- GET `/relationships/{document_id}`
- GET `/relationships/viewer`
- GET `/documents/related/{document_id}`

## Demonstration

The demo includes:

- Document relationship discovery
- RFI reference detection
- Meeting minutes relationship detection
- Knowledge graph creation
- Related document retrieval
- Graph visualization

## Testing

Run:

```bash
pytest
```

Expected output:

```text
19 passed
```

## Run the Application

```bash
python -m uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

Relationship Viewer:

```
http://127.0.0.1:8000/relationships/viewer
```

## Deliverables

- Document relationship engine
- Knowledge graph generation
- Graph visualization
- Relationship viewer
- Related document API
- Demonstration using multiple document types

## Author

Omar Zuarub