from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

class DocumentRepository:
    def __init__(self, root: str | Path = "mcp_test_documents") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _docs(self) -> Iterable[Path]:
        return sorted(p for p in self.root.glob("*.json") if p.is_file())

    def load(self, doc_id: str) -> dict:
        path = self.root / f"{doc_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Document '{doc_id}' not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def search(self, query: str) -> list[dict]:
        q = query.lower().strip()
        results = []
        for p in self._docs():
            d = json.loads(p.read_text(encoding="utf-8"))
            hay = " ".join([
                d.get("id", ""), d.get("title", ""), d.get("type", ""),
                d.get("content", ""), " ".join(d.get("tags", []))
            ]).lower()
            if q in hay:
                results.append({k: d.get(k) for k in ("id","title","type","revision","status")})
        return results

    def related(self, doc_id: str) -> list[dict]:
        d = self.load(doc_id)
        rel = []
        for rid in d.get("related_ids", []):
            try:
                rd = self.load(rid)
                rel.append({k: rd.get(k) for k in ("id","title","type","revision","status")})
            except FileNotFoundError:
                pass
        return rel
