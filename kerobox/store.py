"""Durable storage for memory items.

JSON on disk, written atomically (temp file + os.replace) so an interrupted
write never leaves a half-file. If the existing file is unreadable, it is
*quarantined* (renamed aside) rather than overwritten — you keep the corrupt
data for inspection instead of silently losing it.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from typing import Iterator, Optional

from .types import MemoryItem


class MemoryStore:
    def __init__(self, path: Optional[str] = None) -> None:
        self.path = path
        self._items: dict[str, MemoryItem] = {}
        if path and os.path.exists(path):
            self._load()

    # -- CRUD -------------------------------------------------------------
    def put(self, item: MemoryItem) -> None:
        existing = self._items.get(item.key)
        if existing is not None:
            item.created_at = existing.created_at  # preserve original creation
        item.updated_at = time.time()
        self._items[item.key] = item

    def get(self, key: str) -> Optional[MemoryItem]:
        return self._items.get(key)

    def delete(self, key: str) -> bool:
        return self._items.pop(key, None) is not None

    def all(self) -> list[MemoryItem]:
        return list(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[MemoryItem]:
        return iter(self._items.values())

    # -- persistence ------------------------------------------------------
    def save(self) -> None:
        if not self.path:
            return
        payload = {"version": 1, "items": [i.to_dict() for i in self._items.values()]}
        d = os.path.dirname(os.path.abspath(self.path)) or "."
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            os.replace(tmp, self.path)  # atomic
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)

    def _load(self) -> None:
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            for raw in data.get("items", []):
                item = MemoryItem.from_dict(raw)
                self._items[item.key] = item
        except (json.JSONDecodeError, OSError, KeyError, TypeError):
            self._quarantine()

    def _quarantine(self) -> None:
        """Move an unreadable state file aside so it isn't overwritten."""
        if not self.path or not os.path.exists(self.path):
            return
        bad = f"{self.path}.corrupt.{int(time.time())}"
        try:
            os.replace(self.path, bad)
        except OSError:
            pass
        self._items = {}
