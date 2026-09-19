from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

class EvaluationRepository:
    def __init__(self, path='results/evaluation_history.jsonl'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, result: dict):
        record = {'timestamp': datetime.now(timezone.utc).isoformat(), **result['summary']}
        with self.path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(record) + '\n')
        return record

    def history(self):
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]
