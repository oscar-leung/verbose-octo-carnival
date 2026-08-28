"""In-memory per-IP sliding-window rate limiter for the free tier."""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from typing import Deque, Dict, Tuple

_hits: Dict[str, Deque[float]] = {}
_lock = threading.Lock()

WINDOW_SECONDS = 24 * 60 * 60
FREE_DAILY_LIMIT = int(os.environ.get("FREE_DAILY_LIMIT", "1"))


def check_and_record(ip: str, now: float | None = None) -> Tuple[bool, int]:
    now = now if now is not None else time.time()
    cutoff = now - WINDOW_SECONDS

    with _lock:
        dq = _hits.setdefault(ip, deque())
        while dq and dq[0] < cutoff:
            dq.popleft()

        if len(dq) >= FREE_DAILY_LIMIT:
            return False, 0

        dq.append(now)
        return True, FREE_DAILY_LIMIT - len(dq)


def remaining(ip: str, now: float | None = None) -> int:
    now = now if now is not None else time.time()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        dq = _hits.get(ip)
        if not dq:
            return FREE_DAILY_LIMIT
        while dq and dq[0] < cutoff:
            dq.popleft()
        return max(0, FREE_DAILY_LIMIT - len(dq))
