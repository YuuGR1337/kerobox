"""Tests for recall — all offline."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kerobox import MemoryBank, MemoryItem, MemoryStore
from kerobox.graph import MemoryGraph
from kerobox import query as q


# --- store + persistence -------------------------------------------------
def test_put_get_and_update_preserves_created_at():
    s = MemoryStore()
    s.put(MemoryItem("k", "v1"))
    created = s.get("k").created_at
    time.sleep(0.01)
    s.put(MemoryItem("k", "v2"))
    assert s.get("k").content == "v2"
    assert s.get("k").created_at == created           # creation preserved
    assert s.get("k").updated_at >= created           # updated bumped


def test_persistence_roundtrip(tmp_path):
    p = str(tmp_path / "mem.json")
    b = MemoryBank(p)
    b.remember("user-tz", "Asia/Jakarta", tags=["user"])
    b.link("user-tz", "user-name", "belongs_to")
    b.save()
    b2 = MemoryBank(p)
    assert b2.get("user-tz").content == "Asia/Jakarta"
    assert "user-name" in b2.graph.neighbors("user-tz")


def test_corrupt_file_is_quarantined(tmp_path):
    p = str(tmp_path / "mem.json")
    with open(p, "w") as f:
        f.write("{ this is not valid json ]")
    b = MemoryBank(p)          # must not raise
    assert len(b) == 0
    # original corrupt file moved aside
    assert any(name.startswith("mem.json.corrupt.") for name in os.listdir(tmp_path))


# --- graph ---------------------------------------------------------------
def test_graph_connected_depth():
    g = MemoryGraph()
    g.link("a", "b")
    g.link("b", "c")
    assert set(g.connected("a", depth=1)) == {"b"}
    assert set(g.connected("a", depth=2)) == {"b", "c"}


def test_graph_drop_key_removes_edges():
    g = MemoryGraph()
    g.link("a", "b")
    g.link("b", "a")
    g.drop_key("a")
    assert g.neighbors("b") == []


# --- recall scoring ------------------------------------------------------
def test_recall_text_match_ranks_relevant_first():
    b = MemoryBank()
    b.remember("stack", "Python and Postgres", tags=["tech"])
    b.remember("name", "Sam", tags=["user"])
    hits = b.recall("python postgres database")
    assert hits[0].item.key == "stack"


def test_recall_by_tag():
    b = MemoryBank()
    b.remember("tz", "Asia/Jakarta", tags=["timezone"])
    b.remember("name", "Sam", tags=["user"])
    hits = b.recall(tags=["timezone"])
    assert len(hits) == 1
    assert hits[0].item.key == "tz"


def test_recall_filters_by_kind():
    b = MemoryBank()
    b.remember("a", "x", kind="fact")
    b.remember("b", "y", kind="preference")
    hits = b.recall(kind="preference", limit=10)
    assert {h.item.key for h in hits} == {"b"}


def test_recency_decay_prefers_newer():
    now = 1_000_000.0
    old = MemoryItem("old", "python", updated_at=now - 86400 * 60)   # 60 days old
    new = MemoryItem("new", "python", updated_at=now)                # fresh
    results = q.search([old, new], query="python", half_life_days=30, now=now)
    assert results[0].item.key == "new"


def test_confidence_boosts_score():
    now = 1_000_000.0
    lo = MemoryItem("lo", "python", confidence=0.2, updated_at=now)
    hi = MemoryItem("hi", "python", confidence=1.0, updated_at=now)
    results = q.search([lo, hi], query="python", now=now)
    assert results[0].item.key == "hi"


def test_forget_removes_memory_and_edges():
    b = MemoryBank()
    b.remember("a", "x")
    b.remember("bb", "y")
    b.link("a", "bb")
    assert b.forget("a") is True
    assert b.get("a") is None
    assert b.graph.neighbors("a") == []
