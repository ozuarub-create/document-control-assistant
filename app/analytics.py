"""Analytics and reporting for the integrated document control platform."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database
from app.workflow import get_workflow_summary


def _count_by(rows: list[Any], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        value = row[field] if row[field] else "Unknown"
        counter[str(value)] += 1
    return dict(counter)


def generate_platform_analytics(db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    """Return document, workflow, review, and quality metrics."""
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        documents = connection.execute("SELECT * FROM documents").fetchall()
        latest_documents = connection.execute("SELECT * FROM documents WHERE is_latest = 1").fetchall()
        reviews = connection.execute("SELECT * FROM document_reviews").fetchall()
        latest_preview = connection.execute(
            """
            SELECT id, filename, document_type, document_title, project_name, workflow_state, created_at
            FROM documents
            WHERE is_latest = 1
            ORDER BY created_at DESC, id DESC
            LIMIT 10
            """
        ).fetchall()

    confidence_values = [float(row["confidence_score"] or 0) for row in latest_documents]
    quality_values = [int(row["quality_score"] or 0) for row in reviews]
    duplicate_reviews = [row for row in reviews if row["duplicate_status"] != "No Duplicate Found"]

    review_status_counts: Counter[str] = Counter()
    warning_counter: Counter[str] = Counter()
    recommendation_counter: Counter[str] = Counter()
    for row in reviews:
        review_status_counts[row["review_status"] or "Unknown"] += 1
        try:
            report = json.loads(row["report_json"])
        except Exception:
            report = {}
        for warning in report.get("warnings", []) or []:
            warning_counter[str(warning)] += 1
        for recommendation in report.get("recommendations", []) or []:
            recommendation_counter[str(recommendation)] += 1

    return {
        "document_totals": {
            "total_records": len(documents),
            "latest_documents": len(latest_documents),
            "older_versions": max(len(documents) - len(latest_documents), 0),
        },
        "classification": {
            "by_document_type": _count_by(latest_documents, "document_type"),
            "by_discipline": _count_by(latest_documents, "discipline"),
            "average_confidence_score": round(mean(confidence_values), 3) if confidence_values else 0,
        },
        "workflow": {
            "by_state": get_workflow_summary(db_path=db_path),
        },
        "review_quality": {
            "total_reviews": len(reviews),
            "by_review_status": dict(review_status_counts),
            "average_quality_score": round(mean(quality_values), 2) if quality_values else 0,
            "duplicate_reviews": len(duplicate_reviews),
            "top_warnings": dict(warning_counter.most_common(5)),
            "top_recommendations": dict(recommendation_counter.most_common(5)),
        },
        "latest_documents_preview": [dict(row) for row in latest_preview],
    }


def generate_accuracy_and_performance_report(
    processed_documents: int,
    correct_classifications: int,
    total_seconds: float,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    analytics = generate_platform_analytics(db_path=db_path)
    accuracy = correct_classifications / processed_documents if processed_documents else 0
    docs_per_second = processed_documents / total_seconds if total_seconds else 0
    average_seconds = total_seconds / processed_documents if processed_documents else 0
    return {
        "processed_documents": processed_documents,
        "correct_classifications": correct_classifications,
        "classification_accuracy": round(accuracy, 4),
        "classification_accuracy_percent": round(accuracy * 100, 2),
        "total_processing_seconds": round(total_seconds, 4),
        "average_seconds_per_document": round(average_seconds, 4),
        "documents_per_second": round(docs_per_second, 2),
        "analytics_snapshot": analytics,
    }


def save_report(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
