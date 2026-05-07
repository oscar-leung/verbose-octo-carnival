"""Foreground tracker loop. Polls the active window every N seconds and
writes samples to the local SQLite store. Skips intervals where the user
has been idle for longer than ``idle_threshold`` seconds.
"""
from __future__ import annotations

import signal
import sys
import time
from typing import Optional

from .categorize import Categorizer, extract_url
from .storage import Store
from .window import active_window, idle_seconds


def run(
    poll_interval: float = 5.0,
    idle_threshold: float = 120.0,
    store: Optional[Store] = None,
    verbose: bool = False,
) -> None:
    store = store or Store()
    cats = Categorizer.load()
    running = True

    def stop(*_a):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    if verbose:
        print(f"[tracker] db={store.path} poll={poll_interval}s idle>{idle_threshold}s", flush=True)

    last_tick = time.time()
    while running:
        time.sleep(poll_interval)
        now = time.time()
        elapsed = now - last_tick
        last_tick = now

        idle = idle_seconds()
        if idle is not None and idle >= idle_threshold:
            if verbose:
                print(f"[tracker] idle {idle:.0f}s, skipping", flush=True)
            continue

        win = active_window()
        if win is None:
            if verbose:
                print("[tracker] no active window probe; skipping", flush=True)
            continue

        url = win.url or extract_url(win.title)
        category = cats.classify(win.app, win.title, url)
        store.append_sample(
            ts=now - elapsed,
            duration=elapsed,
            app=win.app,
            title=win.title,
            category=category,
            url=url,
        )
        if verbose:
            print(f"[tracker] +{elapsed:4.1f}s  {category:<12} {win.app} | {win.title[:60]}", flush=True)

    if verbose:
        print("[tracker] stopped", flush=True)
    store.close()


if __name__ == "__main__":  # pragma: no cover
    run(verbose="-v" in sys.argv)
