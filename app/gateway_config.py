from __future__ import annotations
import json
from pathlib import Path
from .gateway_models import ProviderConfig

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / 'config' / 'models.json'

def load_provider_configs(path: str | Path | None = None) -> list[ProviderConfig]:
    p = Path(path) if path else DEFAULT_CONFIG
    raw = json.loads(p.read_text())
    return [ProviderConfig(**item) for item in raw['providers']]

def load_routing_weights(path: str | Path | None = None) -> dict[str, float]:
    p = Path(path) if path else DEFAULT_CONFIG
    raw = json.loads(p.read_text())
    return raw.get('routing_weights', {'quality': 0.6, 'cost': 0.25, 'latency': 0.15})
