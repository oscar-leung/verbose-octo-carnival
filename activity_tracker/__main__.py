"""CLI entry point. Run with `python -m activity_tracker <command>`.

Commands:
  track     run the foreground-window tracker (start this in the morning)
  serve     open the local dashboard at http://127.0.0.1:8765
  run       track + serve together (one process, two threads)
  summary   print today's (or --day YYYY-MM-DD) text summary
  snippet   print today's Markdown snippet to stdout
  note      append a highlight note to today
"""
from __future__ import annotations

import argparse
import sys
import threading

from .storage import Store
from .summary import render_snippet, render_text, summarize


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="activity_tracker")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("track", help="run the tracker loop")
    t.add_argument("--interval", type=float, default=5.0, help="poll seconds")
    t.add_argument("--idle", type=float, default=120.0, help="idle threshold seconds")
    t.add_argument("-v", "--verbose", action="store_true")

    s = sub.add_parser("serve", help="run the local dashboard")
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765)

    r = sub.add_parser("run", help="track + serve in one process")
    r.add_argument("--interval", type=float, default=5.0)
    r.add_argument("--idle", type=float, default=120.0)
    r.add_argument("--host", default="127.0.0.1")
    r.add_argument("--port", type=int, default=8765)
    r.add_argument("-v", "--verbose", action="store_true")

    su = sub.add_parser("summary", help="print today's text summary")
    su.add_argument("--day", help="YYYY-MM-DD (default: today)")

    sn = sub.add_parser("snippet", help="print today's Markdown snippet")
    sn.add_argument("--day", help="YYYY-MM-DD (default: today)")

    n = sub.add_parser("note", help="append a highlight note")
    n.add_argument("text", nargs="+")
    n.add_argument("--day", help="YYYY-MM-DD (default: today)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cmd == "track":
        from .tracker import run
        run(poll_interval=args.interval, idle_threshold=args.idle,
            verbose=args.verbose)
        return 0

    if args.cmd == "serve":
        from .server import serve
        serve(host=args.host, port=args.port)
        return 0

    if args.cmd == "run":
        from .server import serve
        from .tracker import run
        store = Store()
        t = threading.Thread(
            target=run,
            kwargs=dict(poll_interval=args.interval,
                        idle_threshold=args.idle, store=store,
                        verbose=args.verbose),
            daemon=True,
        )
        t.start()
        serve(host=args.host, port=args.port, store=store)
        return 0

    if args.cmd == "summary":
        store = Store()
        print(render_text(summarize(store, args.day)))
        return 0

    if args.cmd == "snippet":
        store = Store()
        print(render_snippet(summarize(store, args.day)))
        return 0

    if args.cmd == "note":
        store = Store()
        store.add_note(" ".join(args.text), day=args.day)
        print("noted.")
        return 0

    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
