from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class EvaluationConfig:
    name: str
    model: str
    prompt_version: str
    retrieval_k: int
    cost_per_1k_input: float
    cost_per_1k_output: float

CONFIGS = {
    'baseline': EvaluationConfig('baseline','fixture-model-a','prompt-v1',3,0.001,0.002),
    'improved': EvaluationConfig('improved','fixture-model-b','prompt-v2',5,0.0015,0.0025),
}
