"""Document review and validation engine for Week 17.

The review engine checks document quality before submission. It uses local,
explainable AI-style rules so the project works without paid services.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database
from app.embeddings import cosine_similarity, create_embedding
from app.repository import make_document_key, row_to_dict

REQUIRED_METADATA_FIELDS = {
    "document_title": "Document Title",
    "revision_number": "Revision Number",
    "project_name": "Project Name",
    "contractor": "Contractor",
    "consultant": "Consultant",
    "submission_date": "Submission Date",
    "discipline": "Discipline",
}

# Validation rules for common construction document types.
DOCUMENT_TYPE_RULES: dict[str, list[dict[str, Any]]] = {
    "Drawing": [
        {"name": "drawing reference", "keywords": ["drawing", "dwg", "drawing number"]},
        {"name": "scale or layout information", "keywords": ["scale", "layout", "plan", "elevation", "section"]},
        {"name": "revision information", "keywords": ["revision", "rev"]},
    ],
    "Specification": [
        {"name": "technical requirements", "keywords": ["specification", "technical", "requirement"]},
        {"name": "standards or compliance", "keywords": ["standard", "compliance", "quality"]},
        {"name": "materials and workmanship", "keywords": ["material", "workmanship", "performance"]},
    ],
    "Method Statement": [
        {"name": "sequence of work", "keywords": ["sequence of work", "work procedure", "procedure"]},
        {"name": "safety precautions", "keywords": ["safety", "precaution", "risk assessment"]},
        {"name": "equipment and manpower", "keywords": ["equipment", "manpower", "resources"]},
    ],
    "Material Submittal": [
        {"name": "manufacturer details", "keywords": ["manufacturer", "supplier"]},
        {"name": "product information", "keywords": ["product data", "data sheet", "catalogue", "sample"]},
        {"name": "approval request", "keywords": ["approval", "material approval", "submittal"]},
    ],
    "Shop Drawing": [
        {"name": "shop drawing reference", "keywords": ["shop drawing", "coordination drawing"]},
        {"name": "fabrication or installation details", "keywords": ["fabrication", "installation", "setting out"]},
        {"name": "revision information", "keywords": ["revision", "rev"]},
    ],
    "Inspection Report": [
        {"name": "inspection details", "keywords": ["inspection", "site inspection", "inspection request"]},
        {"name": "inspection result", "keywords": ["approved", "rejected", "result", "snag"]},
        {"name": "quality control reference", "keywords": ["qa/qc", "checklist", "quality"]},
    ],
    "Contract": [
        {"name": "scope of works", "keywords": ["scope of works", "scope"]},
        {"name": "commercial terms", "keywords": ["contract sum", "payment terms", "terms and conditions"]},
        {"name": "party obligations", "keywords": ["employer", "contractor obligations", "agreement"]},
    ],
    "Meeting Minutes": [
        {"name": "attendees", "keywords": ["attendees", "present"]},
        {"name": "agenda or discussion", "keywords": ["agenda", "discussion"]},
        {"name": "action items", "keywords": ["action items", "next meeting", "actions"]},
    ],
    "RFI": [
        {"name": "request for information", "keywords": ["rfi", "request for information", "clarification"]},
        {"name": "question or query", "keywords": ["question", "query"]},
        {"name": "response requirement", "keywords": ["response required", "reply", "response"]},
    ],
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"none", "null", "unknown", "n/a", "na"}


def _metadata_value(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key)
    return "Not found" if _is_missing(value) else str(value).strip()


def _content_has_any(text_lower: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text_lower for keyword in keywords)


def validate_document(processed: dict[str, Any]) -> dict[str, Any]:
    """Check metadata and document-type-specific validation rules."""
    metadata = processed.get("metadata", {})
    classification = processed.get("classification", {})
    document_type = classification.get("document_type", "Unknown")
    confidence = float(classification.get("confidence_score", 0.0))
    text = processed.get("content_text") or processed.get("text_preview") or ""
    text_lower = text.lower()

    missing_information: list[dict[str, str]] = []
    validation_rules_checked: list[dict[str, Any]] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    for field, label in REQUIRED_METADATA_FIELDS.items():
        missing = _is_missing(metadata.get(field))
        validation_rules_checked.append(
            {
                "rule": f"Required metadata: {label}",
                "passed": not missing,
                "severity": "high" if field in {"document_title", "project_name", "revision_number"} else "medium",
            }
        )
        if missing:
            missing_information.append({"field": field, "label": label})
            warnings.append(f"Missing required metadata: {label}.")
            recommendations.append(f"Add {label} before submitting the document.")

    if document_type == "Unknown":
        warnings.append("Document type could not be clearly classified.")
        recommendations.append("Add a clear Document Type label on the first page.")
        validation_rules_checked.append(
            {"rule": "Document type classification", "passed": False, "severity": "high"}
        )
    else:
        validation_rules_checked.append(
            {"rule": "Document type classification", "passed": True, "severity": "high"}
        )

    if confidence < 0.70:
        warnings.append(f"Low classification confidence: {confidence}.")
        recommendations.append("Review the document title and keywords to make the document type clearer.")
        validation_rules_checked.append(
            {"rule": "Classification confidence >= 0.70", "passed": False, "severity": "medium"}
        )
    else:
        validation_rules_checked.append(
            {"rule": "Classification confidence >= 0.70", "passed": True, "severity": "medium"}
        )

    if len(_clean_text(text)) < 120:
        warnings.append("Extracted document text is short; the file may be incomplete or scanned.")
        recommendations.append("Confirm the uploaded file contains readable PDF/DOCX text.")
        validation_rules_checked.append(
            {"rule": "Readable text length", "passed": False, "severity": "medium"}
        )
    else:
        validation_rules_checked.append(
            {"rule": "Readable text length", "passed": True, "severity": "medium"}
        )

    for rule in DOCUMENT_TYPE_RULES.get(document_type, []):
        passed = _content_has_any(text_lower, rule["keywords"])
        validation_rules_checked.append(
            {
                "rule": f"{document_type}: {rule['name']}",
                "passed": passed,
                "severity": "medium",
            }
        )
        if not passed:
            warnings.append(f"Missing expected {document_type} information: {rule['name']}.")
            recommendations.append(f"Add or clarify {rule['name']} for this {document_type} document.")

    # Remove repeated recommendations while keeping order.
    recommendations = list(dict.fromkeys(recommendations))
    warnings = list(dict.fromkeys(warnings))

    return {
        "missing_information": missing_information,
        "validation_rules_checked": validation_rules_checked,
        "warnings": warnings,
        "recommendations": recommendations,
    }


def generate_document_summary(processed: dict[str, Any]) -> dict[str, Any]:
    """Generate a short local AI-style summary from extracted metadata and text."""
    metadata = processed.get("metadata", {})
    classification = processed.get("classification", {})
    document_type = classification.get("document_type", "Unknown")
    matched_keywords = classification.get("matched_keywords", [])[:5]
    text = _clean_text(processed.get("content_text") or processed.get("text_preview") or "")

    title = _metadata_value(metadata, "document_title")
    project = _metadata_value(metadata, "project_name")
    contractor = _metadata_value(metadata, "contractor")
    consultant = _metadata_value(metadata, "consultant")
    revision = _metadata_value(metadata, "revision_number")
    submission_date = _metadata_value(metadata, "submission_date")
    discipline = _metadata_value(metadata, "discipline")

    sentences = re.split(r"(?<=[.!?])\s+", text)
    useful_sentences = [sentence.strip() for sentence in sentences if len(sentence.strip()) > 30]
    excerpt = " ".join(useful_sentences[:2])[:350]

    summary_text = (
        f"{title} is classified as {document_type} for {project}. "
        f"It is related to the {discipline} discipline, revision {revision}, "
        f"submitted on {submission_date} by {contractor} to {consultant}."
    )
    if excerpt:
        summary_text += f" Key extracted content: {excerpt}"

    key_points = [
        f"Document Type: {document_type}",
        f"Project: {project}",
        f"Revision: {revision}",
        f"Discipline: {discipline}",
    ]
    if matched_keywords:
        key_points.append("Classification evidence: " + ", ".join(matched_keywords))

    return {
        "summary_text": summary_text,
        "key_points": key_points,
    }


def detect_duplicate_submissions(
    processed: dict[str, Any],
    db_path: str | Path = DATABASE_PATH,
    limit: int = 5,
) -> dict[str, Any]:
    """Detect duplicate or repeated submissions using metadata and embeddings."""
    initialize_database(db_path)
    metadata = processed.get("metadata", {})
    filename = processed.get("filename", "")
    current_key = make_document_key(metadata, filename)
    current_revision = str(metadata.get("revision_number") or "").strip().lower()
    current_title = str(metadata.get("document_title") or "").strip().lower()
    current_project = str(metadata.get("project_name") or "").strip().lower()
    current_text = "\n".join(
        str(value)
        for value in [filename, current_title, current_project, processed.get("content_text") or processed.get("text_preview")]
        if value
    )
    current_embedding = create_embedding(current_text)

    candidates: list[dict[str, Any]] = []
    with get_connection(db_path) as connection:
        rows = connection.execute("SELECT * FROM documents ORDER BY id DESC LIMIT 300").fetchall()

    for row in rows:
        stored = row_to_dict(row, include_text=True, include_embedding=True)
        stored_revision = str(stored.get("revision_number") or "").strip().lower()
        stored_title = str(stored.get("document_title") or "").strip().lower()
        stored_project = str(stored.get("project_name") or "").strip().lower()
        stored_filename = str(stored.get("filename") or "").strip().lower()
        stored_key = str(stored.get("document_key") or "")
        stored_embedding = stored.get("embedding") if isinstance(stored.get("embedding"), dict) else {}

        same_key = stored_key == current_key
        same_revision = bool(current_revision and stored_revision == current_revision)
        same_filename = bool(filename and stored_filename == filename.lower())
        same_title_project = bool(current_title and current_project and stored_title == current_title and stored_project == current_project)
        semantic_similarity = cosine_similarity(current_embedding, stored_embedding)

        duplicate_score = 0.0
        if same_key:
            duplicate_score += 0.45
        if same_title_project:
            duplicate_score += 0.25
        if same_revision:
            duplicate_score += 0.20
        if same_filename:
            duplicate_score += 0.20
        if semantic_similarity >= 0.95:
            duplicate_score += 0.30
        elif semantic_similarity >= 0.85:
            duplicate_score += 0.20
        duplicate_score = round(min(duplicate_score, 1.0), 2)

        if same_key or same_filename or same_title_project or semantic_similarity >= 0.80:
            if (same_key or same_filename or same_title_project) and same_revision:
                match_type = "Exact Duplicate"
            elif same_key and not same_revision:
                match_type = "Possible New Version"
            elif semantic_similarity >= 0.88:
                match_type = "Possible Duplicate"
            else:
                match_type = "Similar Document"

            candidates.append(
                {
                    "document_id": stored.get("id"),
                    "filename": stored.get("filename"),
                    "document_title": stored.get("document_title"),
                    "revision_number": stored.get("revision_number"),
                    "version": stored.get("version"),
                    "is_latest": stored.get("is_latest"),
                    "match_type": match_type,
                    "duplicate_score": duplicate_score,
                    "semantic_similarity": semantic_similarity,
                }
            )

    candidates.sort(key=lambda item: item["duplicate_score"], reverse=True)
    candidates = candidates[:limit]

    if any(item["match_type"] == "Exact Duplicate" for item in candidates):
        status = "Exact Duplicate Found"
        is_duplicate = True
        recommendation = "Do not submit again. Use the existing registered document or upload a new revision."
    elif any(item["match_type"] == "Possible Duplicate" for item in candidates):
        status = "Possible Duplicate Found"
        is_duplicate = True
        recommendation = "Check the listed similar documents before submission."
    elif any(item["match_type"] == "Possible New Version" for item in candidates):
        status = "Possible New Version"
        is_duplicate = False
        recommendation = "Confirm the revision number and submit as a new version if appropriate."
    elif candidates:
        status = "Similar Document Found"
        is_duplicate = False
        recommendation = "Review similar documents to avoid repeated submission."
    else:
        status = "No Duplicate Found"
        is_duplicate = False
        recommendation = "No matching registered document was found."

    return {
        "status": status,
        "is_duplicate": is_duplicate,
        "document_key": current_key,
        "candidates": candidates,
        "recommendation": recommendation,
    }


def _calculate_quality_score(
    validation: dict[str, Any],
    duplicate_check: dict[str, Any],
    classification: dict[str, Any],
) -> int:
    score = 100
    missing_count = len(validation.get("missing_information", []))
    failed_rules = [rule for rule in validation.get("validation_rules_checked", []) if not rule.get("passed")]

    score -= min(missing_count * 8, 40)
    score -= min(len(failed_rules) * 4, 30)

    confidence = float(classification.get("confidence_score", 0.0))
    if confidence < 0.70:
        score -= 10
    if duplicate_check.get("status") == "Exact Duplicate Found":
        score -= 30
    elif duplicate_check.get("status") == "Possible Duplicate Found":
        score -= 15

    return max(0, min(100, score))


def review_document(processed: dict[str, Any], db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    """Produce a complete review report for one processed document."""
    classification = processed.get("classification", {})
    metadata = processed.get("metadata", {})
    validation = validate_document(processed)
    duplicate_check = detect_duplicate_submissions(processed, db_path=db_path)
    summary = generate_document_summary(processed)
    quality_score = _calculate_quality_score(validation, duplicate_check, classification)

    warnings = list(validation.get("warnings", []))
    recommendations = list(validation.get("recommendations", []))

    duplicate_status = duplicate_check.get("status", "No Duplicate Found")
    if duplicate_status != "No Duplicate Found":
        warnings.append(f"Duplicate check result: {duplicate_status}.")
        recommendations.append(duplicate_check.get("recommendation", "Review duplicate candidates."))

    if duplicate_status == "Exact Duplicate Found" or quality_score < 60:
        validation_status = "Fail"
    elif warnings or quality_score < 85:
        validation_status = "Needs Review"
    else:
        validation_status = "Pass"

    recommendations = list(dict.fromkeys(recommendations))
    warnings = list(dict.fromkeys(warnings))

    report_seed = f"{processed.get('filename', '')}|{metadata.get('document_title', '')}|{datetime.now(timezone.utc).isoformat()}"
    review_id = hashlib.sha256(report_seed.encode("utf-8")).hexdigest()[:12]

    return {
        "review_id": review_id,
        "filename": processed.get("filename"),
        "document_type": classification.get("document_type"),
        "confidence_score": classification.get("confidence_score"),
        "metadata": metadata,
        "validation_status": validation_status,
        "quality_score": quality_score,
        "summary": summary,
        "missing_information": validation.get("missing_information", []),
        "warnings": warnings,
        "recommendations": recommendations,
        "validation_rules_checked": validation.get("validation_rules_checked", []),
        "duplicate_check": duplicate_check,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def report_to_json(report: dict[str, Any]) -> str:
    """Convert report to readable JSON for storage or export."""
    return json.dumps(report, indent=2, ensure_ascii=False)
