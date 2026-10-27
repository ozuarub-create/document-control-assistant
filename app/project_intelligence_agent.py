from __future__ import annotations
from typing import Any, Dict, List
from .investigation_planner import build_plan
from .project_tools import unresolved_documents, overdue_actions, related_documents
from .conflict_detector import detect_conflicts
from .evidence_engine import evidence, cite_many


class ProjectIntelligenceAgent:
    def __init__(self, documents: List[Dict[str, Any]]):
        self.documents = documents
        self.trace: List[Dict[str, Any]] = []

    def _log(self, step: str, tool: str, result_count: int, reason: str):
        self.trace.append({"step": step, "tool": tool, "result_count": result_count, "reason": reason})

    def investigate(self, request: str) -> Dict[str, Any]:
        plan = build_plan(request)
        self.trace = []

        unresolved = unresolved_documents(self.documents)
        self._log("search", "unresolved_documents", len(unresolved), "Identify open/pending/overdue project items")

        overdue = overdue_actions(self.documents)
        self._log("search", "overdue_actions", len(overdue), "Identify overdue actions requiring attention")

        conflicts = detect_conflicts(self.documents)
        self._log("conflicts", "detect_conflicts", len(conflicts), "Find contradictory information")

        findings = []
        for doc in unresolved:
            ev = [evidence(doc, doc.get("evidence", doc.get("content", ""))[:220], doc.get("page", 1), 0.96)]
            findings.append({
                "kind": "Fact",
                "statement": f"{doc['id']} ({doc['type']}) remains {doc['status']}: {doc['title']}",
                "citations": cite_many(ev),
                "evidence": ev,
            })

        major_risks = [f for f in findings if any(k in f["statement"].lower() for k in ["risk", "delay", "rfi", "rejected", "overdue"])]
        unresolved_items = [f for f in findings if any(k in f["statement"].lower() for k in ["rfi", "submittal"])]

        action_findings = []
        for action in overdue:
            doc = next(d for d in self.documents if d["id"] == action["document_id"])
            ev = [evidence(doc, f"Action: {action['action']} | Owner: {action.get('owner')} | Due: {action.get('due')}")]
            action_findings.append({"kind": "Fact", "statement": f"Overdue action: {action['action']} (Owner: {action.get('owner')}, Due: {action.get('due')})", "citations": cite_many(ev), "evidence": ev})

        conflict_findings = []
        for c in conflicts:
            conflict_findings.append({
                "kind": "Fact",
                "statement": f"Conflicting information on {c['topic']}: {c['document_a']} says '{c['position_a']}' while {c['document_b']} says '{c['position_b']}'.",
                "citations": [f"[{c['document_a']}]", f"[{c['document_b']}]"],
            })

        potential_delays = []
        for f in major_risks + action_findings:
            potential_delays.append({
                "kind": "Inference",
                "statement": f"Schedule impact is possible because {f['statement'].lower()}",
                "citations": f.get("citations", []),
            })

        commercial = []
        for doc in self.documents:
            if doc.get("type") in {"Contract", "Correspondence"} and doc.get("status") in {"open", "pending"}:
                ev = [evidence(doc, doc.get("evidence", doc.get("content", ""))[:220])]
                commercial.append({"kind": "Fact", "statement": f"{doc['title']} requires commercial/contractual attention.", "citations": cite_many(ev), "evidence": ev})

        recommendations = []
        if unresolved_items:
            recommendations.append({"kind": "Recommendation", "statement": "Assign owners and closure dates for unresolved RFIs and submittals, and review them in the next coordination meeting.", "citations": sum([x.get("citations", []) for x in unresolved_items], [])[:4]})
        if action_findings:
            recommendations.append({"kind": "Recommendation", "statement": "Escalate overdue actions to responsible discipline leads and require recovery dates.", "citations": sum([x.get("citations", []) for x in action_findings], [])[:4]})
        if conflicts:
            recommendations.append({"kind": "Recommendation", "statement": "Resolve conflicting project information before further execution or approval.", "citations": sum([x.get("citations", []) for x in conflict_findings], [])[:4]})

        evidence_count = sum(len(f.get("evidence", [])) for f in findings + action_findings + commercial)
        sufficient = evidence_count >= max(3, len(findings) // 2)
        self._log("evidence", "collect_evidence", evidence_count, "Support significant findings with citations")
        self._log("sufficiency", "evidence_sufficiency_check", int(sufficient), "Prevent unsupported assumptions from being presented as facts")

        report = {
            "request": request,
            "plan": plan,
            "executive_summary": f"The investigation identified {len(unresolved)} unresolved project documents, {len(overdue)} overdue actions and {len(conflicts)} conflicting information item(s). Evidence sufficiency: {'sufficient' if sufficient else 'limited'}.",
            "major_risks": major_risks,
            "outstanding_actions": action_findings,
            "potential_delays": potential_delays,
            "commercial_issues": commercial,
            "unresolved_items": unresolved_items,
            "conflicts": conflict_findings,
            "recommendations": recommendations,
            "evidence_sufficient": sufficient,
            "execution_trace": self.trace,
        }
        self._log("report", "management_report", 1, "Generate structured executive report")
        report["execution_trace"] = self.trace
        return report
