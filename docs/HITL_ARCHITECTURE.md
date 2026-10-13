# Week 28 Human-in-the-Loop Architecture

Flow:

Client -> Approval API -> AI Analysis Result -> Rule Engine -> Auto Execute OR Approval Queue -> Human Reviewer -> Executor -> Audit Log

Rules:
- High confidence: automatic processing.
- Medium confidence: human review.
- Low confidence: mandatory review.
- High/critical risk: mandatory review regardless of confidence.

Components:
- `approval_workflow.py`: orchestration.
- `approval_rules.py`: confidence/risk policy.
- `approval_repository.py`: workflow state storage abstraction.
- `approval_executor.py`: approved action execution abstraction.
- `approval_audit.py`: append-only audit events.
- `approval_api.py`: REST API.
