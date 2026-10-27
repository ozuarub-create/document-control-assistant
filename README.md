# Week 30 - Project Intelligence Agent

## Overview
A standalone AI Project Intelligence Agent that investigates a simulated construction project, follows document relationships, gathers evidence, detects conflicts, and produces an evidence-backed management report.

## Capabilities
- Multi-step investigation planning
- Document search and status analysis
- Relationship traversal between project documents
- Evidence and source citations
- Conflict detection
- Evidence sufficiency checks
- Structured findings
- Fact / Inference / Recommendation separation
- Executive management report
- Complete execution trace
- Evaluation dataset and accuracy-oriented tests

## Simulated Project Dataset
Includes realistic examples of:
- Contract
- Specification
- RFI
- Drawing
- Meeting Minutes
- Material Submittal
- Inspection Report
- Progress Report
- Correspondence
- Shop Drawing

## Executive Report Sections
- Executive summary
- Major risks
- Outstanding actions
- Potential delays
- Contractual / commercial issues
- Unresolved RFIs / submittals
- Conflicting information
- Recommended management actions
- Evidence citations

## Run Demo
```bash
python demo_week30.py
```

## Run Tests
```bash
pytest
```

## Run API
```bash
python -m uvicorn app.project_intelligence_api:app --reload
```
Open:
```text
http://127.0.0.1:8000/docs
```

## Deliverables
- Working Project Intelligence Agent
- Realistic simulated project dataset
- Multi-step orchestration
- Evidence/citation engine
- Complete execution trace
- Evaluation dataset
- Architecture documentation
- Technical documentation
- 15-minute demo guide

## Author
Omar Zuarub
