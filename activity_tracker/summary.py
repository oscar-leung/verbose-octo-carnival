"""Aggregations over stored sessions and snippet generation for sharing."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .storage import Session, Store


def day_bounds(day: Optional[str] = None) -> tuple[float, float, str]:
    """Return (start_epoch, end_epoch, YYYY-MM-DD) for a local-time day."""
    if day is None:
        now = datetime.now()
        d = now.date()
    else:
        d = datetime.strptime(day, "%Y-%m-%d").date()
    start = datetime(d.year, d.month, d.day)
    end = start + timedelta(days=1)
    return start.timestamp(), end.timestamp(), d.isoformat()


@dataclass
class Bucket:
    name: str
    seconds: float = 0.0
    titles: dict[str, float] = field(default_factory=dict)

    def add(self, title: str, secs: float) -> None:
        self.seconds += secs
        self.titles[title] = self.titles.get(title, 0.0) + secs

    def top_titles(self, n: int = 5) -> list[tuple[str, float]]:
        return sorted(self.titles.items(), key=lambda kv: kv[1], reverse=True)[:n]


@dataclass
class DaySummary:
    day: str
    total: float
    by_category: list[Bucket]
    by_app: list[Bucket]
    notes: list[str]
    sessions: list[Session]


def summarize(store: Store, day: Optional[str] = None) -> DaySummary:
    start, end, iso = day_bounds(day)
    sessions = store.sessions_between(start, end)

    cat: dict[str, Bucket] = {}
    app: dict[str, Bucket] = {}
    total = 0.0
    for s in sessions:
        secs = s.duration
        total += secs
        cat.setdefault(s.category, Bucket(s.category)).add(s.title, secs)
        app.setdefault(s.app, Bucket(s.app)).add(s.title, secs)

    by_category = sorted(cat.values(), key=lambda b: b.seconds, reverse=True)
    by_app = sorted(app.values(), key=lambda b: b.seconds, reverse=True)
    notes = store.notes_for_day(iso)
    return DaySummary(
        day=iso, total=total, by_category=by_category,
        by_app=by_app, notes=notes, sessions=sessions,
    )


def fmt_duration(secs: float) -> str:
    secs = int(secs)
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m"
    if m:
        return f"{m}m {s:02d}s"
    return f"{s}s"


def render_text(summary: DaySummary) -> str:
    """Plain-text summary, good for terminals and `cat`-friendly logs."""
    lines = [f"=== Activity for {summary.day} ===",
             f"Tracked: {fmt_duration(summary.total)}", ""]
    lines.append("By category:")
    for b in summary.by_category:
        pct = (b.seconds / summary.total * 100) if summary.total else 0
        lines.append(f"  {b.name:<14} {fmt_duration(b.seconds):>10}  ({pct:4.1f}%)")
    lines.append("")
    lines.append("By app:")
    for b in summary.by_app[:10]:
        lines.append(f"  {b.name:<20} {fmt_duration(b.seconds):>10}")
    if summary.notes:
        lines.append("")
        lines.append("Notes:")
        for n in summary.notes:
            lines.append(f"  - {n}")
    return "\n".join(lines)


def render_snippet(summary: DaySummary) -> str:
    """Markdown snippet suitable for a GitHub profile / dev journal / demo."""
    lines = [f"### What I did on {summary.day}"]
    if summary.total:
        lines.append(f"_Total focused time: {fmt_duration(summary.total)}_")
    lines.append("")
    if summary.by_category:
        for b in summary.by_category[:6]:
            pct = (b.seconds / summary.total * 100) if summary.total else 0
            top = ", ".join(t for t, _ in b.top_titles(2)) or "—"
            lines.append(
                f"- **{b.name}** — {fmt_duration(b.seconds)} ({pct:.0f}%) · {top}"
            )
    if summary.notes:
        lines.append("")
        lines.append("**Highlights:**")
        for n in summary.notes:
            lines.append(f"- {n}")
    return "\n".join(lines)
