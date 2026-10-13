import json
from pathlib import Path

DEFAULT_RULES = {
    "high_confidence": 0.90,
    "medium_confidence": 0.70,
    "high_risk_levels": ["high", "critical"],
}

def load_rules(path: str = "config/approval_rules.json"):
    p = Path(path)
    if p.exists():
        return json.loads(p.read_text())
    return DEFAULT_RULES.copy()

def review_requirement(confidence: float, risk_level: str, rules=None):
    rules = rules or DEFAULT_RULES
    if risk_level.lower() in {x.lower() for x in rules["high_risk_levels"]}:
        return "mandatory_review"
    if confidence >= rules["high_confidence"]:
        return "automatic"
    if confidence >= rules["medium_confidence"]:
        return "human_review"
    return "mandatory_review"
