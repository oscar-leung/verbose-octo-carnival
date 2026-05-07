"""Local-only HTTP dashboard. Serves an HTML page with charts and exposes
JSON endpoints for the day's summary, snippet, and notes.

Bound to 127.0.0.1 by default -- nothing leaves your machine.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from .storage import Store
from .summary import fmt_duration, render_snippet, render_text, summarize


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Activity Tracker</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto;
         padding: 0 1rem; line-height: 1.5; }
  h1 { margin-bottom: 0.2rem; }
  .meta { color: #888; margin-bottom: 1.5rem; }
  .row { display: flex; gap: 2rem; flex-wrap: wrap; }
  .col { flex: 1; min-width: 320px; }
  .bar { display: flex; align-items: center; margin: 4px 0; gap: 8px; }
  .bar .name { width: 140px; font-weight: 600; }
  .bar .track { flex: 1; background: #eee2; border-radius: 4px; height: 14px;
                overflow: hidden; }
  .bar .fill { height: 100%; background: linear-gradient(90deg,#4a8cff,#6ad); }
  .bar .val { width: 90px; text-align: right; color: #888; font-variant-numeric: tabular-nums; }
  pre { background: #8881; padding: 1rem; border-radius: 6px; overflow-x: auto; }
  textarea { width: 100%; min-height: 60px; font: inherit; padding: 8px;
             border-radius: 6px; border: 1px solid #8884; box-sizing: border-box; }
  button { padding: 8px 14px; border: 0; border-radius: 6px; background: #4a8cff;
           color: white; font: inherit; cursor: pointer; }
  button:hover { filter: brightness(1.1); }
  input[type=date] { font: inherit; padding: 4px 8px; }
  details { margin-top: 1.5rem; }
  ul.notes { padding-left: 1.2rem; }
</style>
</head>
<body>
<h1>Activity Tracker</h1>
<div class="meta">
  <input type="date" id="day">
  <span id="total"></span>
</div>

<div class="row">
  <div class="col">
    <h3>By category</h3>
    <div id="cats"></div>
  </div>
  <div class="col">
    <h3>By app</h3>
    <div id="apps"></div>
  </div>
</div>

<details open>
  <summary><strong>Notes / highlights</strong></summary>
  <p>Jot down what mattered today. These get included in the snippet.</p>
  <textarea id="note" placeholder="e.g. Shipped activity tracker MVP, paired with X on Y"></textarea>
  <p><button onclick="addNote()">Add note</button></p>
  <ul class="notes" id="noteList"></ul>
</details>

<details>
  <summary><strong>Snippet (Markdown)</strong> &mdash; paste into your README, journal, or demo</summary>
  <pre id="snippet"></pre>
  <button onclick="copySnippet()">Copy snippet</button>
</details>

<script>
const $ = sel => document.querySelector(sel);
function fmt(s){ s=Math.round(s); const h=Math.floor(s/3600), m=Math.floor((s%3600)/60);
  if(h) return h+"h "+String(m).padStart(2,"0")+"m";
  if(m) return m+"m "+(s%60)+"s"; return s+"s"; }

function renderBars(el, items, total){
  el.innerHTML = "";
  for(const b of items){
    const pct = total ? (b.seconds/total*100) : 0;
    const row = document.createElement("div"); row.className="bar";
    row.innerHTML = `<div class="name">${b.name}</div>
      <div class="track"><div class="fill" style="width:${pct}%"></div></div>
      <div class="val">${fmt(b.seconds)}</div>`;
    el.appendChild(row);
  }
}

async function load(){
  const day = $("#day").value;
  const r = await fetch("/api/summary?day="+encodeURIComponent(day));
  const d = await r.json();
  $("#total").textContent = "  Tracked: " + fmt(d.total);
  renderBars($("#cats"), d.by_category, d.total);
  renderBars($("#apps"), d.by_app.slice(0,10), d.total);
  $("#noteList").innerHTML = d.notes.map(n=>`<li>${escape(n)}</li>`).join("");
  const s = await fetch("/api/snippet?day="+encodeURIComponent(day));
  $("#snippet").textContent = await s.text();
}
function escape(s){ return s.replace(/[&<>]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
async function addNote(){
  const text = $("#note").value.trim(); if(!text) return;
  await fetch("/api/note", {method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({text, day: $("#day").value})});
  $("#note").value = ""; load();
}
function copySnippet(){ navigator.clipboard.writeText($("#snippet").textContent); }

const today = new Date().toISOString().slice(0,10);
$("#day").value = today;
$("#day").addEventListener("change", load);
load();
setInterval(load, 30000);
</script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    store: Store  # set on the server instance

    def log_message(self, fmt, *args):  # quiet
        return

    def _json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _text(self, body: str, ctype: str = "text/plain; charset=utf-8") -> None:
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        u = urlparse(self.path)
        q = parse_qs(u.query)
        day = (q.get("day") or [None])[0] or None
        store: Store = self.server.store  # type: ignore[attr-defined]

        if u.path == "/" or u.path == "/index.html":
            self._text(INDEX_HTML, "text/html; charset=utf-8")
            return
        if u.path == "/api/summary":
            s = summarize(store, day)
            self._json({
                "day": s.day,
                "total": s.total,
                "by_category": [
                    {"name": b.name, "seconds": b.seconds,
                     "top_titles": b.top_titles(3)} for b in s.by_category
                ],
                "by_app": [
                    {"name": b.name, "seconds": b.seconds} for b in s.by_app
                ],
                "notes": s.notes,
            })
            return
        if u.path == "/api/snippet":
            s = summarize(store, day)
            self._text(render_snippet(s), "text/markdown; charset=utf-8")
            return
        if u.path == "/api/text":
            s = summarize(store, day)
            self._text(render_text(s))
            return
        self.send_error(404)

    def do_POST(self):  # noqa: N802
        u = urlparse(self.path)
        store: Store = self.server.store  # type: ignore[attr-defined]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            payload = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._json({"error": "invalid json"}, 400)
            return
        if u.path == "/api/note":
            text = (payload.get("text") or "").strip()
            day = payload.get("day") or None
            if not text:
                self._json({"error": "empty"}, 400)
                return
            store.add_note(text, day=day)
            self._json({"ok": True})
            return
        self.send_error(404)


def serve(host: str = "127.0.0.1", port: int = 8765,
          store: Optional[Store] = None) -> None:
    store = store or Store()
    server = ThreadingHTTPServer((host, port), _Handler)
    server.store = store  # type: ignore[attr-defined]
    print(f"Activity dashboard: http://{host}:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()
