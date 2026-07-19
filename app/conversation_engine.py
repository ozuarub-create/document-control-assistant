"""Conversational document question answering with hybrid retrieval and citations.

The implementation is local and deterministic.  It combines metadata matching,
term overlap, sparse semantic embeddings, relationship expansion, and recent
conversation context.  Answers are extractive and every supported statement is
linked to a structured source citation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.conversation_repository import (
    create_conversation_session,
    get_conversation_history,
    save_conversation_message,
)
from app.database import DATABASE_PATH, get_connection, initialize_database
from app.embeddings import cosine_similarity, create_embedding, tokenize
from app.relationship_engine import DOCUMENT_IDENTIFIER_RE, extract_document_identifiers, normalize_identifier
from app.relationship_repository import get_related_documents, list_action_items
from app.repository import get_document, row_to_dict

FOLLOW_UP_RE = re.compile(
    r"^(?:and\b|also\b|what about\b|how about\b|who\b|when\b|where\b|why\b|"
    r"what is it\b|what are they\b|is it\b|does it\b|their\b|its\b)",
    re.IGNORECASE,
)
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|[\r\n]+")
WORD_RE = re.compile(r"[a-z0-9]{2,}")

TYPE_ALIASES = {
    "drawing": "Drawing",
    "drawings": "Drawing",
    "plan": "Drawing",
    "plans": "Drawing",
    "specification": "Specification",
    "specifications": "Specification",
    "spec": "Specification",
    "specs": "Specification",
    "method statement": "Method Statement",
    "method statements": "Method Statement",
    "material submittal": "Material Submittal",
    "material submittals": "Material Submittal",
    "shop drawing": "Shop Drawing",
    "shop drawings": "Shop Drawing",
    "inspection report": "Inspection Report",
    "inspection reports": "Inspection Report",
    "contract": "Contract",
    "contracts": "Contract",
    "meeting minutes": "Meeting Minutes",
    "minutes": "Meeting Minutes",
    "rfi": "RFI",
    "rfis": "RFI",
}

METADATA_FIELDS = {
    "revision": ("revision_number", "revision"),
    "date": ("submission_date", "submission date"),
    "submitted": ("submission_date", "submission date"),
    "contractor": ("contractor", "contractor"),
    "consultant": ("consultant", "consultant"),
    "discipline": ("discipline", "discipline"),
    "project": ("project_name", "project"),
    "status": ("workflow_state", "workflow status"),
    "version": ("version", "version"),
    "title": ("document_title", "title"),
    "type": ("document_type", "document type"),
}

INSUFFICIENT_ANSWER = (
    "I could not find enough information in the registered project documents to answer "
    "that question. Try mentioning a document number, title, project, discipline, or document type."
)


def get_conversation_capabilities() -> dict[str, Any]:
    return {
        "retrieval": [
            "metadata and exact-reference matching",
            "semantic embedding similarity",
            "keyword and phrase overlap",
            "document relationship expansion",
            "conversation-context boosting",
        ],
        "supports_multi_document_questions": True,
        "supports_follow_up_questions": True,
        "citations_returned_with_answers": True,
        "insufficient_information_policy": "Do not invent facts; return a clear insufficient-information response.",
    }


def _all_documents(db_path: str | Path, latest_only: bool = True) -> list[dict[str, Any]]:
    initialize_database(db_path)
    sql = "SELECT * FROM documents"
    if latest_only:
        sql += " WHERE is_latest = 1"
    sql += " ORDER BY id DESC"
    with get_connection(db_path) as connection:
        rows = connection.execute(sql).fetchall()
    return [row_to_dict(row, include_text=True, include_embedding=True) for row in rows]


def _history_context(history: list[dict[str, Any]]) -> tuple[list[str], list[int]]:
    previous_questions: list[str] = []
    document_ids: list[int] = []
    for message in history[-8:]:
        if message.get("role") == "user":
            previous_questions.append(str(message.get("content") or ""))
        if message.get("role") == "assistant":
            metadata = message.get("metadata") or {}
            for document_id in metadata.get("cited_document_ids", []):
                try:
                    value = int(document_id)
                except (TypeError, ValueError):
                    continue
                if value not in document_ids:
                    document_ids.append(value)
    return previous_questions[-2:], document_ids[-8:]


def _is_follow_up(question: str) -> bool:
    stripped = question.strip()
    return bool(FOLLOW_UP_RE.search(stripped)) or len(stripped.split()) <= 6 and any(
        token in stripped.lower().split()
        for token in {"it", "they", "them", "that", "those", "its", "their"}
    )


def _contextualize_question(question: str, history: list[dict[str, Any]]) -> tuple[str, list[int], bool]:
    previous_questions, context_document_ids = _history_context(history)
    follow_up = bool(history) and _is_follow_up(question)
    if follow_up and previous_questions:
        contextualized = f"Previous question: {previous_questions[-1]}\nFollow-up question: {question}"
    else:
        contextualized = question
    return contextualized, context_document_ids, follow_up


def _query_identifiers(text: str) -> set[str]:
    return {normalize_identifier(match.group(0)) for match in DOCUMENT_IDENTIFIER_RE.finditer(text or "")}


def _type_hint(question: str) -> str | None:
    lowered = question.lower()
    for alias, document_type in sorted(TYPE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias in lowered:
            return document_type
    return None


def _lexical_score(query_terms: set[str], document: dict[str, Any]) -> float:
    if not query_terms:
        return 0.0
    title_text = " ".join(
        str(document.get(field) or "")
        for field in ("filename", "document_title", "document_type", "project_name", "discipline")
    ).lower()
    content_text = str(document.get("content_text") or document.get("text_preview") or "").lower()
    title_hits = sum(1 for term in query_terms if term in title_text)
    content_hits = sum(1 for term in query_terms if term in content_text)
    weighted_hits = title_hits * 2.0 + content_hits
    return min(1.0, weighted_hits / max(2.0, len(query_terms) * 1.6))


def _identifier_score(query_identifiers: set[str], document: dict[str, Any]) -> float:
    if not query_identifiers:
        return 0.0
    searchable = "\n".join(
        str(document.get(field) or "")
        for field in ("filename", "document_title", "content_text", "text_preview")
    )
    document_identifiers = _query_identifiers(searchable)
    normalized_searchable = normalize_identifier(searchable[:500])
    for identifier in query_identifiers:
        if identifier in document_identifiers or identifier in normalized_searchable:
            return 1.0
    return 0.0


def _hybrid_retrieve(
    question: str,
    context_document_ids: list[int],
    limit: int,
    latest_only: bool,
    db_path: str | Path,
) -> list[dict[str, Any]]:
    documents = _all_documents(db_path, latest_only=latest_only)
    if not documents:
        return []

    query_embedding = create_embedding(question)
    query_terms = set(tokenize(question)) | set(WORD_RE.findall(question.lower()))
    query_identifiers = _query_identifiers(question)
    document_type_hint = _type_hint(question)

    ranked: dict[int, dict[str, Any]] = {}
    for document in documents:
        semantic = cosine_similarity(query_embedding, document.get("embedding") or {})
        lexical = _lexical_score(query_terms, document)
        identifier = _identifier_score(query_identifiers, document)
        context = 1.0 if int(document["id"]) in context_document_ids else 0.0
        type_match = 1.0 if document_type_hint and document.get("document_type") == document_type_hint else 0.0

        score = min(
            1.0,
            semantic * 0.42
            + lexical * 0.28
            + identifier * 0.22
            + context * 0.18
            + type_match * 0.08,
        )
        if identifier:
            score = max(score, 0.92)
        if context and _is_follow_up(question):
            score = max(score, 0.58)

        ranked[int(document["id"])] = {
            "document": document,
            "score": round(score, 4),
            "retrieval_reasons": {
                "semantic": semantic,
                "lexical": round(lexical, 4),
                "exact_reference": bool(identifier),
                "conversation_context": bool(context),
                "document_type_match": bool(type_match),
            },
        }

    initial = sorted(ranked.values(), key=lambda item: item["score"], reverse=True)
    seed_items = [item for item in initial if item["score"] >= 0.05][: max(4, limit)]

    # Expand highly relevant documents through the Week 20 relationship graph.
    for seed in seed_items[:4]:
        seed_id = int(seed["document"]["id"])
        try:
            related = get_related_documents(seed_id, direction="both", limit=20, db_path=db_path)
        except (ValueError, TypeError):
            related = []
        for relation in related:
            related_document = relation.get("related_document") or {}
            related_id = related_document.get("id")
            if not related_id:
                continue
            full_document = get_document(int(related_id), db_path=db_path)
            if not full_document:
                continue
            relationship_score = max(0.15, float(relation.get("confidence_score") or 0) * 0.72)
            candidate_score = min(0.96, seed["score"] * 0.76 + relationship_score * 0.24)
            existing = ranked.get(int(related_id))
            if not existing or candidate_score > existing["score"]:
                ranked[int(related_id)] = {
                    "document": full_document,
                    "score": round(candidate_score, 4),
                    "retrieval_reasons": {
                        "semantic": existing["retrieval_reasons"].get("semantic", 0) if existing else 0,
                        "lexical": existing["retrieval_reasons"].get("lexical", 0) if existing else 0,
                        "exact_reference": False,
                        "conversation_context": int(related_id) in context_document_ids,
                        "document_type_match": False,
                        "relationship_expansion": relation.get("relationship_type"),
                        "relationship_reference": relation.get("reference_text"),
                    },
                }

    results = sorted(ranked.values(), key=lambda item: item["score"], reverse=True)
    return [item for item in results if item["score"] >= 0.045][: max(limit, 1)]


def _best_excerpt(document: dict[str, Any], question: str, maximum: int = 280) -> str:
    text = str(document.get("content_text") or document.get("text_preview") or "").strip()
    if not text:
        return (
            f"{document.get('document_title') or document.get('filename')} is a "
            f"{document.get('document_type')} document for {document.get('project_name') or 'the project'}."
        )

    query_terms = set(tokenize(question)) | set(WORD_RE.findall(question.lower()))
    sentences = [re.sub(r"\s+", " ", item).strip(" -") for item in SENTENCE_SPLIT_RE.split(text)]
    sentences = [item for item in sentences if len(item) >= 18]
    if not sentences:
        return re.sub(r"\s+", " ", text)[:maximum].strip()

    def sentence_score(sentence: str) -> tuple[int, int]:
        lowered = sentence.lower()
        hits = sum(1 for term in query_terms if term in lowered)
        identifier_bonus = 3 if _query_identifiers(sentence) & _query_identifiers(question) else 0
        return hits + identifier_bonus, min(len(sentence), maximum)

    best = max(sentences, key=sentence_score)
    if len(best) > maximum:
        best = best[: maximum - 3].rstrip() + "..."
    return best


def _citation(
    document: dict[str, Any],
    citation_number: int,
    excerpt: str,
    score: float,
    retrieval_reasons: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "citation_id": f"S{citation_number}",
        "document_id": document.get("id"),
        "filename": document.get("filename"),
        "document_title": document.get("document_title"),
        "document_type": document.get("document_type"),
        "project_name": document.get("project_name"),
        "revision_number": document.get("revision_number"),
        "source_excerpt": excerpt,
        "relevance_score": round(float(score), 4),
        "retrieval_reasons": retrieval_reasons or {},
    }


def _selected_metadata_fields(question: str) -> list[tuple[str, str]]:
    lowered = question.lower()
    selected: list[tuple[str, str]] = []
    for keyword, field in METADATA_FIELDS.items():
        if keyword in lowered and field not in selected:
            selected.append(field)
    return selected


def _relationship_answer(
    ranked: list[dict[str, Any]],
    question: str,
    db_path: str | Path,
) -> tuple[str, list[dict[str, Any]]] | None:
    lowered = question.lower()
    if not any(term in lowered for term in ("reference", "references", "related", "link", "linked")):
        return None

    query_identifiers = _query_identifiers(question)
    candidates = ranked[:6]
    if query_identifiers:
        exact_sources = [
            item
            for item in candidates
            if query_identifiers & {normalize_identifier(value) for value in extract_document_identifiers(item["document"])}
        ]
        remaining = [item for item in candidates if item not in exact_sources]
        candidates = exact_sources + remaining

    for item in candidates:
        document = item["document"]
        try:
            related = get_related_documents(int(document["id"]), direction="outgoing", limit=10, db_path=db_path)
        except (TypeError, ValueError):
            related = []
        if not related:
            continue

        citations: list[dict[str, Any]] = []
        parts: list[str] = []
        source_excerpt = str(related[0].get("reference_text") or _best_excerpt(document, question))
        citations.append(_citation(document, 1, source_excerpt, item["score"], item.get("retrieval_reasons")))

        for relation in related[:4]:
            target = relation.get("related_document") or {}
            if not target:
                continue
            target_full = get_document(int(target["id"]), db_path=db_path) or target
            citation_number = len(citations) + 1
            citations.append(
                _citation(
                    target_full,
                    citation_number,
                    _best_excerpt(target_full, question),
                    float(relation.get("confidence_score") or item["score"]),
                    {"relationship_type": relation.get("relationship_type")},
                )
            )
            parts.append(
                f"{target_full.get('document_title') or target_full.get('filename')} "
                f"({target_full.get('document_type')}) [S{citation_number}]"
            )

        if parts:
            source_name = document.get("document_title") or document.get("filename")
            answer = f"{source_name} is linked to " + "; ".join(parts) + " [S1]."
            return answer, citations
    return None


def _action_item_answer(
    ranked: list[dict[str, Any]],
    question: str,
    db_path: str | Path,
) -> tuple[str, list[dict[str, Any]]] | None:
    lowered = question.lower()
    if not any(term in lowered for term in ("action", "owner", "responsible", "due", "when is it", "status")):
        return None

    for item in ranked[:6]:
        document = item["document"]
        if document.get("document_type") != "Meeting Minutes":
            continue
        actions = list_action_items(meeting_document_id=int(document["id"]), limit=10, db_path=db_path)
        if not actions:
            continue
        citations: list[dict[str, Any]] = []
        statements: list[str] = []
        for action in actions[:3]:
            excerpt = str(action.get("reference_text") or action.get("action_text") or "")
            citation_number = len(citations) + 1
            citations.append(
                _citation(document, citation_number, excerpt, item["score"], item.get("retrieval_reasons"))
            )
            statements.append(
                f"The action is “{action.get('action_text')}”; owner: "
                f"{action.get('owner') or 'not stated'}; due: {action.get('due_date') or 'not stated'}; "
                f"status: {action.get('status') or 'not stated'} [S{citation_number}]."
            )
        return " ".join(statements), citations
    return None


def _metadata_answer(
    ranked: list[dict[str, Any]],
    question: str,
) -> tuple[str, list[dict[str, Any]]] | None:
    fields = _selected_metadata_fields(question)
    if not fields:
        return None

    citations: list[dict[str, Any]] = []
    statements: list[str] = []
    for item in ranked[:3]:
        document = item["document"]
        values = [f"{label}: {document.get(field) or 'not stated'}" for field, label in fields]
        citation_number = len(citations) + 1
        excerpt = "; ".join(values)
        citations.append(_citation(document, citation_number, excerpt, item["score"], item.get("retrieval_reasons")))
        statements.append(
            f"{document.get('document_title') or document.get('filename')}: {excerpt} [S{citation_number}]."
        )
    return " ".join(statements), citations


def _general_answer(
    ranked: list[dict[str, Any]],
    question: str,
) -> tuple[str, list[dict[str, Any]]]:
    lowered = question.lower()
    multi_document = any(
        term in lowered
        for term in ("compare", "across", "both", "multiple", "documents", "summarize", "what do")
    )
    source_count = min(len(ranked), 4 if multi_document else 2)
    citations: list[dict[str, Any]] = []
    statements: list[str] = []

    for item in ranked[:source_count]:
        document = item["document"]
        excerpt = _best_excerpt(document, question)
        citation_number = len(citations) + 1
        citations.append(_citation(document, citation_number, excerpt, item["score"], item.get("retrieval_reasons")))
        statements.append(
            f"{document.get('document_title') or document.get('filename')} "
            f"({document.get('document_type')}): {excerpt} [S{citation_number}]."
        )
    return " ".join(statements), citations


def _evidence_support_ratio(question: str, ranked: list[dict[str, Any]]) -> float:
    """Estimate whether retrieved text actually contains the question's specific concepts."""
    generic = {
        "what", "which", "where", "when", "who", "why", "how", "does", "document",
        "documents", "project", "information", "tell", "about", "show", "find", "give",
        "latest", "current", "final", "approved",
    }
    terms = {term for term in tokenize(question) if term not in generic and len(term) >= 3}
    terms -= {"rfi", "mom", "dwg", "spec"}
    if not terms:
        return 1.0

    evidence_text = " ".join(
        " ".join(
            str(item["document"].get(field) or "")
            for field in (
                "filename", "document_title", "document_type", "project_name", "contractor",
                "consultant", "discipline", "revision_number", "submission_date", "workflow_state",
                "content_text", "text_preview",
            )
        )
        for item in ranked[:5]
    ).lower()
    matched = sum(1 for term in terms if term in evidence_text)
    return matched / max(1, len(terms))


