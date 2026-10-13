import pytest
from app.approval_models import TaskRequest
from app.approval_workflow import ApprovalWorkflow
from app.approval_repository import ApprovalRepository

class DummyAudit:
    def __init__(self): self.events=[]
    def log(self, event, task_id, details): self.events.append((event, task_id, details)); return self.events[-1]

def make(conf=0.95, risk="low", task_id="T1"):
    return TaskRequest(task_id=task_id, document_id="D1", document_type="Drawing", revision="03", confidence=conf, proposed_action="register", risk_level=risk)

def wf():
    return ApprovalWorkflow(repository=ApprovalRepository(), audit=DummyAudit())

def test_high_confidence_auto():
    r=wf().submit(make(0.95)); assert r["state"]=="auto_executed"

def test_medium_requires_review():
    r=wf().submit(make(0.80)); assert r["review_requirement"]=="human_review" and r["state"]=="pending_review"

def test_low_requires_mandatory_review():
    r=wf().submit(make(0.40)); assert r["review_requirement"]=="mandatory_review"

def test_high_risk_overrides_high_confidence():
    r=wf().submit(make(0.99,"critical")); assert r["review_requirement"]=="mandatory_review"

def test_approve_executes():
    x=wf(); x.submit(make(0.80)); r=x.review("T1","approve","alice"); assert r["state"]=="executed"

def test_reject_does_not_execute():
    x=wf(); x.submit(make(0.80)); r=x.review("T1","reject","alice"); assert r["state"]=="rejected" and r["execution"] is None

def test_modify_executes_modified_action():
    x=wf(); x.submit(make(0.60)); r=x.review("T1","modify","alice","register_as_preliminary"); assert r["final_action"]=="register_as_preliminary" and r["state"]=="executed"

def test_modify_requires_action():
    x=wf(); x.submit(make(0.60));
    with pytest.raises(ValueError): x.review("T1","modify","alice")

def test_review_missing_task():
    with pytest.raises(KeyError): wf().review("missing","approve","alice")

def test_cannot_review_auto_executed():
    x=wf(); x.submit(make(0.95));
    with pytest.raises(ValueError): x.review("T1","approve","alice")

def test_audit_events_recorded():
    x=wf(); x.submit(make(0.80)); x.review("T1","approve","alice"); assert len(x.audit.events) >= 4
