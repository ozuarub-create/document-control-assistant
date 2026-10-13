from .approval_audit import AuditLogger
from .approval_executor import ActionExecutor
from .approval_repository import ApprovalRepository
from .approval_rules import load_rules, review_requirement

class ApprovalWorkflow:
    def __init__(self, rules_path="config/approval_rules.json", repository=None, audit=None, executor=None):
        self.rules = load_rules(rules_path)
        self.repository = repository or ApprovalRepository()
        self.audit = audit or AuditLogger()
        self.executor = executor or ActionExecutor()

    def submit(self, request):
        data = request.model_dump() if hasattr(request, "model_dump") else dict(request)
        requirement = review_requirement(data["confidence"], data["risk_level"], self.rules)
        record = {
            "task_id": data["task_id"],
            "request": data,
            "review_requirement": requirement,
            "state": "pending_review",
            "final_action": data["proposed_action"],
            "execution": None,
        }
        self.audit.log("task_received", data["task_id"], data)
        self.audit.log("review_rule_evaluated", data["task_id"], {"requirement": requirement})

        if requirement == "automatic":
            record["execution"] = self.executor.execute(record["final_action"], record)
            record["state"] = "auto_executed"
            self.audit.log("auto_executed", data["task_id"], record["execution"])

        self.repository.save(data["task_id"], record)
        return record

    def review(self, task_id, decision, reviewer, modified_action=None, comment=None):
        record = self.repository.get(task_id)
        if record["state"] != "pending_review":
            raise ValueError("Task is not awaiting review")

        decision = decision.value if hasattr(decision, "value") else decision
        self.audit.log("human_review", task_id, {
            "decision": decision,
            "reviewer": reviewer,
            "modified_action": modified_action,
            "comment": comment,
        })

        if decision == "reject":
            record["state"] = "rejected"
            self.repository.save(task_id, record)
            return record

        if decision == "modify":
            if not modified_action:
                raise ValueError("modified_action is required for modify decision")
            record["final_action"] = modified_action
            record["state"] = "modified"
        else:
            record["state"] = "approved"

        record["execution"] = self.executor.execute(record["final_action"], record)
        record["state"] = "executed"
        self.audit.log("executed_after_review", task_id, record["execution"])
        self.repository.save(task_id, record)
        return record
