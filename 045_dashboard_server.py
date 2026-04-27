"""
Job Tracker Web Dashboard — localhost Flask app.
─────────────────────────────────────────────────
Live UI on top of 043 (Gmail reader) and 044 (rendering).

  python3 045_dashboard_server.py            # http://127.0.0.1:5050
  python3 045_dashboard_server.py --port 8080
  python3 045_dashboard_server.py --host 0.0.0.0   # share on LAN (no auth!)

Pages:
  /                    Funnel + searchable application table
  /entry/<key>         Per-application timeline (every email we have on this thread)
  /scripts             Embedded 044 dashboard (per-script health, daily timeline)
  /api/tracker         Raw job_tracker.json
  /api/refresh  POST   Trigger a Gmail rescan (kicks 043's pipeline in a thread)

The "Scan Gmail now" button calls /api/refresh; the server runs the same code
path as the CLI in 043 — OAuth via gmail_oauth_client.json, classification,
forward-only status promotion, write-back to job_tracker.json. Refresh status
is reported as JSON so the page can show progress without reloading.

This is deliberately a single-process, single-user, *localhost* tool. Do not
expose it to the public internet without adding auth and moving OAuth tokens
to a secret store — the server reads/writes gmail_token.json on disk.

Install: pip install flask
"""

import argparse
import importlib.util
import json
import logging
import sys
import threading
import time
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACKER_PATH = ROOT / "job_tracker.json"

log = logging.getLogger("dashboard_server")


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem.replace(" ", "_"), path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Sibling modules — file names start with digits so we go through importlib.
_tracker_mod = _load_module(ROOT / "043_gmail_job_tracker.py")
_runs_mod = _load_module(ROOT / "044_runs_dashboard.py")


# ── Refresh job state (in-memory) ─────────────────────────────────────────────
_refresh_state = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "last_result": None,        # {"new": int, "changed": int, "scanned": int}
    "last_error": None,
}
_refresh_lock = threading.Lock()


def _run_refresh(days: int) -> None:
    started = datetime.now(timezone.utc).isoformat()
    with _refresh_lock:
        _refresh_state["running"] = True
        _refresh_state["started_at"] = started
        _refresh_state["last_error"] = None

    try:
        service = _tracker_mod.gmail_service()
        query = _tracker_mod.build_query(days)
        msg_ids = _tracker_mod.list_message_ids(service, query)

        entries = _tracker_mod.load_tracker()
        new_count = changed_count = parsed_count = 0
        for mid in msg_ids:
            msg = _tracker_mod.fetch_message(service, mid)
            parsed = _tracker_mod.parse_email(msg)
            if not parsed:
                continue
            parsed_count += 1
            is_new, is_change = _tracker_mod.merge(entries, parsed)
            new_count += int(is_new)
            changed_count += int(is_change)
        _tracker_mod.save_tracker(entries)

        with _refresh_lock:
            _refresh_state["last_result"] = {
                "new": new_count,
                "changed": changed_count,
                "scanned": parsed_count,
                "messages_total": len(msg_ids),
            }
    except Exception as e:
        log.exception("refresh failed")
        with _refresh_lock:
            _refresh_state["last_error"] = f"{type(e).__name__}: {e}"
    finally:
        with _refresh_lock:
            _refresh_state["running"] = False
            _refresh_state["finished_at"] = datetime.now(timezone.utc).isoformat()


# ── HTML rendering ────────────────────────────────────────────────────────────
PAGE_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
       margin: 0; background: #fafafa; color: #1f1f1f; }
