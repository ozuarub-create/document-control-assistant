"""Week 24 document workflow agent tools.

The tools are deliberately small, deterministic, and independently testable.  The
agent decides which tools to call; tools themselves do not decide orchestration.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import pymupdf
except Exception:  # pragma: no cover
    pymupdf = None


DOCUMENT_TYPES = {
    "drawing": ["drawing", "dwg", "plan", "layout", "section", "elevation"],
    "rfi": ["rfi", "request for information", "clarification"],
    "specification": ["specification", "spec", "section 03", "technical specification"],
    "meeting_minutes": ["meeting minutes", "minutes of meeting", "mom-"],
    "inspection_report": ["inspection", "inspection report", "quality inspection"],
    "method_statement": ["method statement", "work method", "procedure"],
    "material_submittal": ["material submittal", "submittal", "material approval"],
}

REQUIRED_FIELDS = {
    "drawing": ["document_number", "revision", "title", "date"],
    "rfi": ["document_number", "title", "date", "status"],
    "specification": ["document_number", "revision", "title"],
    "meeting_minutes": ["document_number", "title", "date"],
    "inspection_report": ["document_number", "title", "date", "status"],
    "method_statement": ["document_number", "revision", "title"],
    "material_submittal": ["document_number", "revision", "title", "status"],
    "unknown": ["title"],
}


@dataclass
class ToolContext:
    path: Path
    text: str
    task: str
    knowledge_base: list[dict[str, Any]]
    memory: dict[str, Any]


def read_document_text(path: str | Path) -> str:
    source = Path(path)
    suffix = source.suffix.lower()
    if suffix == ".pdf":
        if pymupdf is None:
            raise RuntimeError("PyMuPDF is required to read PDF documents.")
        with pymupdf.open(source) as doc:
            return "\n".join(page.get_text("text") for page in doc)
    if suffix in {".txt", ".md"}:
        return source.read_text(encoding="utf-8", errors="replace")
    raise ValueError("Supported document types: PDF, TXT, MD")


def _first_match(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).strip()
    return None


def classify_document(ctx: ToolContext) -> dict[str, Any]:
    haystack = f"{ctx.path.name}\n{ctx.text[:5000]}".lower()
    scores: dict[str, int] = {}
    for doc_type, keywords in DOCUMENT_TYPES.items():
        scores[doc_type] = sum(1 for keyword in keywords if keyword in haystack)
    best = max(scores, key=scores.get) if scores else "unknown"
    score = scores.get(best, 0)
    if score == 0:
        best = "unknown"
    confidence = 0.55 if best == "unknown" else min(0.99, 0.72 + 0.08 * score)
    ctx.memory["document_type"] = best
    return {"document_type": best, "confidence": round(confidence, 2), "evidence": f"keyword_score={score}"}


def extract_metadata(ctx: ToolContext) -> dict[str, Any]:
    text = ctx.text
    title = _first_match([
        r"(?:Title|Document Title)\s*[:\-]\s*(.+)",
        r"^#\s+(.+)$",
    ], text)
    doc_no = _first_match([
        r"(?:Document(?:\s+Number|\s+No\.?|\s+ID)?|Drawing\s+No\.?|RFI\s+No\.?)\s*[:\-]\s*([A-Z0-9_\-/]+)",
    ], text)
    revision = _first_match([r"(?:Revision|Rev\.?)\s*[:=-]\s*([A-Z0-9]+)"], text)
    date = _first_match([r"(?:Date|Issued)\s*[:\-]\s*([0-9]{4}[-/][0-9]{2}[-/][0-9]{2}|[0-9]{2}[-/][0-9]{2}[-/][0-9]{4})"], text)
    status = _first_match([r"(?:Status)\s*[:\-]\s*([^\n\r]+)"], text)
    metadata = {"title": title, "document_number": doc_no, "revision": revision, "date": date, "status": status}
    ctx.memory["metadata"] = metadata
    return {"metadata": metadata, "confidence": 0.92, "evidence": "regex_and_layout_text"}


def search_knowledge_base(ctx: ToolContext) -> dict[str, Any]:
    metadata = ctx.memory.get("metadata", {})
    doc_no = str(metadata.get("document_number") or "").lower()
    title = str(metadata.get("title") or "").lower()
    tokens = {token for token in re.findall(r"[a-z0-9]+", f"{doc_no} {title} {ctx.task.lower()}") if len(token) > 2}
    ranked: list[tuple[int, dict[str, Any]]] = []
    for item in ctx.knowledge_base:
        item_text = " ".join(str(v) for v in item.values()).lower()
        score = sum(1 for token in tokens if token in item_text)
        if score:
            ranked.append((score, item))
    ranked.sort(key=lambda pair: pair[0], reverse=True)
    results = [{**item, "match_score": score} for score, item in ranked[:5]]
    ctx.memory["knowledge_results"] = results
    return {"results": results, "count": len(results), "confidence": 0.88 if results else 0.4}


def check_completeness(ctx: ToolContext) -> dict[str, Any]:
    doc_type = ctx.memory.get("document_type", "unknown")
    metadata = ctx.memory.get("metadata") or extract_metadata(ctx)["metadata"]
    required = REQUIRED_FIELDS.get(doc_type, REQUIRED_FIELDS["unknown"])
    missing = [field for field in required if not metadata.get(field)]
    complete = not missing
    result = {"complete": complete, "required_fields": required, "missing_fields": missing, "confidence": 0.96}
    ctx.memory["completeness"] = result
    return result


def detect_previous_revisions(ctx: ToolContext) -> dict[str, Any]:
    metadata = ctx.memory.get("metadata") or extract_metadata(ctx)["metadata"]
    doc_no = metadata.get("document_number")
    current_rev = metadata.get("revision")
    matches: list[dict[str, Any]] = []
    if doc_no:
        for item in ctx.knowledge_base:
            if str(item.get("document_number", "")).lower() == str(doc_no).lower():
                rev = item.get("revision")
                if rev and str(rev).lower() != str(current_rev or "").lower():
                    matches.append(item)
    result = {"current_revision": current_rev, "previous_revisions": matches, "count": len(matches), "confidence": 0.95 if doc_no else 0.35}
    ctx.memory["previous_revisions"] = matches
    return result


def generate_summary(ctx: ToolContext) -> dict[str, Any]:
    clean = re.sub(r"\s+", " ", ctx.text).strip()
    summary = clean[:520]
    if len(clean) > 520:
        summary += "..."
    result = {"summary": summary or "No readable content found.", "confidence": 0.84}
    ctx.memory["summary"] = result["summary"]
    return result


def generate_review_comments(ctx: ToolContext) -> dict[str, Any]:
    comments: list[str] = []
    completeness = ctx.memory.get("completeness")
    if completeness and completeness.get("missing_fields"):
        comments.append("Provide missing metadata: " + ", ".join(completeness["missing_fields"]) + ".")
    lowered = ctx.text.lower()
    if "for construction" in lowered and ctx.memory.get("document_type") == "drawing":
        comments.append("Confirm that the issued-for-construction drawing has the required approval/signature before release.")
    if "open" in lowered and ctx.memory.get("document_type") == "rfi":
        comments.append("RFI remains open; obtain and record the formal response before closure.")
    if ctx.memory.get("previous_revisions"):
        comments.append("Review changes against the detected previous revision before approval.")
    if not comments:
        comments.append("No critical review issue detected by the automated checks; proceed with discipline review.")
    result = {"comments": comments, "count": len(comments), "confidence": 0.86}
    ctx.memory["review_comments"] = comments
    return result


def recommend_next_action(ctx: ToolContext) -> dict[str, Any]:
    doc_type = ctx.memory.get("document_type", "unknown")
    completeness = ctx.memory.get("completeness", {})
    comments = ctx.memory.get("review_comments", [])
    if completeness and not completeness.get("complete", True):
        action = "return_for_information_completion"
        reason = "Required metadata is missing."
    elif doc_type == "rfi" and "open" in ctx.text.lower():
        action = "route_to_responsible_engineer_for_response"
        reason = "The RFI is open and requires a response."
    elif ctx.memory.get("previous_revisions"):
        action = "route_for_revision_comparison_and_technical_review"
        reason = "A previous revision was detected."
    elif doc_type in {"drawing", "specification", "method_statement", "material_submittal"}:
        action = "route_for_technical_review"
        reason = "Document is complete enough for technical review."
    else:
        action = "route_for_document_control_review"
        reason = "A general document-control review is appropriate."
    if comments:
        reason += f" {len(comments)} review comment(s) generated."
    result = {"recommended_action": action, "reason": reason, "confidence": 0.9}
    ctx.memory["next_action"] = result
    return result


TOOLS = {
    "classify_document": classify_document,
    "extract_metadata": extract_metadata,
    "search_knowledge_base": search_knowledge_base,
    "check_completeness": check_completeness,
    "detect_previous_revisions": detect_previous_revisions,
    "generate_summary": generate_summary,
    "generate_review_comments": generate_review_comments,
    "recommend_next_action": recommend_next_action,
}
