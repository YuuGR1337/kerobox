"""Relationship graph over memory keys.

Facts rarely stand alone: "user prefers dark mode" relates to "user is a
developer"; "found API endpoint X" enables "tested endpoint X". recall stores
those links as a directed graph of edges between memory keys, so you can walk
from one memory to everything connected to it.

The graph stores only keys + relation labels; the memories themselves live in
the MemoryStore. This keeps the two concerns separate and the graph tiny.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Edge:
    src: str
    dst: str
    relation: str = "related"

    def to_dict(self) -> dict:
        return {"src": self.src, "dst": self.dst, "relation": self.relation}

    @classmethod
    def from_dict(cls, d: dict) -> "Edge":
        return cls(src=d["src"], dst=d["dst"], relation=d.get("relation", "related"))


class MemoryGraph:
    def __init__(self) -> None:
        self._edges: list[Edge] = []

    def link(self, src: str, dst: str, relation: str = "related") -> None:
        # Avoid duplicate identical edges.
        for e in self._edges:
            if e.src == src and e.dst == dst and e.relation == relation:
                return
        self._edges.append(Edge(src, dst, relation))

    def unlink(self, src: str, dst: str, relation: Optional[str] = None) -> int:
        before = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (e.src == src and e.dst == dst and (relation is None or e.relation == relation))
        ]
        return before - len(self._edges)

    def neighbors(self, key: str, relation: Optional[str] = None) -> list[str]:
        """Keys directly reachable from `key` (optionally filtered by relation)."""
        return [
            e.dst for e in self._edges
            if e.src == key and (relation is None or e.relation == relation)
        ]

    def connected(self, key: str, depth: int = 1) -> list[str]:
        """All keys reachable from `key` within `depth` hops (breadth-first)."""
        seen: set[str] = set()
        frontier = [key]
        for _ in range(max(0, depth)):
            nxt: list[str] = []
            for k in frontier:
                for n in self.neighbors(k):
                    if n not in seen and n != key:
                        seen.add(n)
                        nxt.append(n)
            frontier = nxt
        return list(seen)

    def drop_key(self, key: str) -> None:
        """Remove every edge touching `key` (call when a memory is deleted)."""
        self._edges = [e for e in self._edges if e.src != key and e.dst != key]

    # -- persistence helpers (used by MemoryBank) ------------------------
    def to_list(self) -> list[dict]:
        return [e.to_dict() for e in self._edges]

    def load_list(self, raw: list[dict]) -> None:
        self._edges = [Edge.from_dict(d) for d in raw]
