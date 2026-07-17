"""Safeway Deal Tracker — localhost Flask app. "Stocks, but for groceries."

UI on top of the history DB built by 047 (which ingests runs of 046).

  python3 047_safeway_history_db.py --demo     # seed data first (or --fetch)
  python3 048_safeway_app.py                   # http://127.0.0.1:5057
  python3 048_safeway_app.py --port 8080

Pages:
  /                    This week's deals — searchable, filterable, sortable,
                       each card has a price-history sparkline + deal verdict
  /product/<key>       Per-product "stock chart": full price timeline,
                       all-time low, average, BUY / WAIT verdict
  /api/deals           Current deals as JSON
  /api/product/<key>   One product's full history as JSON
  /api/stats           Topline stats as JSON

The verdict logic is the whole point: a deal is only "good" relative to that
product's own history. $2.99 chicken means nothing until you know it hit
$2.49 twice last month. Open on your phone and "Add to Home Screen" for the
iOS-app feel — the layout is responsive and has the apple-web-app metas.

Localhost tool, single user, no auth — don't expose publicly as-is.
"""

from __future__ import annotations

import argparse
import sqlite3
import statistics
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request
from jinja2 import DictLoader

ROOT = Path(__file__).parent
DB_PATH = ROOT / "runs" / "safeway" / "safeway.db"

CATEGORY_EMOJI = {
    "Meat & Seafood": "🥩", "Deli": "🍗", "Dairy & Eggs": "🥚",
    "Produce": "🥑", "Bakery": "🥖", "Beverages": "☕", "Snacks": "🍿",
    "Frozen": "🧊", "Pantry": "🥫", "Household": "🧻",
}
DEFAULT_EMOJI = "🛒"

VERDICTS = {
    "all-time-low": ("🔥", "ALL-TIME LOW", "Lowest price ever recorded — stock up"),
    "great":        ("✅", "GREAT PRICE", "Cheaper than 75% of past deals"),
    "good":         ("👍", "GOOD PRICE", "Below this product's average deal price"),
    "typical":      ("⏳", "TYPICAL", "This deal comes back — waiting may pay off"),
    "new":          ("🆕", "FIRST SIGHTING", "No history yet for this product"),
}


# ── Data access ──────────────────────────────────────────────────────────────

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(app.config["DB_PATH"])
    conn.row_factory = sqlite3.Row
    return conn


def default_store(conn) -> str:
    """Store from the most recent ingest — the one the user is tracking now."""
    row = conn.execute(
        "SELECT store_id FROM runs ORDER BY captured_at DESC, id DESC LIMIT 1"
    ).fetchone()
    return row["store_id"] if row else ""


def store_filter(store: str) -> tuple[str, tuple]:
    """SQL fragment scoping a query to one store. Without this, ingesting two
    stores into one DB would silently mix their prices in every stat."""
    return (" AND store_id = ?", (store,)) if store else ("", ())


def latest_run_date(conn, store: str = "") -> str | None:
    frag, params = store_filter(store)
    row = conn.execute(
        f"SELECT MAX(captured_at) d FROM deal_snapshots WHERE 1=1{frag}", params
    ).fetchone()
    return row["d"] if row and row["d"] else None


def product_history(conn, key: str, store: str = "") -> list[sqlite3.Row]:
    frag, params = store_filter(store)
    return conn.execute(
        f"SELECT * FROM deal_snapshots WHERE product_key = ?{frag} ORDER BY captured_at",
        (key, *params),
    ).fetchall()


def verdict_for(current_price: float | None, past_prices: list[float],
                times_seen: int = 1) -> str:
    """Rate the current price against this product's own PAST deals (the
    current week must be excluded by the caller — comparing a price against
    itself would make every recurring deal a perpetual 'all-time low')."""
    if times_seen <= 1:
        return "new"
    if current_price is None:
        return "typical"  # unpriced offer (BOGO/coupon) with real history
    if len(past_prices) < 2:
        return "new"
    lo = min(past_prices)
    if current_price < lo:
        return "all-time-low"
    q = statistics.quantiles(past_prices, n=4)
    if current_price <= q[0]:
        return "great"
    if current_price < statistics.mean(past_prices):
        return "good"
    return "typical"


