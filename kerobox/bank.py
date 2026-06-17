"""MemoryBank — the one class most users need.

Wraps the store, graph, and query engine into a single friendly API:

    bank = MemoryBank("agent-memory.json")
    bank.remember("user-tz", "Asia/Jakarta", tags=["user", "preference"])
    bank.link("user-tz", "user-locale")
    hits = bank.recall("what timezone is the user in")
    bank.save()

Persists store + graph together to one JSON file, atomically.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from typing import Any, Optional

from . import query as _q
from .graph import MemoryGraph
from .store import MemoryStore
from .types import MemoryItem, RecallResult


class MemoryBank:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self.store = MemoryStore()
        self.graph = MemoryGraph()
        if path and os.path.exists(path):
            self._load()

    # -- writing ----------------------------------------------------------
    def remember(
        self,
        key: str,
        content: Any,
        *,
        kind: str = "fact",
        confidence: float = 0.8,
        tags: Optional[list[str]] = None,
        source: str = "",
    ) -> MemoryItem:
        item = MemoryItem(
            key=key, content=content, kind=kind,
            confidence=max(0.0, min(1.0, confidence)),
            tags=tags or [], source=source,
        )
        self.store.put(item)
        return item

    def forget(self, key: str) -> bool:
        self.graph.drop_key(key)
        return self.store.delete(key)

    def link(self, src: str, dst: str, relation: str = "related") -> None:
        self.graph.link(src, dst, relation)

    # -- reading ----------------------------------------------------------
    def get(self, key: str) -> Optional[MemoryItem]:
        return self.store.get(key)

    def recall(
        self,
        query: str = "",
        *,
        tags: Optional[list[str]] = None,
        kind: Optional[str] = None,
        limit: int = 5,
        half_life_days: float = 30.0,
        now: Optional[float] = None,
    ) -> list[RecallResult]:
        return _q.search(
            self.store.all(), query=query, tags=tags, kind=kind,
            limit=limit, half_life_days=half_life_days, now=now,
        )

    def related(self, key: str, depth: int = 1) -> list[MemoryItem]:
        keys = self.graph.connected(key, depth=depth)
        return [self.store.get(k) for k in keys if self.store.get(k) is not None]

    def __len__(self) -> int:
        return len(self.store)

    # -- persistence ------------------------------------------------------
    def save(self) -> None:
        if not self.path:
            return
        payload = {
            "version": 1,
            "items": [i.to_dict() for i in self.store.all()],
            "edges": self.graph.to_list(),
        }
        d = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            os.replace(tmp, self.path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            # Reuse the store's quarantine behaviour for a corrupt bank file.
            bad = f"{self.path}.corrupt.{int(time.time())}"
            try:
                os.replace(self.path, bad)
            except OSError:
                pass
            return
        for raw in data.get("items", []):
            try:
                self.store.put(MemoryItem.from_dict(raw))
            except (KeyError, TypeError):
                continue
        self.graph.load_list(data.get("edges", []))
