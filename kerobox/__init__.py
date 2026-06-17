"""
kerobox — persistent, queryable memory for AI agents and long-running scripts.

An LLM forgets everything between calls. kerobox gives your agent a durable
memory: store facts with a confidence score, link related facts into a graph,
and recall the most relevant ones for the task at hand — across sessions and
process restarts.

Dependency-free. State is JSON on disk, written atomically so a crash never
corrupts it. A corrupt file is quarantined rather than silently dropped.
"""

from .types import MemoryItem, RecallResult
from .store import MemoryStore
from .graph import MemoryGraph
from .bank import MemoryBank

__version__ = "0.1.0"

__all__ = [
    "MemoryItem",
    "RecallResult",
    "MemoryStore",
    "MemoryGraph",
    "MemoryBank",
]