def sparkline_svg(prices: list[float | None], w: int = 110, h: int = 30) -> str:
    """Tiny inline price chart for deal cards. Numeric-only output (XSS-safe)."""
    pts = [p for p in prices if p is not None]
    if len(pts) < 2:
        return ""
    lo, hi = min(pts), max(pts)
    span = (hi - lo) or 1.0
    coords, i = [], 0
    n = len(pts)
    for p in pts:
        x = 2 + i * (w - 4) / (n - 1)
        y = 2 + (h - 4) * (1 - (p - lo) / span)
        coords.append(f"{x:.1f},{y:.1f}")
        i += 1
    last = coords[-1].split(",")
    return (
        f'<svg viewBox="0 0 {w} {h}" class="spark" preserveAspectRatio="none">'
        f'<polyline points="{" ".join(coords)}" fill="none" stroke="currentColor" '
        f'stroke-width="1.5" stroke-linejoin="round"/>'
        f'<circle cx="{last[0]}" cy="{last[1]}" r="2.4" fill="currentColor"/></svg>'
    )


def timeline_chart_svg(labels: list[str], prices: list[float | None], low: float,
                       w: int = 840, h: int = 280) -> str:
    """Server-rendered price-history chart — no JS or CDN dependency, so it
    works offline and renders identically everywhere. Green dots mark the
    all-time low; hover any dot for the exact price (SVG <title>)."""
    pts = [(i, p) for i, p in enumerate(prices) if p is not None]
    if not pts:
        return '<div class="empty">No priced deals recorded yet.</div>'
    vals = [p for _, p in pts]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.15 or max(lo * 0.1, 1.0)
    y0, y1 = lo - pad, hi + pad
    L, R, T, B = 54, 14, 14, 30
    iw, ih = w - L - R, h - T - B
    n = len(labels)

    def x(i: int) -> float:
        return L + iw * i / max(n - 1, 1)

    def y(p: float) -> float:
        return T + ih * (1 - (p - y0) / (y1 - y0))

    parts = [f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto" '
             f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="price history">']
    for k in range(5):
        gy = T + ih * k / 4
        gval = y1 - (y1 - y0) * k / 4
        parts.append(f'<line x1="{L}" y1="{gy:.1f}" x2="{w - R}" y2="{gy:.1f}" stroke="#21262d"/>')
        parts.append(f'<text x="{L - 8}" y="{gy + 4:.1f}" text-anchor="end" '
                     f'fill="#8b949e" font-size="11">${gval:.2f}</text>')
    step = max(1, (n + 9) // 10)
    for i, lab in enumerate(labels):
        if i % step == 0:
            parts.append(f'<text x="{x(i):.1f}" y="{h - 8}" text-anchor="middle" '
                         f'fill="#8b949e" font-size="11">{lab}</text>')
    line = " ".join(f"{x(i):.1f},{y(p):.1f}" for i, p in pts)
    floor = T + ih
    parts.append(f'<polygon points="{x(pts[0][0]):.1f},{floor:.1f} {line} '
                 f'{x(pts[-1][0]):.1f},{floor:.1f}" fill="rgba(255,77,77,.10)"/>')
    parts.append(f'<polyline points="{line}" fill="none" stroke="#ff4d4d" '
                 f'stroke-width="2" stroke-linejoin="round"/>')
    for i, p in pts:
        is_low = abs(p - low) < 1e-9
        color = "#3fb950" if is_low else "#ff4d4d"
        r = 5.5 if is_low else 4
        parts.append(f'<circle cx="{x(i):.1f}" cy="{y(p):.1f}" r="{r}" fill="{color}" '
                     f'stroke="#0d1117" stroke-width="1.5">'
                     f'<title>{labels[i]} — ${p:.2f}</title></circle>')
    parts.append("</svg>")
    return "".join(parts)


def build_current_deals(conn, store: str = "") -> tuple[list[dict], str | None]:
    """Current week's deals, each enriched with history stats + verdict."""
    latest = latest_run_date(conn, store)
    if not latest:
        return [], None
    frag, params = store_filter(store)
    rows = conn.execute(
        f"""SELECT s.*, p.name pname, p.brand, p.category, p.image_url
           FROM deal_snapshots s JOIN products p USING (product_key)
           WHERE s.captured_at = ?{frag}""",
        (latest, *params),
    ).fetchall()
    # One pass over all history for sparklines + stats, grouped in Python.
    hist: dict[str, list[tuple[str, float | None]]] = {}
    for r in conn.execute(
        f"SELECT product_key, captured_at, price_value FROM deal_snapshots "
        f"WHERE 1=1{frag} ORDER BY captured_at", params
    ):
        hist.setdefault(r["product_key"], []).append((r["captured_at"], r["price_value"]))
    deals = []
    for r in rows:
        series = hist.get(r["product_key"], [])
        prices = [p for _, p in series if p is not None]
        past = [p for d_, p in series if p is not None and d_ != latest]
        v = verdict_for(r["price_value"], past, times_seen=len(series))
        deals.append({
            "key": r["product_key"], "name": r["pname"], "brand": r["brand"],
            "category": r["category"], "image_url": r["image_url"],
            "emoji": CATEGORY_EMOJI.get(r["category"], DEFAULT_EMOJI),
            "price_text": r["price_text"], "price_value": r["price_value"],
            "savings_text": r["savings_text"], "savings_value": r["savings_value"],
            "offer_type": r["offer_type"], "end_date": r["end_date"],
            "times_seen": len(series),
            "all_time_low": min(prices) if prices else None,
            "avg_price": round(statistics.mean(prices), 2) if prices else None,
            "verdict": v, "verdict_emoji": VERDICTS[v][0], "verdict_label": VERDICTS[v][1],
            "spark": sparkline_svg([p for _, p in series]),
        })
    return deals, latest


def fmt_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%b %-d")
    except (ValueError, TypeError):
        return iso or ""


# ── Flask app + templates ────────────────────────────────────────────────────

app = Flask(__name__)
app.config["DB_PATH"] = str(DB_PATH)
app.jinja_env.filters["fmtdate"] = fmt_date

BASE_HTML = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0d1117">
<title>{% block title %}Safeway Deal Tracker{% endblock %}</title>
<style>
:root { --bg:#0d1117; --card:#161b22; --border:#21262d; --text:#e6edf3;
        --muted:#8b949e; --red:#ff4d4d; --green:#3fb950; --amber:#d29922; }
* { box-sizing:border-box; margin:0; }
body { background:var(--bg); color:var(--text); font:15px/1.5 -apple-system,
       BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; padding-bottom:40px; }
a { color:inherit; text-decoration:none; }
header { position:sticky; top:0; z-index:10; background:rgba(13,17,23,.92);
         backdrop-filter:blur(8px); border-bottom:1px solid var(--border);
         padding:14px 20px; display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }
header h1 { font-size:19px; } header h1 .logo { color:var(--red); }
header .sub { color:var(--muted); font-size:13px; }
.wrap { max-width:1180px; margin:0 auto; padding:20px; }
.stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
         gap:12px; margin-bottom:20px; }
.stat { background:var(--card); border:1px solid var(--border); border-radius:12px;
        padding:14px 16px; }
.stat .num { font-size:24px; font-weight:700; } .stat .lbl { color:var(--muted); font-size:12px; }
.controls { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; align-items:center; }
.controls input, .controls select { background:var(--card); color:var(--text);
        border:1px solid var(--border); border-radius:8px; padding:8px 12px; font-size:14px; }
.controls input { flex:1; min-width:180px; }
.chips { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }
.chip { border:1px solid var(--border); background:var(--card); border-radius:999px;
        padding:5px 13px; font-size:13px; color:var(--muted); }
.chip.on { border-color:var(--red); color:var(--text); background:#2a1215; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:14px; }
.card { background:var(--card); border:1px solid var(--border); border-radius:14px;
        padding:16px; display:flex; flex-direction:column; gap:8px;
        transition:transform .12s, border-color .12s; }
.card:hover { transform:translateY(-2px); border-color:var(--muted); }
.card .top { display:flex; justify-content:space-between; align-items:flex-start; }
.card .emoji { font-size:30px; }
.badge { font-size:11px; font-weight:700; letter-spacing:.4px; border-radius:6px;
         padding:3px 8px; white-space:nowrap; }
.b-all-time-low { background:#3d1114; color:#ff7b72; }
.b-great { background:#12261e; color:var(--green); }
.b-good  { background:#1b2436; color:#79c0ff; }
.b-typical { background:#2d2812; color:var(--amber); }
.b-new { background:#21262d; color:var(--muted); }
.card h3 { font-size:15px; line-height:1.3; } .card .brand { color:var(--muted); font-size:12px; }
.priceline { display:flex; align-items:baseline; gap:8px; }
.price { font-size:22px; font-weight:800; } .save { color:var(--green); font-size:13px; font-weight:600; }
.meta { color:var(--muted); font-size:12px; display:flex; justify-content:space-between; }
.spark { width:110px; height:30px; color:#79c0ff; }
.pimg { width:48px; height:48px; object-fit:contain; border-radius:8px; background:#fff; }
.histnote { color:var(--muted); font-size:12px; }
.verdict-banner { display:flex; gap:14px; align-items:center; background:var(--card);
        border:1px solid var(--border); border-radius:14px; padding:18px 20px; margin-bottom:20px; }
.verdict-banner .big { font-size:34px; }
.chartbox { background:var(--card); border:1px solid var(--border); border-radius:14px;
        padding:18px; margin-bottom:20px; }
table { width:100%; border-collapse:collapse; font-size:14px; }
th, td { text-align:left; padding:9px 10px; border-bottom:1px solid var(--border); }
th { color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }
.empty { text-align:center; color:var(--muted); padding:60px 20px; }
.empty code { background:var(--card); padding:2px 8px; border-radius:6px; }
@media (max-width:600px){ .grid{grid-template-columns:1fr 1fr;} .card{padding:12px;}
  .price{font-size:18px;} .card .emoji{font-size:24px;} }
</style></head>
<body>
<header>
  <a href="/"><h1><span class="logo">Safeway</span> Deal Tracker</h1></a>
  <span class="sub">{% block sub %}{% endblock %}</span>
</header>
<div class="wrap">{% block body %}{% endblock %}</div>
</body></html>"""

INDEX_HTML = """{% extends "base.html" %}
{% block sub %}{% if latest %}weekly ad of {{ latest|fmtdate }} · {{ deals|length }} deals{% if store %} · store {{ store }}{% endif %}{% endif %}{% endblock %}
{% block body %}
{% if not latest %}
  <div class="empty">
    <p style="font-size:40px">🛒</p>
    <p>No deal history yet.</p>
    <p style="margin-top:10px">Seed demo data with <code>python3 047_safeway_history_db.py --demo</code><br>
       or pull live deals with <code>python3 047_safeway_history_db.py --fetch --zip 94107</code></p>
  </div>
{% else %}
  <div class="stats">
    <div class="stat"><div class="num">{{ deals|length }}</div><div class="lbl">deals this week</div></div>
    <div class="stat"><div class="num">🔥 {{ n_lows }}</div><div class="lbl">all-time lows</div></div>
    <div class="stat"><div class="num">${{ '%.2f'|format(total_savings) }}</div><div class="lbl">total savings on offer</div></div>
    <div class="stat"><div class="num">{{ n_products }}</div><div class="lbl">products tracked</div></div>
    <div class="stat"><div class="num">{{ n_weeks }}</div><div class="lbl">weeks of history</div></div>
  </div>

  <form class="controls" method="get">
    <input type="search" name="q" placeholder="Search deals… (chicken, Tillamook, coffee)"
           value="{{ q }}" autocomplete="off">
    <select name="sort" onchange="this.form.submit()">
      <option value="score"   {{ 'selected' if sort=='score' }}>Best deals first</option>
      <option value="savings" {{ 'selected' if sort=='savings' }}>Biggest savings</option>
      <option value="price"   {{ 'selected' if sort=='price' }}>Lowest price</option>
      <option value="name"    {{ 'selected' if sort=='name' }}>A → Z</option>
    </select>
    {% if stores|length > 1 %}
    <select name="store" onchange="this.form.submit()">
      {% for s in stores %}<option value="{{ s }}" {{ 'selected' if s==store }}>store {{ s }}</option>{% endfor %}
    </select>
    {% elif store %}<input type="hidden" name="store" value="{{ store }}">{% endif %}
    {% if cat %}<input type="hidden" name="cat" value="{{ cat }}">{% endif %}
    <button style="display:none"></button>
  </form>

  <div class="chips">
    <a class="chip {{ 'on' if not cat }}" href="/?q={{ q|urlencode }}&sort={{ sort }}&store={{ store|urlencode }}">All</a>
    {% for c in categories %}
    <a class="chip {{ 'on' if cat==c }}" href="/?cat={{ c|urlencode }}&q={{ q|urlencode }}&sort={{ sort }}&store={{ store|urlencode }}">{{ c }}</a>
    {% endfor %}
  </div>

  <div class="grid">
    {% for d in deals %}
    <a class="card" href="/product/{{ d.key }}{% if store %}?store={{ store|urlencode }}{% endif %}">
      <div class="top">
        {% if d.image_url %}<img class="pimg" src="{{ d.image_url }}" alt="" loading="lazy"
             onerror="this.outerHTML='<span class=emoji>{{ d.emoji }}</span>'">
        {% else %}<span class="emoji">{{ d.emoji }}</span>{% endif %}
        <span class="badge b-{{ d.verdict }}">{{ d.verdict_emoji }} {{ d.verdict_label }}</span>
      </div>
      <div>
        <h3>{{ d.name }}</h3>
        <div class="brand">{{ d.brand or d.category }}</div>
      </div>
      <div class="priceline">
        <span class="price">{{ d.price_text or '—' }}</span>
        <span class="save">{{ d.savings_text }}</span>
      </div>
      {% if d.spark %}{{ d.spark|safe }}{% endif %}
      {% if d.all_time_low is not none and d.times_seen > 1 %}
      <div class="histnote">low ${{ '%.2f'|format(d.all_time_low) }} · avg ${{ '%.2f'|format(d.avg_price) }} · seen {{ d.times_seen }}×</div>
      {% endif %}
      <div class="meta"><span>{{ d.offer_type }}</span><span>{% if d.end_date %}ends {{ d.end_date|fmtdate }}{% endif %}</span></div>
    </a>
    {% endfor %}
  </div>
  {% if not deals %}<div class="empty">No deals match that filter.</div>{% endif %}
{% endif %}
{% endblock %}"""

PRODUCT_HTML = """{% extends "base.html" %}
{% block title %}{{ p.name }} — Safeway Deal Tracker{% endblock %}
{% block sub %}{{ p.category }}{% endblock %}
{% block body %}
  <p style="margin-bottom:14px"><a href="/" style="color:var(--muted)">← all deals</a></p>
  <div class="verdict-banner">
    {% if p.image_url %}<img class="pimg" src="{{ p.image_url }}" alt="" style="width:56px;height:56px"
         onerror="this.outerHTML='<span class=big>{{ emoji }}</span>'">
    {% else %}<span class="big">{{ emoji }}</span>{% endif %}
    <div>
      <h2 style="font-size:20px">{{ p.name }}</h2>
      <div class="brand" style="color:var(--muted)">{{ p.brand }}{% if p.brand and p.category %} · {% endif %}{{ p.category }}</div>
    </div>
    <div style="margin-left:auto;text-align:right">
      <span class="badge b-{{ verdict }}" style="font-size:13px">{{ v_emoji }} {{ v_label }}</span>
      <div class="histnote" style="margin-top:6px">{{ v_desc }}</div>
    </div>
  </div>

  <div class="stats">
    <div class="stat"><div class="num">{{ current_price or '—' }}</div><div class="lbl">{{ 'this week' if on_deal_now else 'last deal price' }}</div></div>
    <div class="stat"><div class="num">{% if low is not none %}${{ '%.2f'|format(low) }}{% else %}—{% endif %}</div><div class="lbl">all-time low</div></div>
    <div class="stat"><div class="num">{% if avg is not none %}${{ '%.2f'|format(avg) }}{% else %}—{% endif %}</div><div class="lbl">average deal price</div></div>
    <div class="stat"><div class="num">{{ rows|length }}</div><div class="lbl">times on deal</div></div>
    <div class="stat"><div class="num">{{ freq }}%</div><div class="lbl">of weeks on deal</div></div>
  </div>

  <div class="chartbox">
    <h3 style="margin-bottom:10px">Price history — green dot = all-time low</h3>
    {{ chart_svg|safe }}
  </div>

  <div class="chartbox">
    <h3 style="margin-bottom:10px">Deal timeline</h3>
    <div style="overflow-x:auto"><table>
      <tr><th>Week</th><th>Price</th><th>Savings</th><th>Offer type</th><th>Ran</th></tr>
      {% for r in rows|reverse %}
      <tr>
        <td>{{ r['captured_at']|fmtdate }}</td>
        <td><b>{{ r['price_text'] or '—' }}</b></td>
        <td style="color:var(--green)">{{ r['savings_text'] }}</td>
        <td>{{ r['offer_type'] }}</td>
        <td style="color:var(--muted)">{{ r['start_date']|fmtdate }} – {{ r['end_date']|fmtdate }}</td>
      </tr>
      {% endfor %}
    </table></div>
  </div>
{% endblock %}"""

app.jinja_loader = DictLoader({
    "base.html": BASE_HTML, "index.html": INDEX_HTML, "product.html": PRODUCT_HTML,
})


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    conn = db()
    try:
        store = request.args.get("store") or default_store(conn)
        stores = [r["store_id"] for r in conn.execute(
            "SELECT DISTINCT store_id FROM runs ORDER BY store_id") if r["store_id"]]
        deals, latest = build_current_deals(conn, store)
        q = (request.args.get("q") or "").strip()
        cat = (request.args.get("cat") or "").strip()
        sort = request.args.get("sort") or "score"
        categories = sorted({d["category"] for d in deals if d["category"]})
        if q:
            ql = q.lower()
            deals = [d for d in deals if ql in d["name"].lower() or ql in d["brand"].lower()]
        if cat:
            deals = [d for d in deals if d["category"] == cat]
        order = {"all-time-low": 0, "great": 1, "good": 2, "new": 3, "typical": 4}
        if sort == "savings":
            deals.sort(key=lambda d: -(d["savings_value"] or 0))
        elif sort == "price":
            deals.sort(key=lambda d: d["price_value"] if d["price_value"] is not None else 1e9)
        elif sort == "name":
            deals.sort(key=lambda d: d["name"].lower())
        else:
            deals.sort(key=lambda d: (order.get(d["verdict"], 9), -(d["savings_value"] or 0)))
        frag, params = store_filter(store)
        n_weeks = conn.execute(
            f"SELECT COUNT(DISTINCT captured_at) c FROM deal_snapshots WHERE 1=1{frag}",
            params).fetchone()["c"]
        n_products = conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]
        return render_template(
            "index.html", deals=deals, latest=latest, q=q, cat=cat, sort=sort,
            categories=categories, store=store, stores=stores,
            n_lows=sum(1 for d in deals if d["verdict"] == "all-time-low"),
            total_savings=sum(d["savings_value"] or 0 for d in deals),
            n_products=n_products, n_weeks=n_weeks,
        )
    finally:
        conn.close()


@app.route("/product/<key>")
def product(key):
    conn = db()
    try:
        p = conn.execute("SELECT * FROM products WHERE product_key = ?", (key,)).fetchone()
        if not p:
            abort(404)
        store = request.args.get("store") or default_store(conn)
        rows = product_history(conn, key, store)
        latest = latest_run_date(conn, store)
        prices = [r["price_value"] for r in rows if r["price_value"] is not None]
        cur = rows[-1] if rows else None
        on_deal_now = bool(cur and latest and cur["captured_at"] == latest)
        past = [r["price_value"] for r in rows[:-1] if r["price_value"] is not None]
        v = verdict_for(cur["price_value"] if cur else None, past,
                        times_seen=len(rows)) if on_deal_now else "new"
        if not on_deal_now:
            v_emoji, v_label, v_desc = "💤", "NOT IN THIS WEEK'S AD", "Check the timeline for when it usually returns"
        else:
            v_emoji, v_label, v_desc = VERDICTS[v]
        # Chart across every week in the DB, gaps where this product wasn't on deal.
        frag, params = store_filter(store)
        all_weeks = [r["captured_at"] for r in conn.execute(
            f"SELECT DISTINCT captured_at FROM deal_snapshots WHERE 1=1{frag} "
            f"ORDER BY captured_at", params)]
        by_week = {r["captured_at"]: r["price_value"] for r in rows}
        chart_svg = timeline_chart_svg(
            [fmt_date(w) for w in all_weeks],
            [by_week.get(w) for w in all_weeks],
            min(prices) if prices else 0,
        )
        return render_template(
            "product.html", p=p, rows=rows, verdict=v if on_deal_now else "new",
            v_emoji=v_emoji, v_label=v_label, v_desc=v_desc,
            emoji=CATEGORY_EMOJI.get(p["category"], DEFAULT_EMOJI),
            current_price=(cur["price_text"] if cur else None),
            on_deal_now=on_deal_now, store=store,
            low=min(prices) if prices else None,
            avg=statistics.mean(prices) if prices else None,
            freq=round(100 * len(rows) / len(all_weeks)) if all_weeks else 0,
            chart_svg=chart_svg,
        )
    finally:
        conn.close()


@app.route("/api/deals")
def api_deals():
    conn = db()
    try:
        deals, latest = build_current_deals(conn, request.args.get("store") or default_store(conn))
        for d in deals:
            d.pop("spark", None)
        return jsonify({"week": latest, "count": len(deals), "deals": deals})
    finally:
        conn.close()


@app.route("/api/product/<key>")
def api_product(key):
    conn = db()
    try:
        p = conn.execute("SELECT * FROM products WHERE product_key = ?", (key,)).fetchone()
        if not p:
            abort(404)
        rows = [dict(r) for r in product_history(conn, key)]
        return jsonify({"product": dict(p), "history": rows})
    finally:
        conn.close()


@app.route("/api/stats")
def api_stats():
    conn = db()
    try:
        deals, latest = build_current_deals(conn, request.args.get("store") or default_store(conn))
        return jsonify({
            "week": latest,
            "deals_this_week": len(deals),
            "all_time_lows": sum(1 for d in deals if d["verdict"] == "all-time-low"),
            "products_tracked": conn.execute("SELECT COUNT(*) c FROM products").fetchone()["c"],
            "weeks_of_history": conn.execute(
                "SELECT COUNT(DISTINCT captured_at) c FROM deal_snapshots").fetchone()["c"],
        })
    finally:
        conn.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=5057)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args()
    app.config["DB_PATH"] = args.db
    if not Path(args.db).exists():
        print(f"note: {args.db} doesn't exist yet — run 047_safeway_history_db.py --demo first")
    print(f"Safeway Deal Tracker -> http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    return_code = main()
    raise SystemExit(return_code)
