"""SQLite storage for activity samples and merged sessions.

Schema is intentionally tiny: one row per "session" (a contiguous stretch
where the same (app, title, category) was foreground). The tracker writes
samples and merges them as it goes -- no separate batch job needed.
"""
from __future__ import annotations

import os
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


def default_db_path() -> Path:
    base = os.environ.get("ACTIVITY_TRACKER_HOME")
    if base:
        return Path(base).expanduser() / "activity.db"
    return Path.home() / ".activity_tracker" / "activity.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    started   REAL NOT NULL,        -- unix epoch seconds
    ended     REAL NOT NULL,
    app       TEXT NOT NULL,
    title     TEXT NOT NULL,
    category  TEXT NOT NULL,
    url       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_started ON sessions(started);
CREATE INDEX IF NOT EXISTS idx_sessions_category ON sessions(category);

CREATE TABLE IF NOT EXISTS notes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    created   REAL NOT NULL,
    day       TEXT NOT NULL,        -- YYYY-MM-DD local date
    text      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_notes_day ON notes(day);
"""


@dataclass
class Session:
    id: int
    started: float
    ended: float
    app: str
    title: str
    category: str
    url: Optional[str]

    @property
    def duration(self) -> float:
        return max(0.0, self.ended - self.started)


class Store:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or default_db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False so the same connection can serve the
        # tracker thread and HTTP handler threads. We serialize access
        # ourselves with _lock; SQLite's own locking handles the file.
        self._conn = sqlite3.connect(
            self.path, isolation_level=None, check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._lock = threading.Lock()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- writes ----------------------------------------------------------
    def append_sample(
        self,
        ts: float,
        duration: float,
        app: str,
        title: str,
        category: str,
        url: Optional[str],
        merge_gap: float = 5.0,
    ) -> None:
        """Add a sample. Extends the last session if it's the same context."""
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, ended, app, title, category FROM sessions "
                "ORDER BY id DESC LIMIT 1"
            )
            last = cur.fetchone()
            ended = ts + duration
            if (
                last
                and last["app"] == app
                and last["title"] == title
                and last["category"] == category
                and ts - last["ended"] <= merge_gap
            ):
                self._conn.execute(
                    "UPDATE sessions SET ended=? WHERE id=?", (ended, last["id"])
                )
            else:
                self._conn.execute(
                    "INSERT INTO sessions(started,ended,app,title,category,url) "
                    "VALUES (?,?,?,?,?,?)",
                    (ts, ended, app, title, category, url),
                )

    def add_note(self, text: str, day: Optional[str] = None) -> None:
        now = time.time()
        if day is None:
            day = time.strftime("%Y-%m-%d", time.localtime(now))
        with self._lock:
            self._conn.execute(
                "INSERT INTO notes(created,day,text) VALUES (?,?,?)",
                (now, day, text),
            )

    # -- reads -----------------------------------------------------------
    def sessions_between(self, start: float, end: float) -> list[Session]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sessions WHERE ended > ? AND started < ? "
                "ORDER BY started",
                (start, end),
            ).fetchall()
        out = []
        for r in rows:
            # clip to window for accurate totals across day boundaries
            s = max(r["started"], start)
            e = min(r["ended"], end)
            if e <= s:
                continue
            out.append(
                Session(
                    id=r["id"], started=s, ended=e, app=r["app"],
                    title=r["title"], category=r["category"], url=r["url"],
                )
            )
        return out

    def notes_for_day(self, day: str) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT text FROM notes WHERE day=? ORDER BY created", (day,)
            ).fetchall()
        return [r["text"] for r in rows]
