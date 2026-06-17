"""Relevance scoring for recall.

Given a query (free text and/or tags), score every memory and return the best.
Score blends three signals:

- **match**      how well the query terms / tags hit the memory's content+tags
- **confidence** the stored belief in the memory
- **recency**    newer memories rank above stale ones, via gentle age decay

No embeddings, no external services — a transparent, tunable scoring function
that runs anywhere. Swap in a vector backend later behind the same interface.
"""

from __future__ import annotations

import math
import re
import time
from typing import Iterable, Optional

from .types import MemoryItem, RecallResult

_WORD_RE = re.compile(r"\w+")


def _tokens(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _text_of(item: MemoryItem) -> str:
    return f"{item.key} {item.content} {' '.join(item.tags)} {item.kind}"


def _match_score(query_terms: set[str], item: MemoryItem, want_tags: set[str]) -> float:
    if not query_terms and not want_tags:
        return 1.0  # no filter -> everything matches equally

    score = 0.0
    if query_terms:
        item_terms = _tokens(_text_of(item))
        overlap = len(query_terms & item_terms)
        score += overlap / len(query_terms)  # 0–1 fraction of query covered

    if want_tags:
        item_tags = {t.lower() for t in item.tags}
        tag_overlap = len(want_tags & item_tags)
        score += tag_overlap / len(want_tags)

    # Normalize by how many filters were supplied.
    divisor = (1 if query_terms else 0) + (1 if want_tags else 0)
    return score / divisor if divisor else 0.0


def _recency_factor(item: MemoryItem, half_life_days: float, now: float) -> float:
    """Exponential decay: a memory at one half-life counts for ~0.5."""
    if half_life_days <= 0:
        return 1.0
    age_days = max(0.0, (now - item.updated_at) / 86400.0)
    return math.pow(0.5, age_days / half_life_days)


def search(
    items: Iterable[MemoryItem],
    query: str = "",
    tags: Optional[list[str]] = None,
    kind: Optional[str] = None,
    limit: int = 5,
    half_life_days: float = 30.0,
    min_score: float = 0.0,
    now: Optional[float] = None,
) -> list[RecallResult]:
    now = now if now is not None else time.time()
    query_terms = _tokens(query)
    want_tags = {t.lower() for t in (tags or [])}

    results: list[RecallResult] = []
    for item in items:
        if kind is not None and item.kind != kind:
            continue
        match = _match_score(query_terms, item, want_tags)
        if match <= 0 and (query_terms or want_tags):
            continue
        recency = _recency_factor(item, half_life_days, now)
        # Final score: match dominates, weighted by belief and freshness.
        score = match * (0.5 + 0.5 * item.confidence) * (0.5 + 0.5 * recency)
        if score >= min_score:
            results.append(RecallResult(item=item, score=round(score, 4)))

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:limit]
