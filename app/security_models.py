from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class SecurityRequest:
    user_id: str
    role: str
    action: str
    document_owner: str | None = None
    tool_name: str | None = None
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityDecision:
    allowed: bool
    reasons: List[str]
    risk_score: float
    sanitized_output: str | None = None
