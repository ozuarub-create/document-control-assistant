from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class GatewayRequest:
    task_type: str
    prompt: str
    max_tokens: int = 512
    metadata: dict[str, Any] | None = None

@dataclass
class ProviderConfig:
    name: str
    model: str
    quality: float
    latency_ms: float
    input_cost_per_1k: float
    output_cost_per_1k: float
    enabled: bool = True
    priority: int = 100

@dataclass
class GatewayResponse:
    request_id: str
    provider: str
    model: str
    output: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    latency_ms: float
    fallback_used: bool
    attempts: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
