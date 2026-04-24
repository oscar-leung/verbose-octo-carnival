"""In-memory per-IP sliding-window rate limiter.

Good enough for a single-worker MVP. For multi-worker or multi-host deploys,
swap the _hits dict for Redis with INCR + EXPIRE.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Deque, Dict, Tuple

_hits: Dict[str, Deque[float]] = {}
_lock = threading.Lock()

WINDOW_SECONDS = 24 * 60 * 60
FREE_DAILY_LIMIT = 3


def check_and_record(ip: str, now: float | None = None) -> Tuple[bool, int]:
    """Record a hit for `ip`. Returns (allowed, remaining_after_this_hit).

    If not allowed, returns (False, 0) and does NOT record the hit.
    """
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
    """How many free hits `ip` has left without recording a new one."""
    now = now if now is not None else time.time()
    cutoff = now - WINDOW_SECONDS
    with _lock:
        dq = _hits.get(ip)
        if not dq:
            return FREE_DAILY_LIMIT
        while dq and dq[0] < cutoff:
            dq.popleft()
        return max(0, FREE_DAILY_LIMIT - len(dq))
