# Retrieval and Citation Rules – Week 21

## Retrieval Quality

The assistant combines five signals:

1. Exact document number and metadata matches.
2. Sparse semantic embedding similarity.
3. Keyword and phrase overlap.
4. Week 20 relationship-graph expansion.
5. Recent conversation context for follow-up questions.

## Answer Rules

- Factual statements must include an inline marker such as `[S1]`.
- Every marker must map to one structured citation object.
- Multi-document answers may cite multiple documents.
- Follow-up questions reuse recent cited document IDs only as a retrieval boost, not as unsupported evidence.
- No answer is produced when the evidence score is below the minimum threshold.

## Safety Against Unsupported Answers

The assistant uses extractive source snippets and stored metadata. When the documents do not support the requested information, it returns an insufficient-information response instead of guessing.
