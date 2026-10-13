from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class ReviewDecision(str, Enum):
    approve = "approve"
    reject = "reject"
    modify = "modify"

class WorkflowState(str, Enum):
    auto_executed = "auto_executed"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    modified = "modified"
    executed = "executed"

class TaskRequest(BaseModel):
    task_id: str = Field(min_length=1)
    document_id: str = Field(min_length=1)
    document_type: str = Field(min_length=1)
    revision: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    proposed_action: str = Field(min_length=1)
    risk_level: str = Field(default="low")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReviewRequest(BaseModel):
    task_id: str
    decision: ReviewDecision
    reviewer: str = Field(min_length=1)
    modified_action: Optional[str] = None
    comment: Optional[str] = None
