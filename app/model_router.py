from __future__ import annotations
from .gateway_models import ProviderConfig

TASK_PREFERENCES = {
    'classification': {'quality': 0.55, 'cost': 0.30, 'latency': 0.15},
    'retrieval': {'quality': 0.50, 'cost': 0.20, 'latency': 0.30},
    'summarization': {'quality': 0.60, 'cost': 0.25, 'latency': 0.15},
    'reasoning': {'quality': 0.75, 'cost': 0.15, 'latency': 0.10},
}

class ModelRouter:
    def __init__(self, configs: list[ProviderConfig], default_weights: dict[str, float] | None = None):
        self.configs = [c for c in configs if c.enabled]
        self.default_weights = default_weights or {'quality': .6, 'cost': .25, 'latency': .15}

    def rank(self, task_type: str) -> list[ProviderConfig]:
        weights = TASK_PREFERENCES.get(task_type, self.default_weights)
        max_cost = max((c.input_cost_per_1k + c.output_cost_per_1k) for c in self.configs) or 1
        max_latency = max(c.latency_ms for c in self.configs) or 1
        def score(c: ProviderConfig):
            cost = c.input_cost_per_1k + c.output_cost_per_1k
            cost_score = 1 - (cost / max_cost)
            latency_score = 1 - (c.latency_ms / max_latency)
            return (weights['quality'] * c.quality + weights['cost'] * cost_score + weights['latency'] * latency_score, -c.priority)
        return sorted(self.configs, key=score, reverse=True)
