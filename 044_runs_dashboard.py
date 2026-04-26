"""
Runs Dashboard — health-check view across all job-application scripts.
─────────────────────────────────────────────────────────────────────
Aggregates everything under runs/ into a single report:

  • Per-script: total runs, last run, jobs applied / skipped / errored
  • Daily timeline of applications over the last 30 days
  • Pipeline funnel from job_tracker.json (043 Gmail tracker)
  • Recent-runs table

Two output modes — both read-only:

  python3 044_runs_dashboard.py                     # writes runs/dashboard.html
  python3 044_runs_dashboard.py --terminal          # ANSI summary to stdout
  python3 044_runs_dashboard.py --runs-dir /path    # override runs/ location
  python3 044_runs_dashboard.py --no-color          # plain ASCII for terminal mode
  python3 044_runs_dashboard.py --window-days 14    # timeline window (default 30)

The HTML file is self-contained (embedded CSS, inline SVG bars, no JS).
Open it with `open runs/dashboard.html` on macOS or pair it with
`open_dashboard.sh` for the live-tail panes alongside the rollup view.
"""

import argparse
import html
import json
import logging
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# ── Friendly names per dir prefix ────────────────────────────────────────────
SCRIPT_LABELS: dict[str, tuple[str, str]] = {
    # prefix                           : (script_id, display_name)
    "linkedin_easy_apply_pa":           ("035", "LinkedIn Easy Apply"),
    "linkedin_easy_apply":              ("025", "LinkedIn Easy Apply (legacy)"),
    "handshake_apply_pa":               ("036", "Handshake Easy Apply"),
    "handshake_apply":                  ("033", "Handshake (legacy)"),
    "handshake_people":                 ("040", "Handshake People + Jobs"),
    "handshake_follow":                 ("039", "Handshake Follow Employers"),
    "handshake_job_scraper":            ("034", "Handshake Job Scraper"),
    "indeed_apply":                     ("037", "Indeed Apply"),
    "greenhouse_apply":                 ("038", "Greenhouse Apply"),
    "calcareers":                       ("041", "CalCareers Monitor"),
    "calcareers_monitor":               ("041", "CalCareers Monitor"),
    "unified":                          ("042", "Unified Pipeline"),
    "gmail_job_tracker":                ("043", "Gmail Job Tracker"),
    "linkedin_emails":                  ("029", "LinkedIn Email Scraper"),
}

# Status colour buckets (used by both renderers)
STATUS_BUCKETS = ["applied", "skipped", "error", "dry_run", "scraped_only", "other"]

RUN_DIR_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9_]*?)_(?P<ts>\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})$")

log = logging.getLogger("runs_dashboard")


# ── Models ────────────────────────────────────────────────────────────────────
@dataclass
class RunRecord:
    prefix: str
    timestamp: datetime
    path: Path
    jobs_total: int = 0
    status_counts: Counter = field(default_factory=Counter)
    had_run_log: bool = False
    log_size: int = 0


@dataclass
class ScriptSummary:
    prefix: str
    script_id: str
    display_name: str
    runs: list[RunRecord] = field(default_factory=list)

    @property
    def run_count(self) -> int:
        return len(self.runs)

    @property
    def last_run(self) -> RunRecord | None:
        return max(self.runs, key=lambda r: r.timestamp) if self.runs else None

    @property
    def status_totals(self) -> Counter:
        c = Counter()
        for r in self.runs:
            c.update(r.status_counts)
        return c

    @property
    def applied(self) -> int:
        return self.status_totals.get("applied", 0)

    @property
    def errored(self) -> int:
        return self.status_totals.get("error", 0)

    @property
    def total_jobs(self) -> int:
        return sum(r.jobs_total for r in self.runs)


@dataclass
class Report:
    generated_at: datetime
    runs_dir: Path
    scripts: list[ScriptSummary]
    daily_applied: dict[date, int]              # date → applications
    pipeline_funnel: dict[str, int]             # status → count from job_tracker.json
    recent_runs: list[RunRecord]                # last 20
    window_days: int


