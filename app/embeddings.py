"""Small local embedding engine for semantic document search.

This project does not use paid AI services.  The embedding is a deterministic
sparse vector built from document terms, construction keywords, and simple
synonym expansion.  It is enough to demonstrate semantic search locally.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "it", "of", "on", "or", "project", "show", "the", "this", "to",
    "with", "all", "me", "find", "give", "list", "documents", "document",
}

SYNONYMS = {
    "drawing": ["plan", "layout", "elevation", "section", "dwg", "architectural"],
    "drawings": ["drawing", "plan", "layout", "elevation", "section"],
    "specification": ["standard", "requirement", "technical", "compliance"],
    "method": ["procedure", "sequence", "installation", "work"],
    "statement": ["procedure", "method"],
    "material": ["submittal", "product", "manufacturer", "supplier"],
    "submittal": ["material", "approval", "product", "datasheet"],
    "shop": ["fabrication", "coordination", "installation"],
    "inspection": ["qa", "qc", "checklist", "quality", "site"],
    "report": ["inspection", "result", "record"],
    "contract": ["agreement", "terms", "payment", "obligations"],
    "meeting": ["minutes", "agenda", "attendees", "actions"],
    "minutes": ["meeting", "agenda", "action", "discussion"],
    "rfi": ["request", "information", "clarification", "query", "reply"],
    "query": ["rfi", "clarification", "question"],
    "architectural": ["architecture", "floor", "finishes", "drawing"],
    "structural": ["structure", "concrete", "steel", "rebar"],
    "mechanical": ["hvac", "plumbing", "duct", "chilled"],
    "electrical": ["lighting", "power", "cable", "lowcurrent"],
    "civil": ["road", "drainage", "earthwork", "utilities"],
}


def tokenize(text: str) -> list[str]:
    """Convert text to useful search tokens."""
    raw_tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    tokens: list[str] = []
    for token in raw_tokens:
        if len(token) <= 1 or token in STOP_WORDS:
            continue
        # Very small normalization to keep the project simple.
        if token.endswith("s") and len(token) > 4:
            token = token[:-1]
        tokens.append(token)
    return tokens


def _add_synonyms(tokens: Iterable[str]) -> list[str]:
    expanded: list[str] = []
    for token in tokens:
        expanded.append(token)
        expanded.extend(SYNONYMS.get(token, []))
    return expanded


def create_embedding(text: str) -> dict[str, float]:
    """Create a normalized sparse embedding vector."""
    tokens = tokenize(text)
    expanded_tokens = _add_synonyms(tokens)

    # Add simple bigrams because construction document types often use two words.
    bigrams = [f"{tokens[i]}_{tokens[i + 1]}" for i in range(len(tokens) - 1)]
    counts = Counter(expanded_tokens + bigrams)

    if not counts:
        return {}

    # Log weighting prevents very common words from dominating.
    weighted = {term: 1.0 + math.log(freq) for term, freq in counts.items()}
    norm = math.sqrt(sum(value * value for value in weighted.values()))
    if norm == 0:
        return {}
    return {term: round(value / norm, 6) for term, value in weighted.items()}


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    """Calculate cosine similarity between two sparse vectors."""
    if not left or not right:
        return 0.0

    if len(left) > len(right):
        left, right = right, left

    score = sum(value * right.get(term, 0.0) for term, value in left.items())
    return round(score, 4)
