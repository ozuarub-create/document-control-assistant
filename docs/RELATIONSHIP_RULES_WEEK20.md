# Week 20 Relationship Detection Rules

## Exact Reference Rule

A high-confidence relationship is created when one document contains the registered number, filename, or complete title of another document.

Examples:

- `RFI-015` references `DWG-A-101`.
- `RFI-015` references `SPEC-03-30-00`.
- `MOM-007` references `RFI-015`.

Exact references receive a confidence score of `0.98`.

## RFI Linking Rule

RFIs are linked to drawings, shop drawings, and specifications. When no exact number is found, the engine uses:

- Project name.
- Discipline.
- Topic overlap.

Inferred links are labelled separately and have a lower confidence score.

## Meeting Minutes Rule

Meeting minutes are linked to referenced documents. Lines beginning with `Action Item:`, `Action:`, or `AI:` are extracted as action items.

The engine also extracts:

- Owner or responsible party.
- Due date.
- Status.
- Referenced document number.

## Explainability

Every relationship includes:

- Relationship type.
- Confidence score.
- Detection method.
- Supporting reference text or inference explanation.