# ── Discovery ─────────────────────────────────────────────────────────────────
def parse_run_dir(p: Path) -> RunRecord | None:
    m = RUN_DIR_RE.match(p.name)
    if not m:
        return None
    try:
        ts = datetime.strptime(m["ts"], "%Y-%m-%d_%H-%M-%S")
    except ValueError:
        return None

    rec = RunRecord(prefix=m["prefix"], timestamp=ts, path=p)

    jobs_path = p / "jobs.json"
    if jobs_path.exists():
        try:
            jobs = json.loads(jobs_path.read_text())
        except Exception as e:
            log.debug(f"bad jobs.json in {p.name}: {e}")
            jobs = []
        if isinstance(jobs, dict) and "jobs" in jobs:
            jobs = jobs["jobs"]
        rec.jobs_total = len(jobs) if isinstance(jobs, list) else 0
        for j in (jobs if isinstance(jobs, list) else []):
            status = (j.get("status") or "other").split("_")[0] if "_" in (j.get("status") or "") \
                else (j.get("status") or "other")
            # bucket: applied / skipped_* / error / dry_run / scraped_only
            raw = j.get("status") or "other"
            bucket = (
                "applied" if raw == "applied"
                else "error" if raw == "error"
                else "dry_run" if raw == "dry_run"
                else "scraped_only" if raw == "scraped_only"
                else "skipped" if raw.startswith("skipped")
                else "other"
            )
            rec.status_counts[bucket] += 1

    summary_path = p / "summary.json"
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text())
            for stage, info in (summary.get("stages") or {}).items():
                if info.get("ok"):
                    rec.status_counts["applied"] += 0  # don't double count, just mark presence
                else:
                    rec.status_counts["error"] += 1
        except Exception:
            pass

    log_path = p / "run.log"
    if log_path.exists():
        rec.had_run_log = True
        try:
            rec.log_size = log_path.stat().st_size
        except OSError:
            pass

    return rec


def discover_runs(runs_dir: Path) -> list[RunRecord]:
    if not runs_dir.exists():
        return []
    out = []
    for child in runs_dir.iterdir():
        if not child.is_dir() or child.name == "daily_logs":
            continue
        rec = parse_run_dir(child)
        if rec:
            out.append(rec)
    return out


def group_by_script(records: list[RunRecord]) -> list[ScriptSummary]:
    by_prefix: dict[str, list[RunRecord]] = defaultdict(list)
    for r in records:
        by_prefix[r.prefix].append(r)

    summaries = []
    for prefix, runs in by_prefix.items():
        sid, name = SCRIPT_LABELS.get(prefix, ("???", prefix.replace("_", " ").title()))
        summaries.append(ScriptSummary(prefix=prefix, script_id=sid, display_name=name, runs=runs))

    summaries.sort(key=lambda s: (s.script_id, s.prefix))
    return summaries


def daily_applied_window(records: list[RunRecord], window_days: int) -> dict[date, int]:
    today = date.today()
    start = today - timedelta(days=window_days - 1)
    out = {start + timedelta(days=i): 0 for i in range(window_days)}
    for r in records:
        d = r.timestamp.date()
        if d < start or d > today:
            continue
        out[d] += r.status_counts.get("applied", 0)
    return out


def load_pipeline_funnel(tracker_path: Path) -> dict[str, int]:
    if not tracker_path.exists():
        return {}
    try:
        data = json.loads(tracker_path.read_text())
    except Exception as e:
        log.warning(f"could not read {tracker_path}: {e}")
        return {}
    counts: Counter = Counter()
    for entry in (data.get("entries") or {}).values():
        counts[entry.get("status", "unknown")] += 1
    # Order matters for a funnel display
    order = ["applied", "assessment", "interview", "offer", "rejection", "ghosted", "unknown"]
    return {k: counts.get(k, 0) for k in order if counts.get(k, 0) > 0}


