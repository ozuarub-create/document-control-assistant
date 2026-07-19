"""SQLite repository for document relationships and meeting action items."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.database import DATABASE_PATH, get_connection, initialize_database
from app.repository import row_to_dict


def clear_relationship_data(db_path: str | Path = DATABASE_PATH) -> None:
    """Delete generated relationships and action items without removing documents."""
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute("DELETE FROM document_relationships")
        connection.execute("DELETE FROM document_action_items")
        connection.commit()


def save_relationship(
    source_document_id: int,
    target_document_id: int,
    relationship_type: str,
    reference_text: str | None,
    confidence_score: float,
    detected_by: str,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Create or update one directed document relationship."""
    initialize_database(db_path)
    if source_document_id == target_document_id:
        raise ValueError("A document cannot be related to itself.")

    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO document_relationships (
                source_document_id, target_document_id, relationship_type,
                reference_text, confidence_score, detected_by
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_document_id, target_document_id, relationship_type)
            DO UPDATE SET
                reference_text = excluded.reference_text,
                confidence_score = excluded.confidence_score,
                detected_by = excluded.detected_by,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                source_document_id,
                target_document_id,
                relationship_type,
                reference_text,
                round(float(confidence_score), 3),
                detected_by,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT * FROM document_relationships
            WHERE source_document_id = ? AND target_document_id = ?
              AND relationship_type = ?
            """,
            (source_document_id, target_document_id, relationship_type),
        ).fetchone()
        return dict(row)


def save_action_item(
    meeting_document_id: int,
    action_text: str,
    owner: str | None = None,
    due_date: str | None = None,
    status: str = "Open",
    related_document_id: int | None = None,
    reference_text: str | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Store one action item extracted from meeting minutes."""
    initialize_database(db_path)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO document_action_items (
                meeting_document_id, action_text, owner, due_date, status,
                related_document_id, reference_text
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(meeting_document_id, action_text)
            DO UPDATE SET
                owner = excluded.owner,
                due_date = excluded.due_date,
                status = excluded.status,
                related_document_id = excluded.related_document_id,
                reference_text = excluded.reference_text
            """,
            (
                meeting_document_id,
                action_text.strip(),
                owner,
                due_date,
                status,
                related_document_id,
                reference_text,
            ),
        )
        connection.commit()
        row = connection.execute(
            """
            SELECT * FROM document_action_items
            WHERE meeting_document_id = ? AND action_text = ?
            """,
            (meeting_document_id, action_text.strip()),
        ).fetchone()
        return dict(row)


def list_relationships(
    limit: int = 200,
    relationship_type: str | None = None,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """List relationship edges with source and target document labels."""
    initialize_database(db_path)
    where = ""
    params: list[Any] = []
    if relationship_type:
        where = "WHERE LOWER(r.relationship_type) = ?"
        params.append(relationship_type.lower())
    params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
                r.*,
                s.filename AS source_filename,
                s.document_title AS source_title,
                s.document_type AS source_type,
                t.filename AS target_filename,
                t.document_title AS target_title,
                t.document_type AS target_type
            FROM document_relationships r
            JOIN documents s ON s.id = r.source_document_id
            JOIN documents t ON t.id = r.target_document_id
            {where}
            ORDER BY r.confidence_score DESC, r.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


def list_action_items(
    meeting_document_id: int | None = None,
    limit: int = 200,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """List extracted action items, optionally for one meeting document."""
    initialize_database(db_path)
    where = ""
    params: list[Any] = []
    if meeting_document_id is not None:
        where = "WHERE a.meeting_document_id = ?"
        params.append(meeting_document_id)
    params.append(limit)

    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT
                a.*,
                m.filename AS meeting_filename,
                m.document_title AS meeting_title,
                d.filename AS related_filename,
                d.document_title AS related_title,
                d.document_type AS related_type
            FROM document_action_items a
            JOIN documents m ON m.id = a.meeting_document_id
            LEFT JOIN documents d ON d.id = a.related_document_id
            {where}
            ORDER BY a.id ASC
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(row) for row in rows]


def get_related_documents(
    document_id: int,
    direction: str = "both",
    relationship_type: str | None = None,
    limit: int = 100,
    db_path: str | Path = DATABASE_PATH,
) -> list[dict[str, Any]]:
    """Return incoming and/or outgoing related documents for one document."""
    initialize_database(db_path)
    direction = direction.lower().strip()
    if direction not in {"both", "incoming", "outgoing"}:
        raise ValueError("direction must be both, incoming, or outgoing")

    relationship_filter = ""
    rel_params: list[Any] = []
    if relationship_type:
        relationship_filter = " AND LOWER(r.relationship_type) = ?"
        rel_params.append(relationship_type.lower())

    results: list[dict[str, Any]] = []
    with get_connection(db_path) as connection:
        exists = connection.execute("SELECT 1 FROM documents WHERE id = ?", (document_id,)).fetchone()
        if not exists:
            return []

        if direction in {"both", "outgoing"}:
            rows = connection.execute(
                f"""
                SELECT
                    r.id AS relationship_id,
                    r.source_document_id,
                    r.target_document_id,
                    r.relationship_type,
                    r.reference_text,
                    r.confidence_score,
                    r.detected_by,
                    r.created_at AS relationship_created_at,
                    d.*
                FROM document_relationships r
                JOIN documents d ON d.id = r.target_document_id
                WHERE r.source_document_id = ? {relationship_filter}
                ORDER BY r.confidence_score DESC, r.id ASC
                LIMIT ?
                """,
                [document_id, *rel_params, limit],
            ).fetchall()
            for row in rows:
                raw = dict(row)
                relation = {
                    "relationship_id": raw.pop("relationship_id"),
                    "direction": "outgoing",
                    "relationship_type": raw.pop("relationship_type"),
                    "reference_text": raw.pop("reference_text"),
                    "confidence_score": raw.pop("confidence_score"),
                    "detected_by": raw.pop("detected_by"),
                    "source_document_id": raw.pop("source_document_id"),
                    "target_document_id": raw.pop("target_document_id"),
                    "created_at": raw.pop("relationship_created_at"),
                }
                relation["related_document"] = row_to_dict(raw)
                results.append(relation)

        if direction in {"both", "incoming"}:
            rows = connection.execute(
                f"""
                SELECT
                    r.id AS relationship_id,
                    r.source_document_id,
                    r.target_document_id,
                    r.relationship_type,
                    r.reference_text,
                    r.confidence_score,
                    r.detected_by,
                    r.created_at AS relationship_created_at,
                    d.*
                FROM document_relationships r
                JOIN documents d ON d.id = r.source_document_id
                WHERE r.target_document_id = ? {relationship_filter}
                ORDER BY r.confidence_score DESC, r.id ASC
                LIMIT ?
                """,
                [document_id, *rel_params, limit],
            ).fetchall()
            for row in rows:
                raw = dict(row)
                relation = {
                    "relationship_id": raw.pop("relationship_id"),
                    "direction": "incoming",
                    "relationship_type": raw.pop("relationship_type"),
                    "reference_text": raw.pop("reference_text"),
                    "confidence_score": raw.pop("confidence_score"),
                    "detected_by": raw.pop("detected_by"),
                    "source_document_id": raw.pop("source_document_id"),
                    "target_document_id": raw.pop("target_document_id"),
                    "created_at": raw.pop("relationship_created_at"),
                }
                relation["related_document"] = row_to_dict(raw)
                results.append(relation)

    results.sort(key=lambda item: (-float(item["confidence_score"]), item["relationship_id"]))
    return results[:limit]


def get_graph_data(
    limit: int = 300,
    include_action_items: bool = True,
    include_isolated: bool = False,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Create JSON-ready graph nodes and edges for the relationship viewer."""
    initialize_database(db_path)
    relationships = list_relationships(limit=limit, db_path=db_path)
    action_items = list_action_items(limit=limit, db_path=db_path) if include_action_items else []

    document_ids: set[int] = set()
    for item in relationships:
        document_ids.add(int(item["source_document_id"]))
        document_ids.add(int(item["target_document_id"]))
    for item in action_items:
        document_ids.add(int(item["meeting_document_id"]))
        if item.get("related_document_id"):
            document_ids.add(int(item["related_document_id"]))

    with get_connection(db_path) as connection:
        if include_isolated:
            rows = connection.execute(
                "SELECT * FROM documents WHERE is_latest = 1 ORDER BY id ASC LIMIT ?",
                (limit,),
            ).fetchall()
        elif document_ids:
            placeholders = ",".join("?" for _ in document_ids)
            rows = connection.execute(
                f"SELECT * FROM documents WHERE id IN ({placeholders}) ORDER BY id ASC",
                list(sorted(document_ids)),
            ).fetchall()
        else:
            rows = []

    nodes: list[dict[str, Any]] = []
    for row in rows:
        doc = row_to_dict(row)
        nodes.append(
            {
                "id": f"doc-{doc['id']}",
                "entity_type": "document",
                "document_id": doc["id"],
                "label": doc.get("document_title") or doc.get("filename"),
                "filename": doc.get("filename"),
                "group": doc.get("document_type") or "Unknown",
                "project_name": doc.get("project_name"),
                "discipline": doc.get("discipline"),
                "workflow_state": doc.get("workflow_state"),
            }
        )

    edges: list[dict[str, Any]] = []
    for item in relationships:
        edges.append(
            {
                "id": f"rel-{item['id']}",
                "source": f"doc-{item['source_document_id']}",
                "target": f"doc-{item['target_document_id']}",
                "label": item["relationship_type"],
                "confidence_score": item["confidence_score"],
                "detected_by": item["detected_by"],
                "reference_text": item.get("reference_text"),
            }
        )

    if include_action_items:
        for item in action_items:
            action_id = f"action-{item['id']}"
            nodes.append(
                {
                    "id": action_id,
                    "entity_type": "action_item",
                    "action_item_id": item["id"],
                    "label": item["action_text"],
                    "group": "Action Item",
                    "owner": item.get("owner"),
                    "due_date": item.get("due_date"),
                    "status": item.get("status"),
                }
            )
            edges.append(
                {
                    "id": f"meeting-action-{item['id']}",
                    "source": f"doc-{item['meeting_document_id']}",
                    "target": action_id,
                    "label": "contains_action_item",
                    "confidence_score": 1.0,
                    "detected_by": "action_item_extraction",
                    "reference_text": item.get("reference_text"),
                }
            )
            if item.get("related_document_id"):
                edges.append(
                    {
                        "id": f"action-doc-{item['id']}",
                        "source": action_id,
                        "target": f"doc-{item['related_document_id']}",
                        "label": "action_references_document",
                        "confidence_score": 0.98,
                        "detected_by": "identifier_match",
                        "reference_text": item.get("reference_text"),
                    }
                )

    type_counts: dict[str, int] = {}
    for edge in edges:
        type_counts[edge["label"]] = type_counts.get(edge["label"], 0) + 1

    return {
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "document_nodes": sum(1 for node in nodes if node["entity_type"] == "document"),
            "action_item_nodes": sum(1 for node in nodes if node["entity_type"] == "action_item"),
            "relationship_types": type_counts,
        },
        "nodes": nodes,
        "edges": edges,
    }
