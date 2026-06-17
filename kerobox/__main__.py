"""Command-line access to a memory bank: `python -m kerobox`.

    python -m kerobox --file mem.json remember user-tz "Asia/Jakarta" --tags user,preference
    python -m kerobox --file mem.json recall "timezone"
    python -m kerobox --file mem.json link user-tz user-locale
    python -m kerobox --file mem.json list
"""

from __future__ import annotations

import argparse
import json
import sys

from .bank import MemoryBank


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kerobox", description="Persistent memory for AI agents.")
    ap.add_argument("--file", "-f", required=True, help="path to the memory JSON file")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("remember", help="store a fact")
    r.add_argument("key")
    r.add_argument("content")
    r.add_argument("--kind", default="fact")
    r.add_argument("--confidence", type=float, default=0.8)
    r.add_argument("--tags", default="", help="comma-separated")

    q = sub.add_parser("recall", help="query memories")
    q.add_argument("query", nargs="?", default="")
    q.add_argument("--tags", default="")
    q.add_argument("--limit", type=int, default=5)

    lk = sub.add_parser("link", help="link two memory keys")
    lk.add_argument("src")
    lk.add_argument("dst")
    lk.add_argument("--relation", default="related")

    sub.add_parser("list", help="list all memories")

    f = sub.add_parser("forget", help="delete a memory")
    f.add_argument("key")

    args = ap.parse_args(argv)
    bank = MemoryBank(args.file)

    if args.cmd == "remember":
        tags = [t for t in args.tags.split(",") if t]
        bank.remember(args.key, args.content, kind=args.kind, confidence=args.confidence, tags=tags)
        bank.save()
        print(f"remembered: {args.key}")
    elif args.cmd == "recall":
        tags = [t for t in args.tags.split(",") if t]
        hits = bank.recall(args.query, tags=tags, limit=args.limit)
        if not hits:
            print("(no matches)")
        for h in hits:
            print(f"[{h.score:.3f}] {h.item.key}: {h.item.content}")
    elif args.cmd == "link":
        bank.link(args.src, args.dst, args.relation)
        bank.save()
        print(f"linked: {args.src} -[{args.relation}]-> {args.dst}")
    elif args.cmd == "list":
        for item in bank.store.all():
            print(f"{item.key} ({item.kind}, conf={item.confidence}): {item.content}")
        print(f"\n{len(bank)} memories")
    elif args.cmd == "forget":
        ok = bank.forget(args.key)
        bank.save()
        print("forgotten" if ok else "not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