def build_report(runs_dir: Path, tracker_path: Path, window_days: int) -> Report:
    records = discover_runs(runs_dir)
    return Report(
        generated_at=datetime.now(timezone.utc),
        runs_dir=runs_dir,
        scripts=group_by_script(records),
        daily_applied=daily_applied_window(records, window_days),
        pipeline_funnel=load_pipeline_funnel(tracker_path),
        recent_runs=sorted(records, key=lambda r: r.timestamp, reverse=True)[:20],
        window_days=window_days,
    )


# ── Terminal renderer ────────────────────────────────────────────────────────
class C:
    def __init__(self, enabled: bool):
        self.on = enabled
    def _w(self, code: str, s: str) -> str:
        return f"\033[{code}m{s}\033[0m" if self.on else s
    def bold(self, s):    return self._w("1", s)
    def dim(self, s):     return self._w("2", s)
    def green(self, s):   return self._w("32", s)
    def yellow(self, s):  return self._w("33", s)
    def red(self, s):     return self._w("31", s)
    def cyan(self, s):    return self._w("36", s)
    def magenta(self, s): return self._w("35", s)


def _bar(n: int, peak: int, width: int = 30) -> str:
    if peak <= 0:
        return ""
    filled = round(width * n / peak)
    return "█" * filled + "░" * (width - filled)


def render_terminal(r: Report, color: bool = True) -> str:
    c = C(color)
    lines = []
    title = f"  Runs Dashboard — {r.generated_at.astimezone().strftime('%Y-%m-%d %H:%M %Z')}  "
    bar_len = max(60, len(title) + 4)
    lines.append(c.bold(c.cyan("┏" + "━" * bar_len + "┓")))
    lines.append(c.bold(c.cyan("┃") + title.center(bar_len) + c.cyan("┃")))
    lines.append(c.bold(c.cyan("┗" + "━" * bar_len + "┛")))
    lines.append(c.dim(f"  runs/: {r.runs_dir}    window: last {r.window_days} days"))
    lines.append("")

    # ── Per-script summary ──
    lines.append(c.bold("Per-script health"))
    lines.append(c.dim("─" * 78))
    if not r.scripts:
        lines.append(c.dim("  (no run directories found)"))
    else:
        header = f"  {'#':<4} {'Script':<28} {'Runs':>5} {'Last run':<19} "\
                 f"{'Applied':>7} {'Errors':>6} {'Total':>6}"
        lines.append(c.bold(header))
        for s in r.scripts:
            last = s.last_run.timestamp.strftime("%Y-%m-%d %H:%M") if s.last_run else "—"
            err = s.errored
            err_s = c.red(f"{err:>6}") if err else c.dim(f"{err:>6}")
            applied_s = c.green(f"{s.applied:>7}") if s.applied else c.dim(f"{s.applied:>7}")
            lines.append(
                f"  {s.script_id:<4} {s.display_name[:28]:<28} {s.run_count:>5} "
                f"{last:<19} {applied_s} {err_s} {s.total_jobs:>6}"
            )
    lines.append("")

    # ── Timeline ──
    lines.append(c.bold(f"Applications per day (last {r.window_days} days)"))
    lines.append(c.dim("─" * 78))
    peak = max(r.daily_applied.values() or [0])
    if peak == 0:
        lines.append(c.dim("  (no applications recorded in this window)"))
    else:
        for d, n in r.daily_applied.items():
            row = f"  {d.isoformat()}  {_bar(n, peak)}  {n}"
            lines.append(c.green(row) if n else c.dim(row))
    lines.append("")

    # ── Pipeline funnel ──
    lines.append(c.bold("Pipeline funnel — job_tracker.json"))
    lines.append(c.dim("─" * 78))
    if not r.pipeline_funnel:
        lines.append(c.dim("  (no job_tracker.json yet — run 043_gmail_job_tracker.py)"))
    else:
        peak = max(r.pipeline_funnel.values())
        colour = {
            "applied":    c.cyan,
            "assessment": c.yellow,
            "interview":  c.magenta,
            "offer":      c.green,
            "rejection":  c.red,
            "ghosted":    c.dim,
            "unknown":    c.dim,
        }
        for status, n in r.pipeline_funnel.items():
            paint = colour.get(status, c.dim)
            lines.append(f"  {paint(status):<22} {_bar(n, peak)}  {n}")
    lines.append("")

    # ── Recent runs ──
    lines.append(c.bold("Recent runs (latest 20)"))
    lines.append(c.dim("─" * 78))
    if not r.recent_runs:
        lines.append(c.dim("  (none)"))
    else:
        for rec in r.recent_runs:
            sid, name = SCRIPT_LABELS.get(rec.prefix, ("???", rec.prefix))
            ts = rec.timestamp.strftime("%Y-%m-%d %H:%M")
            applied = rec.status_counts.get("applied", 0)
            errored = rec.status_counts.get("error", 0)
            tag = (c.red(" ✗") if errored else c.green(" ✓") if applied else c.dim(" ·"))
            lines.append(f"  {ts}  {sid:<4} {name[:28]:<28}"
                         f"  applied={applied:<3}  errors={errored:<2}{tag}")
    lines.append("")
    return "\n".join(lines)


