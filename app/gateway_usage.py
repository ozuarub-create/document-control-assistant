from __future__ import annotations
import json
from pathlib import Path
from threading import Lock

class UsageTracker:
    def __init__(self, path: str = 'results/gateway_usage.jsonl'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

    def record(self, event: dict) -> None:
        with self.lock:
            with self.path.open('a', encoding='utf-8') as f:
                f.write(json.dumps(event) + '\n')

    def summary(self) -> dict:
        if not self.path.exists():
            return {'requests': 0, 'input_tokens': 0, 'output_tokens': 0, 'estimated_cost': 0.0}
        rows = [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]
        return {
            'requests': len(rows),
            'input_tokens': sum(r.get('input_tokens', 0) for r in rows),
            'output_tokens': sum(r.get('output_tokens', 0) for r in rows),
            'estimated_cost': round(sum(r.get('estimated_cost', 0.0) for r in rows), 6),
        }
