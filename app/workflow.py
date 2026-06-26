"""Document lifecycle workflow states and transitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database
from app.repository import row_to_dict

WORKFLOW_STATES = [
    "registered",
    "under_review",
    "needs_revision",
    "approved",
    "rejected",
    "archived",
]

ALLOWED_TRANSITIONS = {
    "registered": {"under_review", "approved", "rejected", "archived"},
    "under_review": {"needs_revision", "approved", "rejected", "archived"},
    "needs_revision": {"under_review", "approved", "rejected", "archived"},
    "approved": {"archived", "under_review"},
    "rejected": {"archived", "under_review"},
    "archived": {"registered"},
}


def _get_document_row(document_id: int, db_path: str | Path = DATABASE_PATH) -> Any | None:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        return connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()


def get_workflow_states() -> dict[str, Any]:
    return {
        "states": WORKFLOW_STATES,
        "transitions": {state: sorted(list(targets)) for state, targets in ALLOWED_TRANSITIONS.items()},
    }


def get_workflow_history(document_id: int, db_path: str | Path = DATABASE_PATH) -> list[dict[str, Any]]:
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM workflow_history
            WHERE document_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (document_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def update_workflow_state(
    document_id: int,
    new_state: str,
    action: str | None = None,
    user: str = "system",
    comment: str | None = None,
    db_path: str | Path = DATABASE_PATH,
    enforce_transition: bool = True,
) -> dict[str, Any]:
    """Move a document to a new workflow state and record the lifecycle event."""
    new_state = new_state.strip().lower().replace(" ", "_")
    if new_state not in WORKFLOW_STATES:
        raise ValueError(f"Unknown workflow state: {new_state}")

    initialize_database(db_path)
    with get_connection(db_path) as connection:
        row = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        if not row:
            raise ValueError(f"Document {document_id} not found")

        current_state = row["workflow_state"] or "registered"
        allowed = ALLOWED_TRANSITIONS.get(current_state, set())
        if enforce_transition and new_state != current_state and new_state not in allowed:
            raise ValueError(f"Invalid workflow transition from {current_state} to {new_state}")

        action = action or f"move_to_{new_state}"
        connection.execute(
            """
            UPDATE documents
            SET workflow_state = ?, last_workflow_action = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_state, action, document_id),
        )
        connection.execute(
            """
            INSERT INTO workflow_history (document_id, from_state, to_state, action, user, comment)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, current_state, new_state, action, user, comment),
        )
        connection.commit()
        updated = connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone()
        return row_to_dict(updated)


def apply_review_workflow(
    document_id: int,
    review_report: dict[str, Any],
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Set the workflow state based on a review report result."""
    status = (review_report.get("validation_status") or "Needs Review").lower()
    if status == "pass":
        target_state = "approved"
        comment = "Document passed validation and review."
    elif status == "fail":
        target_state = "rejected"
        comment = "Document failed validation and should not be submitted."
    else:
        target_state = "needs_revision"
        comment = "Document needs revision before approval."

    try:
        update_workflow_state(
            document_id,
            "under_review",
            action="review_started",
            comment="Automated review started.",
            db_path=db_path,
            enforce_transition=False,
        )
    except ValueError:
        pass

    return update_workflow_state(
        document_id,
        target_state,
        action="automated_review_completed",
        comment=comment,
        db_path=db_path,
        enforce_transition=False,
    )


def get_workflow_summary(db_path: str | Path = DATABASE_PATH) -> dict[str, int]:
    initialize_database(db_path)
    summary = {state: 0 for state in WORKFLOW_STATES}
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT COALESCE(workflow_state, 'registered') AS workflow_state, COUNT(*) AS count
            FROM documents
            GROUP BY COALESCE(workflow_state, 'registered')
            """
        ).fetchall()
    for row in rows:
        summary[row["workflow_state"]] = int(row["count"])
    return summary


def get_document_workflow(document_id: int, db_path: str | Path = DATABASE_PATH) -> dict[str, Any]:
    row = _get_document_row(document_id, db_path=db_path)
    if not row:
        raise ValueError(f"Document {document_id} not found")
    document = row_to_dict(row)
    return {
        "document_id": document_id,
        "current_state": document.get("workflow_state", "registered"),
        "last_workflow_action": document.get("last_workflow_action"),
        "history": get_workflow_history(document_id, db_path=db_path),
    }
