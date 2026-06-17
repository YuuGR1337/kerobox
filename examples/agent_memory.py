#!/usr/bin/env python3
"""Demo: an agent that remembers across runs.

Run it twice:

    python examples/agent_memory.py     # first run: learns facts
    python examples/agent_memory.py     # second run: recalls them from disk

The point: nothing is hard-coded between runs. The second run reads the JSON
file the first run wrote, proving memory survives process restart — the thing a
bare LLM can't do.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kerobox import MemoryBank  # noqa: E402

MEM_FILE = os.path.join(os.path.dirname(__file__), "demo-memory.json")


def main() -> None:
    bank = MemoryBank(MEM_FILE)

    if len(bank) == 0:
        print("First run — learning facts about the user...\n")
        bank.remember("user-name", "Sam", tags=["user"], confidence=0.95)
        bank.remember("user-tz", "Asia/Jakarta", kind="preference", tags=["user", "timezone"])
        bank.remember("user-stack", "Python and Postgres", kind="preference", tags=["user", "tech"])
        bank.remember("proj-deadline", "ships in 2 weeks", kind="fact", tags=["project"], confidence=0.6)
        # Link related memories into a small graph (user-name -> its attributes).
        bank.link("user-name", "user-tz", "has")
        bank.link("user-name", "user-stack", "has")
        bank.save()
        print(f"Stored {len(bank)} memories to {os.path.basename(MEM_FILE)}.")
        print("Run this script again — it will recall them from disk.\n")
        return

    print(f"Second run — recalled {len(bank)} memories from disk.\n")

    print('Query: "what tech does the user like?"')
    for hit in bank.recall("tech stack programming", limit=3):
        print(f"  [{hit.score:.3f}] {hit.item.key}: {hit.item.content}")

    print('\nQuery by tag: ["timezone"]')
    for hit in bank.recall(tags=["timezone"]):
        print(f"  [{hit.score:.3f}] {hit.item.key}: {hit.item.content}")

    print("\nMemories related to 'user-name':")
    for item in bank.related("user-name"):
        print(f"  - {item.key}: {item.content}")

    print(
        "\nDelete examples/demo-memory.json to reset the demo."
    )


if __name__ == "__main__":
    main()
