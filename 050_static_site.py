"""Static-site exporter for the Grocery Deal Tracker.

Renders the whole tracker — every store, every deal card, every product
price-history page — into ONE self-contained docs/index.html: no server, no
CDN, no JS framework. Search, sort, category filters, the store switcher and
product pages all work client-side, so the file can be:

  - opened directly from disk (file://)
  - served by GitHub Pages (Settings -> Pages -> deploy from gh-pages branch)
  - shared anywhere as a single file

Usage:
    python3 050_static_site.py                 # writes docs/index.html
    python3 050_static_site.py --out site.html

Regenerate after each weekly fetch and push to refresh the website.
"""

from __future__ import annotations

import argparse
import html
import importlib.util
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent


def load(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def build(out_path: Path) -> None:
    w = load("048_safeway_app.py", "safeway_app")
    conn = w.db()

    stores = [r["store_id"] for r in conn.execute(
        "SELECT DISTINCT store_id FROM runs ORDER BY store_id") if r["store_id"]]
    if not stores:
        raise SystemExit("history DB is empty — run 047 --demo (and 049 demo) first")

    store_sections, detail_sections, store_options = [], [], []
    for si, store in enumerate(stores):
        deals, latest = w.build_current_deals(conn, store)
        order = {"all-time-low": 0, "great": 1, "good": 2, "new": 3, "typical": 4}
        deals.sort(key=lambda d: (order.get(d["verdict"], 9), -(d["savings_value"] or 0)))
        label = w.store_label(store)
        store_options.append(
            f'<option value="{esc(store)}"{" selected" if si == 0 else ""}>{esc(label)}</option>')
        cats = sorted({d["category"] for d in deals if d["category"]})
        n_lows = sum(1 for d in deals if d["verdict"] == "all-time-low")
        total_savings = sum(d["savings_value"] or 0 for d in deals)
        n_weeks = conn.execute(
            "SELECT COUNT(DISTINCT captured_at) c FROM deal_snapshots WHERE store_id=?",
            (store,)).fetchone()["c"]

        cards = []
        for d in deals:
            hist = (f'low ${d["all_time_low"]:.2f} · avg ${d["avg_price"]:.2f} · seen {d["times_seen"]}×'
                    if d["all_time_low"] is not None and d["times_seen"] > 1 else "")
            cards.append(f"""
<a class="card" href="#p/{esc(store)}/{esc(d['key'])}"
   data-search="{esc((d['name'] + ' ' + d['brand']).lower())}" data-cat="{esc(d['category'])}"
   data-savings="{d['savings_value'] or 0}" data-price="{d['price_value'] if d['price_value'] is not None else 1e9}"
   data-name="{esc(d['name'].lower())}" data-score="{order.get(d['verdict'], 9)}">
  <div class="top"><span class="emoji">{d['emoji']}</span>
    <span class="badge b-{d['verdict']}">{d['verdict_emoji']} {esc(d['verdict_label'])}</span></div>
  <div><h3>{esc(d['name'])}</h3><div class="brand">{esc(d['brand'] or d['category'])}</div></div>
  <div class="priceline"><span class="price">{esc(d['price_text'] or '—')}</span>
    <span class="save">{esc(d['savings_text'])}</span></div>
  {d['spark']}
  <div class="histnote">{hist}</div>
  <div class="meta"><span>{esc(d['offer_type'])}</span><span>{('ends ' + w.fmt_date(d['end_date'])) if d['end_date'] else ''}</span></div>
</a>""")

        chips = ['<button class="chip on" data-cat="">All</button>'] + [
            f'<button class="chip" data-cat="{esc(c)}">{esc(c)}</button>' for c in cats]
        store_sections.append(f"""
<section class="store" data-store="{esc(store)}" {'hidden' if si else ''}>
  <div class="stats">
    <div class="stat"><div class="num">{len(deals)}</div><div class="lbl">deals this week</div></div>
    <div class="stat"><div class="num">🔥 {n_lows}</div><div class="lbl">all-time lows</div></div>
    <div class="stat"><div class="num">${total_savings:.2f}</div><div class="lbl">total savings on offer</div></div>
    <div class="stat"><div class="num">{n_weeks}</div><div class="lbl">weeks of history</div></div>
    <div class="stat"><div class="num">{w.fmt_date(latest) if latest else '—'}</div><div class="lbl">weekly ad</div></div>
  </div>
  <div class="chips">{''.join(chips)}</div>
  <div class="grid">{''.join(cards)}</div>
  <div class="empty" hidden>No deals match that filter.</div>
</section>""")

        # Per-product detail views for this store.
        all_weeks = [r["captured_at"] for r in conn.execute(
            "SELECT DISTINCT captured_at FROM deal_snapshots WHERE store_id=? ORDER BY captured_at",
            (store,))]
        for d in deals:
            rows = w.product_history(conn, d["key"], store)
            prices = [r["price_value"] for r in rows if r["price_value"] is not None]
            by_week = {r["captured_at"]: r["price_value"] for r in rows}
            chart = w.timeline_chart_svg(
                [w.fmt_date(x) for x in all_weeks],
                [by_week.get(x) for x in all_weeks],
                min(prices) if prices else 0)
            trs = "".join(
                f"<tr><td>{w.fmt_date(r['captured_at'])}</td><td><b>{esc(r['price_text'] or '—')}</b></td>"
                f"<td class='save'>{esc(r['savings_text'])}</td><td>{esc(r['offer_type'])}</td>"
                f"<td class='mut'>{w.fmt_date(r['start_date'])} – {w.fmt_date(r['end_date'])}</td></tr>"
                for r in reversed(rows))
            vd = w.VERDICTS[d["verdict"]]
            freq = round(100 * len(rows) / len(all_weeks)) if all_weeks else 0
            detail_sections.append(f"""
<section class="detail" data-detail="{esc(store)}/{esc(d['key'])}" hidden>
  <p class="backrow"><a href="#s/{esc(store)}" class="back">← all deals</a></p>
  <div class="banner"><span class="big">{d['emoji']}</span>
    <div><h2>{esc(d['name'])}</h2><div class="brand">{esc(d['brand'])}{' · ' if d['brand'] and d['category'] else ''}{esc(d['category'])} · {esc(label)}</div></div>
    <div class="vwrap"><span class="badge b-{d['verdict']}">{d['verdict_emoji']} {esc(d['verdict_label'])}</span>
      <div class="histnote">{esc(vd[2])}</div></div>
  </div>
  <div class="stats">
    <div class="stat"><div class="num">{esc(d['price_text'] or '—')}</div><div class="lbl">this week</div></div>
    <div class="stat"><div class="num">{'$%.2f' % min(prices) if prices else '—'}</div><div class="lbl">all-time low</div></div>
    <div class="stat"><div class="num">{'$%.2f' % (sum(prices) / len(prices)) if prices else '—'}</div><div class="lbl">average deal price</div></div>
    <div class="stat"><div class="num">{len(rows)}</div><div class="lbl">times on deal</div></div>
    <div class="stat"><div class="num">{freq}%</div><div class="lbl">of weeks on deal</div></div>
  </div>
  <div class="chartbox"><h3>Price history — green dot = all-time low</h3>{chart}</div>
  <div class="chartbox"><h3>Deal timeline</h3><div class="tblwrap"><table>
    <tr><th>Week</th><th>Price</th><th>Savings</th><th>Offer type</th><th>Ran</th></tr>{trs}
  </table></div></div>
</section>""")

    generated = datetime.now().strftime("%b %d, %Y")
    page = f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#0d1117">
<title>Grocery Deal Tracker</title>
<style>
:root {{ --bg:#0d1117; --card:#161b22; --border:#21262d; --text:#e6edf3;
        --muted:#8b949e; --red:#ff4d4d; --green:#3fb950; --amber:#d29922; }}
* {{ box-sizing:border-box; margin:0; }}
body {{ background:var(--bg); color:var(--text); font:15px/1.5 -apple-system,
       BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; padding-bottom:48px; }}
a {{ color:inherit; text-decoration:none; }}
header {{ position:sticky; top:0; z-index:10; background:rgba(13,17,23,.92);
         backdrop-filter:blur(8px); border-bottom:1px solid var(--border);
         padding:14px 20px; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }}
header h1 {{ font-size:19px; }} header h1 .logo {{ color:var(--red); }}
header .sub {{ color:var(--muted); font-size:13px; }}
.wrap {{ max-width:1180px; margin:0 auto; padding:20px; }}
.controls {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; }}
input[type=search], select {{ background:var(--card); color:var(--text);
        border:1px solid var(--border); border-radius:8px; padding:8px 12px; font-size:14px; }}
input[type=search] {{ flex:1; min-width:180px; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
         gap:12px; margin-bottom:18px; }}
.stat {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px 16px; }}
.stat .num {{ font-size:22px; font-weight:700; font-variant-numeric:tabular-nums; }}
.stat .lbl {{ color:var(--muted); font-size:12px; }}
.chips {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:18px; }}
.chip {{ border:1px solid var(--border); background:var(--card); border-radius:999px;
        padding:5px 13px; font-size:13px; color:var(--muted); cursor:pointer; font-family:inherit; }}
