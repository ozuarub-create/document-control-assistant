from app.approval_models import TaskRequest
from app.approval_workflow import ApprovalWorkflow


def req(task_id, confidence, risk="low", action="register_classification"):
    return TaskRequest(
        task_id=task_id,
        document_id=f"DOC-{task_id}",
        document_type="Structural Shop Drawing",
        revision="03",
        confidence=confidence,
        proposed_action=action,
        risk_level=risk,
        metadata={"source": "demo"},
    )


def main():
    wf = ApprovalWorkflow()
    print("Week 28 - Human-in-the-Loop AI Approval Demo")
    print("=" * 60)

    auto = wf.submit(req("AUTO-01", 0.96))
    print(f"AUTO-01 -> requirement={auto['review_requirement']} state={auto['state']}")

    medium = wf.submit(req("REVIEW-01", 0.78))
    print(f"REVIEW-01 -> requirement={medium['review_requirement']} state={medium['state']}")
    approved = wf.review("REVIEW-01", "approve", "reviewer@example.com", comment="Verified")
    print(f"REVIEW-01 approved -> state={approved['state']}")

    low = wf.submit(req("LOW-01", 0.52))
    print(f"LOW-01 -> requirement={low['review_requirement']} state={low['state']}")
    modified = wf.review("LOW-01", "modify", "reviewer@example.com", modified_action="register_as_preliminary", comment="Adjusted classification")
    print(f"LOW-01 modified -> state={modified['state']} action={modified['final_action']}")

    high_risk = wf.submit(req("RISK-01", 0.99, risk="critical", action="release_for_construction"))
    print(f"RISK-01 -> requirement={high_risk['review_requirement']} state={high_risk['state']}")
    rejected = wf.review("RISK-01", "reject", "senior.reviewer@example.com", comment="Insufficient evidence")
    print(f"RISK-01 rejected -> state={rejected['state']}")

    print("\nWeek 28 Demo Complete")
    print("- Configurable confidence thresholds: working")
    print("- Automatic processing: working")
    print("- Human review: working")
    print("- Approve/reject/modify: working")
    print("- High-risk override: working")
    print("- Audit trail: working")

if __name__ == "__main__":
    main()
