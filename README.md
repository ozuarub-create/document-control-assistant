# Week 28 - Human-in-the-Loop AI Approval Workflow

## Goal
Build an enterprise-style approval framework where AI can recommend actions while sensitive or uncertain actions require human review.

## Features
- Task/document intake
- Proposed action and confidence handling
- Configurable confidence thresholds
- Automatic processing for high-confidence low-risk actions
- Human review for medium/low confidence
- Mandatory review for high-risk actions
- Approve / reject / modify decisions
- Approved-action execution
- Complete audit trail
- REST API
- 10+ automated test scenarios

## Demo
```bash
python demo_week28.py
```

## Tests
```bash
pytest
```

## API
```bash
uvicorn app.approval_api:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation.