# ── HTML renderer ────────────────────────────────────────────────────────────
HTML_CSS = """
:root { color-scheme: light dark; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
       margin: 0; padding: 24px 32px; max-width: 1100px;
       background: #fafafa; color: #1f1f1f; }
@media (prefers-color-scheme: dark) {
  body { background: #111; color: #eee; }
  .card { background: #1b1b1b; border-color: #2a2a2a; }
  th { background: #1f1f1f; color: #ddd; }
  tr:nth-child(even) td { background: #161616; }
  .bar-track { background: #222; }
  .meta, .empty { color: #888; }
}
h1 { margin: 0 0 4px; font-size: 22px; }
h2 { margin: 32px 0 12px; font-size: 16px; letter-spacing: .04em;
     text-transform: uppercase; color: #555; }
.meta { color: #777; font-size: 13px; margin-bottom: 24px; }
.cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.card { background: #fff; border: 1px solid #eaeaea; border-radius: 10px; padding: 14px 16px; }
.card .name { font-weight: 600; }
.card .id { color: #999; font-size: 12px; margin-right: 8px; }
.card .stats { display: flex; gap: 12px; font-size: 13px; margin-top: 8px; color: #444; }
.card .stat-applied { color: #1d8348; font-weight: 600; }
.card .stat-error   { color: #c0392b; font-weight: 600; }
.card .last { font-size: 12px; color: #888; margin-top: 6px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #eee; }
th { background: #f3f3f3; font-weight: 600; font-size: 12px; }
tr:nth-child(even) td { background: #fafafa; }
.bar-track { background: #eee; height: 10px; border-radius: 5px; overflow: hidden; min-width: 120px; }
.bar-fill  { height: 100%; }
.fill-applied    { background: #2ecc71; }
.fill-assessment { background: #f1c40f; }
.fill-interview  { background: #9b59b6; }
.fill-offer      { background: #16a085; }
.fill-rejection  { background: #e74c3c; }
.fill-ghosted    { background: #95a5a6; }
.fill-unknown    { background: #bdc3c7; }
.fill-day        { background: #3498db; }
.empty { color: #999; font-style: italic; }
.tag-ok    { color: #1d8348; }
.tag-fail  { color: #c0392b; }
.tag-dim   { color: #888; }
"""


def _bar_div(klass: str, n: int, peak: int) -> str:
    pct = (n / peak * 100) if peak else 0
    return (f'<div class="bar-track"><div class="bar-fill {klass}" '
            f'style="width:{pct:.1f}%"></div></div>')


