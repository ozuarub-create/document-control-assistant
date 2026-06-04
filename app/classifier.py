"""Simple document classification engine.

The classifier uses labels and construction-document keywords. This keeps the
assignment easy to run locally without paid AI services.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


DOCUMENT_CATEGORIES = [
    "Drawing",
    "Specification",
    "Method Statement",
    "Material Submittal",
    "Shop Drawing",
    "Inspection Report",
    "Contract",
    "Meeting Minutes",
    "RFI",
]

CATEGORY_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "Drawing": [
        ("drawing", 5), ("general arrangement", 4), ("layout", 3), ("plan", 3),
        ("elevation", 3), ("section", 2), ("scale", 2), ("grid", 2), ("dwg", 3),
    ],
    "Specification": [
        ("specification", 6), ("technical specification", 5), ("performance requirements", 3),
        ("materials and workmanship", 3), ("standard", 2), ("compliance", 2),
        ("quality requirements", 3),
    ],
    "Method Statement": [
        ("method statement", 7), ("work procedure", 4), ("sequence of work", 4),
        ("risk assessment", 3), ("safety precautions", 3), ("equipment and manpower", 3),
        ("installation procedure", 3),
    ],
    "Material Submittal": [
        ("material submittal", 7), ("manufacturer", 3), ("product data", 4),
        ("sample", 2), ("supplier", 3), ("material approval", 4),
        ("catalogue", 3), ("data sheet", 3),
    ],
    "Shop Drawing": [
        ("shop drawing", 8), ("fabrication", 3), ("coordination drawing", 4),
        ("installation details", 3), ("setting out", 3), ("builder work", 3),
        ("as built", 2),
    ],
    "Inspection Report": [
        ("inspection report", 7), ("inspection request", 3), ("site inspection", 4),
        ("checklist", 3), ("approved", 2), ("rejected", 2), ("snag", 3),
        ("inspection result", 4), ("qa/qc", 3),
    ],
    "Contract": [
        ("contract", 7), ("agreement", 4), ("terms and conditions", 4),
        ("contract sum", 4), ("scope of works", 3), ("payment terms", 3),
        ("employer", 3), ("contractor obligations", 3),
    ],
    "Meeting Minutes": [
        ("meeting minutes", 8), ("minutes of meeting", 8), ("attendees", 3),
        ("agenda", 3), ("action items", 4), ("next meeting", 3), ("discussion", 2),
    ],
    "RFI": [
        ("rfi", 8), ("request for information", 8), ("clarification", 4),
        ("query", 3), ("response required", 4), ("question", 2), ("reply", 2),
    ],
}


@dataclass
class ClassificationResult:
    document_type: str
    confidence_score: float
    matched_keywords: list[str]
    scores: dict[str, int]

    def to_dict(self) -> dict:
        return {
            "document_type": self.document_type,
            "confidence_score": self.confidence_score,
            "matched_keywords": self.matched_keywords,
            "scores": self.scores,
        }


def _normalize_category(value: str) -> str | None:
    value = re.sub(r"[^a-zA-Z ]+", " ", value).strip().lower()
    for category in DOCUMENT_CATEGORIES:
        if value == category.lower():
            return category
    aliases = {
        "minutes": "Meeting Minutes",
        "mom": "Meeting Minutes",
        "request for information": "RFI",
        "information request": "RFI",
        "material approval request": "Material Submittal",
        "inspection": "Inspection Report",
    }
    return aliases.get(value)


def _find_declared_document_type(text: str) -> str | None:
    labels = ["Document Type", "Category", "Type"]
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for index, line in enumerate(lines):
        for label in labels:
            label_lower = label.lower()
            line_lower = line.lower()

            if line_lower == label_lower and index + 1 < len(lines):
                category = _normalize_category(lines[index + 1])
                if category:
                    return category

            if line_lower.startswith(label_lower):
                rest = line[len(label):].strip()
                if rest.startswith((":", "-", "|")):
                    category = _normalize_category(rest[1:].strip())
                    if category:
                        return category
    return None


def classify_document(text: str, filename: str = "") -> ClassificationResult:
    """Classify the document and return a confidence score from 0 to 1."""
    combined_text = f"{filename}\n{text}".lower()
    declared = _find_declared_document_type(text)

    scores: dict[str, int] = {}
    evidence: dict[str, list[str]] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        hits: list[str] = []
        for keyword, weight in keywords:
            occurrences = len(re.findall(rf"\b{re.escape(keyword.lower())}\b", combined_text))
            if occurrences:
                score += min(occurrences, 3) * weight
                hits.append(keyword)
        scores[category] = score
        evidence[category] = hits

    if declared:
        scores[declared] += 20
        evidence[declared].insert(0, f"declared type: {declared}")

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    sorted_scores = sorted(scores.values(), reverse=True)
    second_score = sorted_scores[1] if len(sorted_scores) > 1 else 0

    if best_score == 0:
        return ClassificationResult(
            document_type="Unknown",
            confidence_score=0.20,
            matched_keywords=[],
            scores=scores,
        )

    # Confidence uses both strength and margin. Exact declared type gets a boost.
    margin = max(best_score - second_score, 0)
    confidence = 0.45 + min(best_score, 35) / 100 + min(margin, 25) / 125
    if declared == best_type:
        confidence += 0.07
    confidence = max(0.50, min(confidence, 0.99))

    return ClassificationResult(
        document_type=best_type,
        confidence_score=round(confidence, 2),
        matched_keywords=evidence[best_type],
        scores=scores,
    )
