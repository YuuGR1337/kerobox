"""Core data types for stored memories."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional


def _now() -> float:
    return time.time()


@dataclass
class MemoryItem:
    """A single remembered fact.

    - `key`        stable identifier (used for updates and linking)
    - `content`    the fact itself (any JSON-serializable value)
    - `kind`       free-form category ("fact", "preference", "result", ...)
    - `confidence` 0.0–1.0 belief in this memory; decays with age on recall
    - `tags`       searchable labels
    - `source`     where it came from (optional provenance)
    """

    key: str
    content: Any
    kind: str = "fact"
    confidence: float = 0.8
    tags: list[str] = field(default_factory=list)
    source: str = ""
    created_at: float = field(default_factory=_now)
    updated_at: float = field(default_factory=_now)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "content": self.content,
            "kind": self.kind,
            "confidence": self.confidence,
            "tags": self.tags,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryItem":
        return cls(
            key=d["key"],
            content=d.get("content"),
            kind=d.get("kind", "fact"),
            confidence=float(d.get("confidence", 0.8)),
            tags=list(d.get("tags", [])),
            source=d.get("source", ""),
            created_at=float(d.get("created_at", _now())),
            updated_at=float(d.get("updated_at", _now())),
        )


@dataclass
class RecallResult:
    """A memory returned from a query, with its computed relevance score."""

    item: MemoryItem
    score: float

    @property
    def key(self) -> str:
        return self.item.key

    @property
    def content(self) -> Any:
        return self.item.content
