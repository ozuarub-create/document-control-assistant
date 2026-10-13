import json
from datetime import datetime, timezone
from pathlib import Path

class AuditLogger:
    def __init__(self, path="results/week28_audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event, task_id, details):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "task_id": task_id,
            "details": details,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        return entry