def answer_document_question(
    question: str,
    session_id: str | None = None,
    limit: int = 6,
    latest_only: bool = True,
    db_path: str | Path = DATABASE_PATH,
) -> dict[str, Any]:
    """Answer a question using registered documents, conversation history, and citations."""
    question = (question or "").strip()
    if not question:
        raise ValueError("question is required")

    session = create_conversation_session(
        session_id=session_id,
        title=question[:80],
        db_path=db_path,
    )
    session_id = str(session["id"])
    history = get_conversation_history(session_id, limit=30, db_path=db_path)
    contextualized_question, context_document_ids, follow_up = _contextualize_question(question, history)

    save_conversation_message(session_id, "user", question, db_path=db_path)
    ranked = _hybrid_retrieve(
        contextualized_question,
        context_document_ids=context_document_ids,
        limit=max(2, limit),
        latest_only=latest_only,
        db_path=db_path,
    )

    top_score = ranked[0]["score"] if ranked else 0.0
    identifiers = _query_identifiers(contextualized_question)
    threshold = 0.045 if identifiers or context_document_ids else 0.075
    evidence_support = _evidence_support_ratio(contextualized_question, ranked) if ranked else 0.0
    unsupported_specific_question = (
        not identifiers
        and not follow_up
        and len(WORD_RE.findall(contextualized_question.lower())) >= 4
        and evidence_support < 0.34
    )

    if not ranked or top_score < threshold or unsupported_specific_question:
        answer = INSUFFICIENT_ANSWER
        citations: list[dict[str, Any]] = []
        status = "insufficient_information"
    else:
        composed = (
            _action_item_answer(ranked, contextualized_question, db_path)
            or _relationship_answer(ranked, contextualized_question, db_path)
            or _metadata_answer(ranked, contextualized_question)
        )
        if composed:
            answer, citations = composed
        else:
            answer, citations = _general_answer(ranked, contextualized_question)
        status = "answered" if citations else "insufficient_information"
        if not citations:
            answer = INSUFFICIENT_ANSWER

    cited_document_ids = [int(item["document_id"]) for item in citations if item.get("document_id") is not None]
    retrieval_summary = {
        "method": "hybrid_metadata_semantic_relationship_context",
        "documents_considered": len(_all_documents(db_path, latest_only=latest_only)),
        "documents_retrieved": len(ranked),
        "sources_cited": len(citations),
        "top_relevance_score": round(top_score, 4),
        "evidence_support_ratio": round(evidence_support, 4),
        "follow_up_detected": follow_up,
        "context_document_ids": context_document_ids,
    }
    assistant_metadata = {
        "status": status,
        "cited_document_ids": cited_document_ids,
        "contextualized_question": contextualized_question,
        "retrieval": retrieval_summary,
    }
    save_conversation_message(
        session_id,
        "assistant",
        answer,
        citations=citations,
        metadata=assistant_metadata,
        db_path=db_path,
    )

    return {
        "session_id": session_id,
        "question": question,
        "contextualized_question": contextualized_question,
        "answer": answer,
        "status": status,
        "insufficient_information": status == "insufficient_information",
        "citations": citations,
        "retrieval": retrieval_summary,
        "history_used": follow_up,
    }
