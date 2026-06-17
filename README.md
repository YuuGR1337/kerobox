# kerobox

[![Tests](https://img.shields.io/badge/tests-11%20passing-brightgreen)]() [![Python](https://img.shields.io/badge/python-3.9%2B-blue)]() [![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Your AI agent forgets everything the moment a session ends — so it re-asks what it was already told, repeats work it already did, and can't build on yesterday.**

kerobox is a persistent memory box for agents: store facts with a confidence score, link related facts into a graph, and recall the most relevant ones for the task at hand — across sessions and process restarts. No database, no vector service, no API key. Just a dependency-free Python library backed by a JSON file that's written atomically (a crash never corrupts it).

```
remember(fact + confidence + tags) ─► link(related facts) ─► recall(query) ─► most relevant, ranked
```

---

## Why it exists

| The problem | What kerobox does |
|---|---|
| LLM has no memory between calls | Durable store on disk, survives restarts |
| Agent re-asks / repeats itself | `recall()` surfaces what's already known |
| "Which fact matters here?" | Relevance ranking by match + confidence + recency |
| Facts are related, not isolated | A graph links memories so you can walk neighbors |
| State files get corrupted on crash | Atomic writes; a bad file is quarantined, not lost |
| Old beliefs outweigh new ones | Confidence + age decay rank fresh, trusted facts first |

No embeddings or external services — transparent, tunable scoring that runs anywhere. Swap in a vector backend later behind the same interface.

---

## Quick start

```bash
git clone https://github.com/YuuGR1337/kerobox
cd kerobox
python examples/agent_memory.py     # run 1: learns facts
python examples/agent_memory.py     # run 2: recalls them from disk
```

```python
from kerobox import MemoryBank

bank = MemoryBank("agent-memory.json")

# remember facts (with confidence + tags)
bank.remember("user-tz", "Asia/Jakarta", kind="preference", tags=["user", "timezone"])
bank.remember("user-stack", "Python and Postgres", tags=["user", "tech"], confidence=0.9)

# link related memories into a graph
bank.link("user-stack", "user-tz", "same_user")

# recall the most relevant memories for a task
for hit in bank.recall("what tech does the user use?"):
    print(hit.score, hit.item.key, hit.item.content)
# -> 0.86 user-stack  Python and Postgres

bank.save()   # persists store + graph atomically
```

Next run, `MemoryBank("agent-memory.json")` loads everything back — your agent picks up where it left off.

---

## How recall ranks

A memory's score blends three signals, so the right fact rises to the top:

- **match** — how well the query terms / tags hit the memory
- **confidence** — how much you trust the memory (0–1)
- **recency** — newer memories outrank stale ones (configurable half-life)

```python
bank.recall("deploy steps", tags=["ops"], kind="procedure", limit=3, half_life_days=14)
```

## Command line

```bash
python -m kerobox -f mem.json remember user-tz "Asia/Jakarta" --tags user,timezone
python -m kerobox -f mem.json recall "timezone"
python -m kerobox -f mem.json link user-tz user-stack --relation same_user
python -m kerobox -f mem.json list
```

---

## API in one screen

| Call | Does |
|---|---|
| `remember(key, content, *, kind, confidence, tags, source)` | store/update a fact |
| `recall(query, *, tags, kind, limit, half_life_days)` | ranked relevant memories |
| `link(src, dst, relation)` | connect two memories |
| `related(key, depth)` | memories connected to one |
| `forget(key)` | delete a memory (and its links) |
| `save()` / `MemoryBank(path)` | persist / load |

---

## Testing

```bash
pip install pytest
pytest
```

Covers persistence round-trips, corrupt-file quarantine, graph traversal, relevance ranking, recency decay, and confidence weighting — all offline.

## Use cases

kerobox is a good fit if you're trying to:

- give an **LLM agent long-term memory** that persists between calls and restarts
- let a **chatbot remember user preferences and past conversations** across sessions
- add a **lightweight memory layer** to a Python agent without a vector database
- store and **recall facts by relevance** without standing up Pinecone/Chroma/Weaviate
- build **agent state / knowledge that survives restarts** for long-running automations
- prototype **agent memory** before committing to a heavier embedding stack

A simple, dependency-free alternative to vector-DB memory for AI agents — start here, swap in embeddings later behind the same `recall()` API.

## Roadmap

- Optional vector/embedding backend behind the same `recall()` API
- TTL / forgetting policies for ephemeral memories
- Pluggable stores (SQLite, Redis)

## License

MIT — see [LICENSE](LICENSE).
