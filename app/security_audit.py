import json
from datetime import datetime, timezone
from pathlib import Path

class AuditLogger:
    def __init__(self, path: str = "results/week29_security_audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: dict) -> None:
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