@media (prefers-color-scheme: dark) {
  body { background: #111; color: #eee; }
  header { background: #1b1b1b; border-color: #2a2a2a; }
  .panel { background: #1b1b1b; border-color: #2a2a2a; }
  th { background: #1f1f1f; color: #ddd; }
  tr:nth-child(even) td { background: #161616; }
  input, button, select { background: #222; color: #eee; border-color: #333; }
  .pill { background: #222; }
  .meta, .empty { color: #888; }
  a { color: #6cb2ff; }
}
header { display: flex; align-items: center; gap: 16px; padding: 14px 24px;
         background: #fff; border-bottom: 1px solid #eaeaea; position: sticky; top: 0; z-index: 10;}
header h1 { font-size: 17px; margin: 0; }
header nav a { margin-right: 12px; font-size: 14px; }
header .spacer { flex: 1; }
header #refresh-status { font-size: 12px; color: #888; }
main { padding: 18px 24px 32px; max-width: 1200px; margin: 0 auto; }
.panel { background: #fff; border: 1px solid #eaeaea; border-radius: 10px;
         padding: 14px 18px; margin-bottom: 18px; }
h2 { margin: 0 0 12px; font-size: 15px; letter-spacing: .04em;
     text-transform: uppercase; color: #555; }
.funnel { display: flex; gap: 8px; flex-wrap: wrap; }
.funnel .pill { padding: 8px 14px; border-radius: 20px; background: #f3f3f3;
                font-size: 13px; display: flex; gap: 8px; align-items: center; }
.funnel .pill .n { font-weight: 700; font-size: 15px; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.dot.applied    { background: #3498db; }
.dot.assessment { background: #f1c40f; }
.dot.interview  { background: #9b59b6; }
.dot.offer      { background: #16a085; }
.dot.rejection  { background: #e74c3c; }
.dot.ghosted    { background: #95a5a6; }
.dot.unknown    { background: #bdc3c7; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid #eee; }
th { background: #f3f3f3; font-weight: 600; font-size: 12px; cursor: pointer; user-select: none; }
tr:nth-child(even) td { background: #fafafa; }
tr:hover td { background: #f0f7ff; cursor: pointer; }
.controls { display: flex; gap: 10px; margin-bottom: 12px; align-items: center; }
.controls input, .controls select {
  padding: 6px 9px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.controls input { flex: 1; max-width: 320px; }
button { padding: 6px 12px; border: 1px solid #ddd; border-radius: 6px;
         background: #fff; cursor: pointer; font-size: 13px; }
button:hover { background: #f4f4f4; }
button.primary { background: #2563eb; color: #fff; border-color: #2563eb; }
button.primary:hover { background: #1e4fd6; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.timeline { list-style: none; padding: 0; margin: 0; }
.timeline li { padding: 10px 0; border-bottom: 1px solid #eee; }
.timeline .when { font-size: 12px; color: #888; }
.timeline .what { font-weight: 600; }
.timeline .subj { color: #555; font-size: 13px; }
.empty { color: #999; font-style: italic; padding: 18px 0; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
.kvs { display: grid; grid-template-columns: max-content 1fr; gap: 4px 14px; font-size: 13px; }
.kvs dt { color: #888; }
.tag { font-size: 11px; padding: 2px 8px; border-radius: 12px;
       background: #eee; color: #333; }
.tag.applied    { background: #d6e9ff; color: #14467a; }
.tag.assessment { background: #fef3cd; color: #6f5800; }
.tag.interview  { background: #ead6ff; color: #4d2378; }
.tag.offer      { background: #c9efe1; color: #0a4f3a; }
.tag.rejection  { background: #fad7d2; color: #721b12; }
.tag.ghosted    { background: #e6e6e6; color: #555; }
.tag.unknown    { background: #eee; color: #555; }
"""

PAGE_JS = """
async function refreshNow(button) {
  button.disabled = true;
  document.getElementById('refresh-status').textContent = 'Scanning Gmail…';
  try {
    const r = await fetch('/api/refresh', {method:'POST'});
    if (!r.ok) throw new Error('HTTP '+r.status);
    pollStatus();
  } catch (e) {
    document.getElementById('refresh-status').textContent = 'Refresh failed: '+e;
    button.disabled = false;
  }
}
async function pollStatus() {
  const r = await fetch('/api/refresh-status');
  const s = await r.json();
  const el = document.getElementById('refresh-status');
  if (s.running) {
    el.textContent = 'Scanning Gmail… (started '+formatRel(s.started_at)+')';
    setTimeout(pollStatus, 1500);
  } else if (s.last_error) {
    el.textContent = 'Refresh error: '+s.last_error;
    document.querySelector('button.primary').disabled = false;
  } else if (s.last_result) {
    const lr = s.last_result;
    el.textContent = 'Done — '+lr.new+' new · '+lr.changed+' status changes · '+lr.scanned+' scanned';
    setTimeout(()=>location.reload(), 800);
  } else {
    el.textContent = '';
    document.querySelector('button.primary').disabled = false;
  }
}
function formatRel(iso) {
  if (!iso) return '';
  const s = (Date.now() - new Date(iso).getTime())/1000;
  return Math.round(s)+'s ago';
}
function applyFilter() {
  const q = (document.getElementById('q').value || '').toLowerCase();
  const status = document.getElementById('status-filter').value;
  document.querySelectorAll('tbody tr').forEach(tr => {
    const matchesQ = !q || tr.dataset.search.includes(q);
    const matchesS = !status || tr.dataset.status === status;
    tr.style.display = (matchesQ && matchesS) ? '' : 'none';
  });
}
document.addEventListener('DOMContentLoaded', () => {
  const q = document.getElementById('q');
  if (q) { q.addEventListener('input', applyFilter); }
  const sf = document.getElementById('status-filter');
  if (sf) { sf.addEventListener('change', applyFilter); }
  document.querySelectorAll('tbody tr').forEach(tr => {
    tr.addEventListener('click', () => { window.location = tr.dataset.href; });
  });
  // resume polling if user navigated back during a refresh
  pollStatus();
});
"""


def _layout(title: str, body: str) -> str:
    return (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<title>{escape(title)}</title>'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<style>{PAGE_CSS}</style></head>'
        f'<body>'
        f'<header>'
        f'<h1>Job Tracker</h1>'
        f'<nav><a href="/">Applications</a><a href="/scripts">Script health</a>'
        f'<a href="/api/tracker">API</a></nav>'
        f'<div class="spacer"></div>'
        f'<span id="refresh-status"></span>'
        f'<button class="primary" onclick="refreshNow(this)">Scan Gmail now</button>'
        f'</header>'
        f'<main>{body}</main>'
        f'<script>{PAGE_JS}</script>'
        f'</body></html>'
    )


def _funnel_html(funnel: dict[str, int]) -> str:
    if not funnel:
        return ('<div class="panel"><h2>Pipeline</h2>'
                '<div class="empty">No tracker data yet — click '
                '<b>Scan Gmail now</b> to populate.</div></div>')
    pills = []
    for status, n in funnel.items():
        pills.append(
            f'<a class="pill" href="?status={escape(status)}">'
            f'<span class="dot {escape(status)}"></span>'
            f'<span>{escape(status)}</span><span class="n">{n}</span></a>'
        )
    return f'<div class="panel"><h2>Pipeline</h2><div class="funnel">{"".join(pills)}</div></div>'


def _entries_table(entries: dict, status_filter: str | None) -> str:
    items = sorted(
        entries.items(),
        key=lambda kv: kv[1].get("last_updated") or "",
        reverse=True,
    )
    if status_filter:
        items = [(k, v) for k, v in items if v.get("status") == status_filter]
    if not items:
        return '<div class="panel"><div class="empty">No matching applications.</div></div>'

    rows = []
    for key, e in items:
        company = e.get("company") or "(unknown)"
        role = e.get("role") or "—"
        loc = e.get("location") or ""
        status = e.get("status", "unknown")
        last = (e.get("last_updated") or "")[:10]
        first = (e.get("first_seen") or "")[:10]
        search_blob = " ".join([company, role, loc, status]).lower()
        rows.append(
            f'<tr data-status="{escape(status)}" '
            f'data-search="{escape(search_blob)}" '
            f'data-href="/entry/{escape(key)}">'
            f'<td>{escape(company)}</td>'
            f'<td>{escape(role)}</td>'
            f'<td>{escape(loc)}</td>'
            f'<td><span class="tag {escape(status)}">{escape(status)}</span></td>'
            f'<td>{escape(first)}</td>'
            f'<td>{escape(last)}</td>'
            f'</tr>'
        )

    options = ['<option value="">all statuses</option>']
    for s in ["applied", "assessment", "interview", "offer", "rejection", "ghosted", "unknown"]:
        sel = " selected" if status_filter == s else ""
        options.append(f'<option value="{s}"{sel}>{s}</option>')

    return (
        f'<div class="panel">'
        f'<h2>Applications ({len(items)})</h2>'
        f'<div class="controls">'
        f'<input id="q" placeholder="Search company, role, location…" />'
        f'<select id="status-filter">{"".join(options)}</select>'
        f'</div>'
        f'<table>'
        f'<thead><tr><th>Company</th><th>Role</th><th>Location</th>'
        f'<th>Status</th><th>First seen</th><th>Last update</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        f'</table>'
        f'</div>'
    )


def _entry_detail_html(key: str, entry: dict) -> str:
    company = entry.get("company") or "(unknown)"
    role = entry.get("role") or "—"
    status = entry.get("status", "unknown")
    history = sorted(entry.get("history") or [], key=lambda h: h.get("date", ""), reverse=True)

    items = []
    for h in history:
        date_s = (h.get("date") or "")[:16].replace("T", " ")
        items.append(
            f'<li>'
            f'<div class="when">{escape(date_s)}</div>'
            f'<div class="what"><span class="tag {escape(h.get("status",""))}">'
            f'{escape(h.get("status",""))}</span></div>'
            f'<div class="subj">{escape(h.get("subject",""))}</div>'
            f'</li>'
        )
    timeline = ('<ul class="timeline">' + "".join(items) + "</ul>"
                if items else '<div class="empty">No email history recorded.</div>')

    threads = entry.get("gmail_thread_ids") or []
    thread_links = "".join(
        f'<a href="https://mail.google.com/mail/u/0/#inbox/{escape(t)}" target="_blank">{escape(t[:8])}</a> '
        for t in threads
    )

    return (
        f'<div class="panel">'
        f'<a href="/">← All applications</a>'
        f'<h2 style="margin-top:8px">{escape(company)} — {escape(role)}</h2>'
        f'<dl class="kvs">'
        f'<dt>Status</dt><dd><span class="tag {escape(status)}">{escape(status)}</span></dd>'
        f'<dt>Location</dt><dd>{escape(entry.get("location","") or "—")}</dd>'
        f'<dt>First seen</dt><dd>{escape((entry.get("first_seen") or "")[:16].replace("T"," "))}</dd>'
        f'<dt>Last update</dt><dd>{escape((entry.get("last_updated") or "")[:16].replace("T"," "))}</dd>'
        f'<dt>Gmail threads</dt><dd>{thread_links or "—"}</dd>'
        f'</dl>'
        f'</div>'
        f'<div class="panel">'
        f'<h2>Email timeline</h2>'
        f'{timeline}'
        f'</div>'
    )


# ── Flask app ─────────────────────────────────────────────────────────────────
def make_app():
    try:
        from flask import Flask, abort, jsonify, redirect, request
    except ImportError:
        sys.exit("pip install flask")

    app = Flask(__name__)

    def _read_tracker() -> dict:
        if not TRACKER_PATH.exists():
            return {}
        try:
            return json.loads(TRACKER_PATH.read_text()).get("entries", {}) or {}
        except Exception as e:
            log.warning("bad tracker json: %s", e)
            return {}

    @app.get("/")
    def index():
        entries = _read_tracker()
        # Funnel respects the actual stored statuses
        from collections import Counter
        cnt = Counter(e.get("status", "unknown") for e in entries.values())
        order = ["applied", "assessment", "interview", "offer", "rejection", "ghosted", "unknown"]
        funnel = {k: cnt[k] for k in order if cnt[k]}
        status_filter = request.args.get("status") or None
        body = _funnel_html(funnel) + _entries_table(entries, status_filter)
        return _layout("Job Tracker", body)

    @app.get("/entry/<path:key>")
    def entry_detail(key):
        entries = _read_tracker()
        if key not in entries:
            abort(404)
        return _layout(f"{entries[key].get('company','')} — Job Tracker",
                       _entry_detail_html(key, entries[key]))

    @app.get("/scripts")
    def scripts():
        # Reuse 044's HTML renderer in-place.
        report = _runs_mod.build_report(
            runs_dir=ROOT / "runs",
            tracker_path=TRACKER_PATH,
            window_days=30,
        )
        # 044 emits a full <html>; we strip and inline its body to keep a single
        # consistent header.
        full = _runs_mod.render_html(report)
        body = full.split("<body>", 1)[-1].rsplit("</body>", 1)[0]
        return _layout("Script health", body)

    @app.get("/api/tracker")
    def api_tracker():
        return jsonify({"entries": _read_tracker()})

    @app.get("/api/refresh-status")
    def api_refresh_status():
        with _refresh_lock:
            return jsonify(dict(_refresh_state))

    @app.post("/api/refresh")
    def api_refresh():
        with _refresh_lock:
            if _refresh_state["running"]:
                return jsonify({"status": "already-running"}), 409
        days = int(request.args.get("days", 7))
        threading.Thread(target=_run_refresh, args=(days,), daemon=True).start()
        # tiny sleep so the polling loop sees running=True on its first call
        time.sleep(0.05)
        return jsonify({"status": "started", "days": days})

    return app


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    app = make_app()
    log.info(f"Job Tracker dashboard → http://{args.host}:{args.port}")
    if args.host != "127.0.0.1":
        log.warning("Listening on %s — this exposes Gmail-derived data without "
                    "auth. Use ssh tunnel or add a reverse proxy with login.", args.host)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
