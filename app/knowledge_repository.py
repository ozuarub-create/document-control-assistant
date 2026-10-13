from __future__ import annotations
from pathlib import Path

class KnowledgeRepository:
    def __init__(self, path: str | Path = "config/knowledge_base.txt") -> None:
        self.path = Path(path)

    def search(self, query: str) -> list[str]:
        if not self.path.exists():
            return []
        q = query.lower().strip()
        lines = [x.strip() for x in self.path.read_text(encoding="utf-8").splitlines() if x.strip()]
        tokens = [t for t in q.split() if len(t) > 2]
        ranked = []
        for line in lines:
            score = sum(1 for t in tokens if t in line.lower())
            if score:
                ranked.append((score, line))
        ranked.sort(key=lambda x: (-x[0], x[1]))
        return [line for _, line in ranked[:5]]