.chip.on {{ border-color:var(--red); color:var(--text); background:#2a1215; }}
.chip:focus-visible, .card:focus-visible {{ outline:2px solid var(--red); outline-offset:2px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(250px,1fr)); gap:14px; }}
.card {{ background:var(--card); border:1px solid var(--border); border-radius:14px;
        padding:16px; display:flex; flex-direction:column; gap:8px;
        transition:transform .12s, border-color .12s; }}
.card:hover {{ transform:translateY(-2px); border-color:var(--muted); }}
@media (prefers-reduced-motion: reduce) {{ .card {{ transition:none; }} }}
.card .top {{ display:flex; justify-content:space-between; align-items:flex-start; }}
.card .emoji {{ font-size:30px; }}
.badge {{ font-size:11px; font-weight:700; letter-spacing:.4px; border-radius:6px;
         padding:3px 8px; white-space:nowrap; }}
.b-all-time-low {{ background:#3d1114; color:#ff7b72; }}
.b-great {{ background:#12261e; color:var(--green); }}
.b-good  {{ background:#1b2436; color:#79c0ff; }}
.b-typical {{ background:#2d2812; color:var(--amber); }}
.b-new {{ background:#21262d; color:var(--muted); }}
.card h3 {{ font-size:15px; line-height:1.3; }} .brand {{ color:var(--muted); font-size:12px; }}
.priceline {{ display:flex; align-items:baseline; gap:8px; }}
.price {{ font-size:22px; font-weight:800; font-variant-numeric:tabular-nums; }}
.save {{ color:var(--green); font-size:13px; font-weight:600; }}
.meta {{ color:var(--muted); font-size:12px; display:flex; justify-content:space-between; }}
.mut {{ color:var(--muted); }}
.spark {{ width:110px; height:30px; color:#79c0ff; }}
.histnote {{ color:var(--muted); font-size:12px; }}
.banner {{ display:flex; gap:14px; align-items:center; background:var(--card);
        border:1px solid var(--border); border-radius:14px; padding:18px 20px; margin-bottom:18px;
        flex-wrap:wrap; }}
.banner .big {{ font-size:34px; }} .banner h2 {{ font-size:20px; }}
.vwrap {{ margin-left:auto; text-align:right; }}
.chartbox {{ background:var(--card); border:1px solid var(--border); border-radius:14px;
        padding:18px; margin-bottom:18px; }}
.chartbox h3 {{ margin-bottom:10px; font-size:15px; }}
.tblwrap {{ overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; font-size:14px; }}
th, td {{ text-align:left; padding:9px 10px; border-bottom:1px solid var(--border); }}
th {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }}
.empty {{ text-align:center; color:var(--muted); padding:60px 20px; }}
.backrow {{ margin-bottom:14px; }} .back {{ color:var(--muted); }}
footer {{ text-align:center; color:var(--muted); font-size:12px; margin-top:28px; }}
@media (max-width:600px) {{ .grid {{ grid-template-columns:1fr 1fr; }} .card {{ padding:12px; }}
  .price {{ font-size:18px; }} .card .emoji {{ font-size:24px; }} }}
</style></head>
<body>
<header>
  <a href="#"><h1><span class="logo">Grocery</span> Deal Tracker</h1></a>
  <span class="sub">deal history &amp; buy/wait verdicts · updated {generated}</span>
</header>
<div class="wrap">
  <div class="controls" id="controls">
    <input type="search" id="q" placeholder="Search deals… (rice, Tillamook, coffee)" autocomplete="off">
    <select id="sort">
      <option value="score">Best deals first</option>
      <option value="savings">Biggest savings</option>
      <option value="price">Lowest price</option>
      <option value="name">A → Z</option>
    </select>
    <select id="storeSel">{''.join(store_options)}</select>
  </div>
  {''.join(store_sections)}
  {''.join(detail_sections)}
  <footer>Built from a local price-history database · deal verdicts compare each product
  against its own past deals · demo data where marked (demo)</footer>
</div>
<script>
(function () {{
  var q = document.getElementById('q'), sortSel = document.getElementById('sort'),
      storeSel = document.getElementById('storeSel'), controls = document.getElementById('controls');
  var stores = [].slice.call(document.querySelectorAll('.store'));
  var details = [].slice.call(document.querySelectorAll('.detail'));

  function currentStore() {{ return storeSel.value; }}

  function applyFilters() {{
    var sec = document.querySelector('.store[data-store="' + CSS.escape(currentStore()) + '"]');
    if (!sec) return;
    var text = q.value.trim().toLowerCase();
    var cat = (sec.querySelector('.chip.on') || {{}}).dataset ? sec.querySelector('.chip.on').dataset.cat : '';
    var cards = [].slice.call(sec.querySelectorAll('.card')), shown = 0;
    cards.forEach(function (c) {{
      var ok = (!text || c.dataset.search.indexOf(text) !== -1) && (!cat || c.dataset.cat === cat);
      c.hidden = !ok; if (ok) shown++;
    }});
    sec.querySelector('.empty').hidden = shown > 0;
    var key = sortSel.value, grid = sec.querySelector('.grid');
    cards.sort(function (a, b) {{
      if (key === 'name') return a.dataset.name < b.dataset.name ? -1 : 1;
      if (key === 'price') return (+a.dataset.price) - (+b.dataset.price);
      if (key === 'savings') return (+b.dataset.savings) - (+a.dataset.savings);
      return (+a.dataset.score) - (+b.dataset.score) || (+b.dataset.savings) - (+a.dataset.savings);
    }}).forEach(function (c) {{ grid.appendChild(c); }});
  }}

  function route() {{
    var h = decodeURIComponent(location.hash.slice(1));
    var m = h.match(/^p\\/(.+)$/);
    details.forEach(function (d) {{ d.hidden = true; }});
    if (m) {{
      var d = document.querySelector('.detail[data-detail="' + CSS.escape(m[1]) + '"]');
      stores.forEach(function (s) {{ s.hidden = true; }});
      controls.style.display = 'none';
      if (d) {{ d.hidden = false; window.scrollTo(0, 0); }}
      return;
    }}
    var sm = h.match(/^s\\/(.+)$/);
    if (sm) storeSel.value = sm[1];
    controls.style.display = '';
    stores.forEach(function (s) {{ s.hidden = s.dataset.store !== currentStore(); }});
    applyFilters();
  }}

  document.addEventListener('click', function (e) {{
    var chip = e.target.closest('.chip');
    if (!chip) return;
    chip.parentElement.querySelectorAll('.chip').forEach(function (c) {{ c.classList.remove('on'); }});
    chip.classList.add('on');
    applyFilters();
  }});
  q.addEventListener('input', applyFilters);
  sortSel.addEventListener('change', applyFilters);
  storeSel.addEventListener('change', function () {{ location.hash = 's/' + storeSel.value; }});
  window.addEventListener('hashchange', route);
  route();
}})();
</script>
</body></html>"""

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page)
    kb = out_path.stat().st_size // 1024
    print(f"Wrote {out_path} ({kb} KB, {len(stores)} stores, {len(detail_sections)} product pages)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "docs" / "index.html"))
    args = ap.parse_args()
    build(Path(args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
