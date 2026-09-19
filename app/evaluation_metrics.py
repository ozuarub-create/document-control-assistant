from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable


def exact_match(expected: str, actual: str) -> float:
    return float(expected.strip().lower() == actual.strip().lower())


def token_f1(expected: str, actual: str) -> float:
    e = expected.lower().split()
    a = actual.lower().split()
    if not e and not a:
        return 1.0
    if not e or not a:
        return 0.0
    common = 0
    used = [False] * len(a)
    for t in e:
        for i, x in enumerate(a):
            if not used[i] and x == t:
                used[i] = True
                common += 1
                break
    p = common / len(a)
    r = common / len(e)
    return 0.0 if p + r == 0 else 2 * p * r / (p + r)


def retrieval_recall(expected_ids: Iterable[str], retrieved_ids: Iterable[str]) -> float:
    expected = set(expected_ids)
    retrieved = set(retrieved_ids)
    if not expected:
        return 1.0
    return len(expected & retrieved) / len(expected)


def citation_accuracy(expected_ids: Iterable[str], cited_ids: Iterable[str]) -> float:
    expected = set(expected_ids)
    cited = set(cited_ids)
    if not cited:
        return 1.0 if not expected else 0.0
    return len(expected & cited) / len(cited)


def hallucination_rate(unsupported_claims: int, total_claims: int) -> float:
    if total_claims <= 0:
        return 0.0
    return unsupported_claims / total_claims


def field_accuracy(expected: dict, actual: dict) -> float:
    if not expected:
        return 1.0
    correct = 0
    for k, v in expected.items():
        if str(actual.get(k, '')).strip().lower() == str(v).strip().lower():
            correct += 1
    return correct / len(expected)


@dataclass
class AggregateMetrics:
    retrieval_accuracy: float
    answer_correctness: float
    citation_accuracy: float
    hallucination_rate: float
    metadata_accuracy: float
    classification_accuracy: float
    avg_latency_ms: float
    total_tokens: int
    estimated_cost_usd: float