def render_html(r: Report) -> str:
    rows = []
    out = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
           '<title>Runs Dashboard</title>',
           f'<style>{HTML_CSS}</style></head><body>']
    out.append(f'<h1>Runs Dashboard</h1>')
    out.append(f'<div class="meta">Generated '
               f'{html.escape(r.generated_at.astimezone().strftime("%Y-%m-%d %H:%M %Z"))} '
               f'· runs at <code>{html.escape(str(r.runs_dir))}</code> · '
               f'window {r.window_days} days</div>')

    # Cards
    out.append('<h2>Per-script health</h2>')
    if not r.scripts:
        out.append('<div class="empty">No run directories found.</div>')
    else:
        out.append('<div class="cards">')
        for s in r.scripts:
            last = s.last_run.timestamp.strftime("%Y-%m-%d %H:%M") if s.last_run else "—"
            out.append(
                '<div class="card">'
                f'<div><span class="id">#{html.escape(s.script_id)}</span>'
                f'<span class="name">{html.escape(s.display_name)}</span></div>'
                f'<div class="stats">'
                f'<span>{s.run_count} runs</span>'
                f'<span class="stat-applied">{s.applied} applied</span>'
                f'<span class="stat-error">{s.errored} errors</span>'
                f'<span>{s.total_jobs} jobs</span>'
                f'</div>'
                f'<div class="last">last run: {html.escape(last)}</div>'
                '</div>'
            )
        out.append('</div>')

    # Timeline
    out.append(f'<h2>Applications per day (last {r.window_days} days)</h2>')
    peak = max(r.daily_applied.values() or [0])
    if peak == 0:
        out.append('<div class="empty">No applications recorded in this window.</div>')
    else:
        out.append('<table><tr><th>Date</th><th>Applications</th><th></th></tr>')
        for d, n in r.daily_applied.items():
            out.append(f'<tr><td>{d.isoformat()}</td>'
                       f'<td>{n}</td>'
                       f'<td>{_bar_div("fill-day", n, peak)}</td></tr>')
        out.append('</table>')

    # Funnel
    out.append('<h2>Pipeline funnel — job_tracker.json</h2>')
    if not r.pipeline_funnel:
        out.append('<div class="empty">No job_tracker.json yet — run '
                   '<code>043_gmail_job_tracker.py</code>.</div>')
    else:
        peak_f = max(r.pipeline_funnel.values())
        out.append('<table><tr><th>Status</th><th>Count</th><th></th></tr>')
        for status, n in r.pipeline_funnel.items():
            out.append(f'<tr><td>{html.escape(status)}</td>'
                       f'<td>{n}</td>'
                       f'<td>{_bar_div("fill-" + status, n, peak_f)}</td></tr>')
        out.append('</table>')

    # Recent runs
    out.append('<h2>Recent runs (latest 20)</h2>')
    if not r.recent_runs:
        out.append('<div class="empty">None.</div>')
    else:
        out.append('<table><tr><th>Time</th><th>#</th><th>Script</th>'
                   '<th>Applied</th><th>Errors</th><th></th></tr>')
        for rec in r.recent_runs:
            sid, name = SCRIPT_LABELS.get(rec.prefix, ("???", rec.prefix))
            applied = rec.status_counts.get("applied", 0)
            errored = rec.status_counts.get("error", 0)
            tag = ('<span class="tag-fail">✗</span>' if errored
                   else '<span class="tag-ok">✓</span>' if applied
                   else '<span class="tag-dim">·</span>')
            out.append(f'<tr><td>{rec.timestamp.strftime("%Y-%m-%d %H:%M")}</td>'
                       f'<td>{html.escape(sid)}</td>'
                       f'<td>{html.escape(name)}</td>'
                       f'<td>{applied}</td><td>{errored}</td><td>{tag}</td></tr>')
        out.append('</table>')

    out.append('</body></html>')
    return "".join(out)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-dir", default="runs", type=Path)
    parser.add_argument("--tracker", default="job_tracker.json", type=Path)
    parser.add_argument("--terminal", action="store_true",
                        help="Print ANSI summary to stdout (default writes HTML)")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI colors in --terminal mode")
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--out", type=Path, default=None,
                        help="HTML output path (default: <runs-dir>/dashboard.html)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    report = build_report(args.runs_dir, args.tracker, args.window_days)

    if args.terminal:
        use_color = sys.stdout.isatty() and not args.no_color
        print(render_terminal(report, color=use_color))
        return

    out_path = args.out or (args.runs_dir / "dashboard.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_html(report))
    log.info(f"Wrote {out_path}  ({out_path.stat().st_size:,} bytes)")
    log.info(f"Open with: open {out_path}")


if __name__ == "__main__":
    main()
