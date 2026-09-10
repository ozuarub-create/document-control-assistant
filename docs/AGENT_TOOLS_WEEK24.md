# Week 24 Agent Tool Catalogue

| Tool | Purpose | Typical trigger |
|---|---|---|
| classify_document | Identify document type | Every run |
| extract_metadata | Extract document number, revision, date, status | Every run |
| search_knowledge_base | Find related project records | Related/reference/search tasks |
| check_completeness | Validate required metadata | Review/approval/workflow tasks |
| detect_previous_revisions | Find prior revisions | Revision/compare/latest tasks |
| generate_summary | Produce concise document overview | Summary/brief tasks |
| generate_review_comments | Generate actionable review findings | Review/comment/approval tasks |
| recommend_next_action | Recommend routing or workflow state | Next-action/workflow/review tasks |

Tools return structured dictionaries and do not make orchestration decisions themselves.
