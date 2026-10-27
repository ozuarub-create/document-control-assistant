from __future__ import annotations
from typing import Dict, List


def build_plan(request: str) -> List[Dict[str, str]]:
    return [
        {"step": "scope", "reason": "Understand management question and project scope"},
        {"step": "search", "reason": "Find open risks, RFIs, actions, submittals and contractual issues"},
        {"step": "relationships", "reason": "Follow references between documents"},
        {"step": "conflicts", "reason": "Detect inconsistent project information"},
        {"step": "evidence", "reason": "Collect source-backed evidence"},
        {"step": "sufficiency", "reason": "Check whether evidence supports each finding"},
        {"step": "report", "reason": "Create management report with fact/inference/recommendation separation"},
    ]
