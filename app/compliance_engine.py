"""Week 19 compliance checking engine.

This module reviews construction documents against configurable compliance
requirements. It is intentionally local and explainable so it works without a
paid AI/API service while still behaving like an AI document assistant.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

REQUIRED_METADATA_LABELS: dict[str, str] = {
    "document_title": "Document Title",
    "revision_number": "Revision Number",
    "project_name": "Project Name",
    "contractor": "Contractor",
    "consultant": "Consultant",
    "submission_date": "Submission Date",
    "discipline": "Discipline",
}

# Configurable document-type rules. To change the compliance behavior, update
# this dictionary. Each document type can have required metadata, sections,
# approval indicators, signature indicators, and document-number patterns.
COMPLIANCE_RULES: dict[str, dict[str, Any]] = {
    "Drawing": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "drawing reference", "keywords": ["drawing", "drawing number", "dwg", "layout", "plan"]},
            {"name": "revision history", "keywords": ["revision", "rev"]},
            {"name": "scale or grid reference", "keywords": ["scale", "grid", "section", "elevation"]},
        ],
        "approval_keywords": ["approved", "approval", "checked by", "approved by"],
        "signature_keywords": ["signature", "signed", "prepared by", "checked by", "approved by"],
        "document_number_patterns": [r"drawing\s*(number|no\.?|ref\.?)[\s:]+[a-z0-9\-/]+", r"dwg[\s\-:]+[a-z0-9\-/]+"],
    },
    "Specification": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "scope", "keywords": ["scope", "general requirements"]},
            {"name": "technical requirements", "keywords": ["technical", "specification", "requirement"]},
            {"name": "quality or standards", "keywords": ["quality", "standard", "compliance"]},
        ],
        "approval_keywords": ["approved", "approval", "reviewed by"],
        "signature_keywords": ["signature", "signed", "prepared by", "reviewed by", "approved by"],
        "document_number_patterns": [r"specification\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"spec[\s\-:]+[a-z0-9\-/]+"],
    },
    "Method Statement": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "work procedure", "keywords": ["procedure", "sequence of work", "methodology"]},
            {"name": "risk and safety", "keywords": ["risk", "safety", "hazard", "precaution"]},
            {"name": "resources", "keywords": ["equipment", "manpower", "resources", "materials"]},
        ],
        "approval_keywords": ["approved", "approval", "approved by", "site approval"],
        "signature_keywords": ["signature", "signed", "prepared by", "checked by", "approved by"],
        "document_number_patterns": [r"method\s*statement\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"ms[\s\-:]+[a-z0-9\-/]+"],
    },
    "Material Submittal": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "manufacturer or supplier", "keywords": ["manufacturer", "supplier"]},
            {"name": "product data", "keywords": ["product data", "data sheet", "catalogue", "sample"]},
            {"name": "approval request", "keywords": ["approval", "submittal", "material approval"]},
        ],
        "approval_keywords": ["approved", "approval", "material approval", "consultant approval"],
        "signature_keywords": ["signature", "signed", "submitted by", "approved by"],
        "document_number_patterns": [r"submittal\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"msub[\s\-:]+[a-z0-9\-/]+"],
    },
    "Shop Drawing": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "shop drawing reference", "keywords": ["shop drawing", "coordination drawing"]},
            {"name": "fabrication or installation details", "keywords": ["fabrication", "installation", "setting out"]},
            {"name": "revision history", "keywords": ["revision", "rev"]},
        ],
        "approval_keywords": ["approved", "approval", "checked by", "approved by"],
        "signature_keywords": ["signature", "signed", "prepared by", "checked by", "approved by"],
        "document_number_patterns": [r"shop\s*drawing\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"sd[\s\-:]+[a-z0-9\-/]+"],
    },
    "Inspection Report": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "inspection details", "keywords": ["inspection", "inspection request", "site inspection"]},
            {"name": "inspection result", "keywords": ["approved", "rejected", "result", "snag"]},
            {"name": "quality checklist", "keywords": ["checklist", "quality", "qa/qc"]},
        ],
        "approval_keywords": ["approved", "accepted", "passed", "signed off"],
        "signature_keywords": ["signature", "signed", "inspected by", "approved by"],
        "document_number_patterns": [r"inspection\s*(request|report)?\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"ir[\s\-:]+[a-z0-9\-/]+"],
    },
    "Contract": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "scope of works", "keywords": ["scope of works", "scope"]},
            {"name": "commercial terms", "keywords": ["contract sum", "payment terms", "terms and conditions"]},
            {"name": "party obligations", "keywords": ["employer", "contractor obligations", "agreement"]},
        ],
        "approval_keywords": ["approved", "agreement", "accepted", "executed"],
        "signature_keywords": ["signature", "signed", "signed by", "authorized representative"],
        "document_number_patterns": [r"contract\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"agreement\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+"],
    },
    "Meeting Minutes": {
        "required_metadata": ["document_title", "project_name", "contractor", "consultant", "submission_date", "discipline"],
        "mandatory_sections": [
            {"name": "attendees", "keywords": ["attendees", "present"]},
            {"name": "agenda or discussion", "keywords": ["agenda", "discussion"]},
            {"name": "actions", "keywords": ["action items", "actions", "next meeting"]},
        ],
        "approval_keywords": ["approved", "confirmed", "accepted"],
        "signature_keywords": ["signature", "signed", "prepared by", "chairperson"],
        "document_number_patterns": [r"meeting\s*(minutes)?\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+", r"mom[\s\-:]+[a-z0-9\-/]+"],
    },
    "RFI": {
        "required_metadata": list(REQUIRED_METADATA_LABELS),
        "mandatory_sections": [
            {"name": "request for information", "keywords": ["rfi", "request for information", "clarification"]},
            {"name": "question or query", "keywords": ["question", "query"]},
            {"name": "response requirement", "keywords": ["response", "reply", "response required"]},
        ],
        "approval_keywords": ["answered", "response", "approved", "closed"],
        "signature_keywords": ["signature", "signed", "submitted by", "responded by", "approved by"],
        "document_number_patterns": [r"rfi\s*(number|no\.?|ref\.?)?[\s:]+[a-z0-9\-/]+"],
    },
}

SEVERITY_DEDUCTIONS = {
    "critical": 18,
    "high": 12,
    "medium": 7,
    "low": 3,
}


def _clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _is_missing(value: Any) -> bool:
    text = _clean_text(value)
    return text == "" or text.lower() in {"none", "null", "unknown", "n/a", "na", "not found"}


def _content_has_any(text_lower: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text_lower for keyword in keywords)


def _content_matches_any(text_lower: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text_lower, flags=re.IGNORECASE) for pattern in patterns)


def _finding(rule_id: str, category: str, severity: str, passed: bool, message: str, recommendation: str) -> dict[str, Any]:
    return {
        "rule_id": rule_id,
        "category": category,
        "severity": severity,
        "passed": passed,
        "message": message,
        "recommendation": recommendation,
    }


def get_compliance_rules() -> dict[str, Any]:
    """Return the current configurable compliance rules."""
    return COMPLIANCE_RULES


def check_document_compliance(processed: dict[str, Any]) -> dict[str, Any]:
    """Check a processed document against required metadata and mandatory sections."""
    metadata = processed.get("metadata", {}) or {}
    classification = processed.get("classification", {}) or {}
    document_type = classification.get("document_type", "Unknown") or "Unknown"
    rules = COMPLIANCE_RULES.get(document_type, COMPLIANCE_RULES["Drawing"])
    filename = processed.get("filename", "unknown")
    content_text = processed.get("content_text") or processed.get("text_preview") or ""
    text_lower = _clean_text(content_text).lower()

    findings: list[dict[str, Any]] = []

    # Required metadata checks.
    for field in rules.get("required_metadata", []):
        label = REQUIRED_METADATA_LABELS.get(field, field.replace("_", " ").title())
        missing = _is_missing(metadata.get(field))
        findings.append(
            _finding(
                f"metadata_{field}",
                "required_metadata",
                "high" if field in {"document_title", "revision_number", "project_name"} else "medium",
                not missing,
                f"{label} is present." if not missing else f"Missing required metadata: {label}.",
                f"Add {label} before submission." if missing else "No action required.",
            )
        )

    # Explicit checks requested by the assignment.
    has_revision = not _is_missing(metadata.get("revision_number")) or _content_has_any(text_lower, ["revision", "rev"])
    findings.append(
        _finding(
            "revision_check",
            "revision",
            "high",
            has_revision,
            "Revision information is present." if has_revision else "Missing revision information.",
            "Add revision number and revision history before submission." if not has_revision else "No action required.",
        )
    )

    has_date = not _is_missing(metadata.get("submission_date")) or bool(re.search(r"\b20\d{2}[-/]\d{1,2}[-/]\d{1,2}\b", text_lower))
    findings.append(
        _finding(
            "date_check",
            "date",
            "high",
            has_date,
            "Submission date or document date is present." if has_date else "Missing document date or submission date.",
            "Add submission date or document date." if not has_date else "No action required.",
        )
    )

    has_document_number = _content_matches_any(text_lower, rules.get("document_number_patterns", [])) or _content_has_any(
        text_lower, ["document number", "document no", "doc no", "reference number", "reference no"]
    )
    findings.append(
        _finding(
            "document_number_check",
            "document_number",
            "high",
            has_document_number,
            "Document number/reference is present." if has_document_number else "Missing document number or reference number.",
            "Add a clear document number/reference number." if not has_document_number else "No action required.",
        )
    )

    has_signature = _content_has_any(text_lower, rules.get("signature_keywords", []))
    findings.append(
        _finding(
            "signature_check",
            "signature",
            "medium",
            has_signature,
            "Signature/prepared-by/checker information is present." if has_signature else "Missing signature or prepared/checked/approved by information.",
            "Add signature block or prepared/checked/approved by information." if not has_signature else "No action required.",
        )
    )

    has_approval = _content_has_any(text_lower, rules.get("approval_keywords", []))
    findings.append(
        _finding(
            "approval_check",
            "approval",
            "medium",
            has_approval,
            "Approval/acceptance information is present." if has_approval else "Missing approval or acceptance information.",
            "Add approval status, reviewer approval, or acceptance information." if not has_approval else "No action required.",
        )
    )

    # Mandatory section checks by document type.
    for index, section in enumerate(rules.get("mandatory_sections", []), start=1):
        passed = _content_has_any(text_lower, section.get("keywords", []))
        findings.append(
            _finding(
                f"section_{index}_{section['name'].replace(' ', '_')}",
                "mandatory_section",
                "medium",
                passed,
                f"Mandatory section found: {section['name']}." if passed else f"Missing mandatory section: {section['name']}.",
                f"Add or clarify the {section['name']} section." if not passed else "No action required.",
            )
        )

    # Inconsistency check: document title should not contradict classified type.
    title = _clean_text(metadata.get("document_title")).lower()
    inconsistent = False
    if title and document_type != "Unknown":
        other_types = [name.lower() for name in COMPLIANCE_RULES if name != document_type]
        inconsistent = any(other in title for other in other_types)
    findings.append(
        _finding(
            "title_type_consistency",
            "inconsistency",
            "low",
            not inconsistent,
            "Document title is consistent with classification." if not inconsistent else "Document title may conflict with the classified document type.",
            "Review the title and document type classification." if inconsistent else "No action required.",
        )
    )

    failed_findings = [item for item in findings if not item["passed"]]
    score = 100 - sum(SEVERITY_DEDUCTIONS.get(item["severity"], 5) for item in failed_findings)
    score = max(0, min(100, score))

    critical_failures = [item for item in failed_findings if item["severity"] == "critical"]
    if score >= 85 and not critical_failures:
        status = "Compliant"
    elif score >= 60:
        status = "Needs Revision"
    else:
        status = "Non-Compliant"

    missing_items = [item for item in failed_findings if item["category"] in {"required_metadata", "signature", "approval", "revision", "date", "document_number", "mandatory_section"}]
    warnings = [item["message"] for item in failed_findings]
    recommendations = list(dict.fromkeys(item["recommendation"] for item in failed_findings if item["recommendation"] != "No action required."))

    report = {
        "report_type": "Week 19 Compliance Validation Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "filename": filename,
        "document_type": document_type,
        "classification_confidence": classification.get("confidence_score", 0),
        "metadata": metadata,
        "compliance_status": status,
        "compliance_score": score,
        "summary": {
            "total_rules_checked": len(findings),
            "passed_rules": len(findings) - len(failed_findings),
            "failed_rules": len(failed_findings),
            "missing_items_count": len(missing_items),
        },
        "findings": findings,
        "missing_items": missing_items,
        "warnings": warnings,
        "recommendations": recommendations,
        "structured_review": {
            "metadata_complete": not any(not item["passed"] for item in findings if item["category"] == "required_metadata"),
            "mandatory_sections_complete": not any(not item["passed"] for item in findings if item["category"] == "mandatory_section"),
            "signature_present": has_signature,
            "revision_present": has_revision,
            "approval_present": has_approval,
            "date_present": has_date,
            "document_number_present": has_document_number,
        },
    }
    return report
