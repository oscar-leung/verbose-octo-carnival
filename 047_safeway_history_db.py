"""Safeway deals history database — "stocks, but for groceries".

Every run of 046_safeway_deals_scraper.py is a snapshot of that week's deals.
This module ingests snapshots into SQLite so each product accumulates a
price/deal timeline over the weeks. 048_safeway_app.py serves the UI on top:
current deals, savings, and a per-product price-history chart.

Usage:
    # Seed 12 weeks of realistic demo data (no network needed) so the app
    # has something to show immediately:
    python3 047_safeway_history_db.py --demo

    # Ingest a raw JSON dump produced by the scraper:
    python3 047_safeway_history_db.py --from-json runs/safeway/safeway_2926_2026-05-13.raw.json --store-id 2926

    # Fetch live from the Safeway API and ingest in one step:
    python3 047_safeway_history_db.py --fetch --store-id 2926
    python3 047_safeway_history_db.py --fetch --zip 94107

Database: runs/safeway/safeway.db (gitignored). Schema:
    products        one row per product, keyed by normalized brand+name —
                    Safeway offer ids change week to week, so brand+name is
                    the stable identity that lets history accumulate
    deal_snapshots  one row per (product, run) — the timeline
    runs            one row per ingest, for bookkeeping
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
DB_PATH = ROOT / "runs" / "safeway" / "safeway.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    product_key TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    brand       TEXT DEFAULT '',
    category    TEXT DEFAULT '',
    image_url   TEXT DEFAULT '',
    first_seen  TEXT NOT NULL,
    last_seen   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deal_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    product_key   TEXT NOT NULL REFERENCES products(product_key),
    captured_at   TEXT NOT NULL,
    store_id      TEXT DEFAULT '',
    offer_id      TEXT DEFAULT '',
    offer_type    TEXT DEFAULT '',
    title         TEXT DEFAULT '',
    description   TEXT DEFAULT '',
    price_text    TEXT DEFAULT '',
    savings_text  TEXT DEFAULT '',
    price_value   REAL,
    savings_value REAL,
    start_date    TEXT DEFAULT '',
    end_date      TEXT DEFAULT '',
    UNIQUE(product_key, captured_at, store_id)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_product ON deal_snapshots(product_key, captured_at);
CREATE INDEX IF NOT EXISTS idx_snapshots_captured ON deal_snapshots(captured_at);
CREATE TABLE IF NOT EXISTS runs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TEXT NOT NULL,
    store_id    TEXT DEFAULT '',
    offer_count INTEGER DEFAULT 0,
    source      TEXT DEFAULT 'live'
);
"""


def get_db(path: Path = DB_PATH) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def product_key(brand: str, name: str) -> str:
    """Stable product identity across weeks: normalized brand+name slug."""
    raw = f"{brand} {name}".lower().strip()
    # Split digit/letter boundaries so '16oz' and '16 oz' slug identically.
    raw = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", raw)
    return re.sub(r"[^a-z0-9]+", "-", raw).strip("-") or "unknown"


MONEY_RE = re.compile(r"\$\s*(\d+(?:\.\d{1,2})?)")
MULTIBUY_RE = re.compile(r"(?<![\d.$])(\d+)\s*(?:for|/)\s*\$\s*(\d+(?:\.\d{1,2})?)", re.I)


def parse_money(text: str) -> float | None:
    """Best-effort dollars from deal text: '$2.99', '2 for $5', 'Save $1.50'.

    Multi-buy deals ('Buy 2 for $6', '2/$5') return the effective unit price.
    Text with no dollar amount — 'BOGO', 'Buy 1 Get 1 Free', '50% off',
    'Member Price' — returns None; a bare number only counts as dollars when
    it's the entire string. A wrong guess here is worse than no guess: a fake
    price_value becomes a permanent bogus all-time low in the history.
    """
    if not text:
        return None
    t = str(text).strip()
    if re.search(r"%|\bfree\b|\bbogo\b", t, re.I):
        return None
    m = MULTIBUY_RE.search(t)
    if m:
        qty, total = int(m.group(1)), float(m.group(2))
        return round(total / qty, 2) if qty else None
    m = MONEY_RE.search(t)
    if m:
        return float(m.group(1))
    m = re.fullmatch(r"\d+(?:\.\d{1,2})?", t)
    return float(m.group(0)) if m else None


def norm_date(v) -> str:
    """ISO date from whatever the API sends: ISO strings, datetimes, epoch ms."""
    if v in (None, ""):
        return ""
    s = str(v).strip()
    if s.isdigit() and len(s) >= 12:
        return datetime.fromtimestamp(int(s) / 1000).date().isoformat()
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return s


def ad_week_date(offers: list[dict], filename: str | None = None) -> str:
    """Canonical snapshot date for a batch of offers: the date embedded in the
    dump filename, else the ad's start_date, else the most recent Wednesday
    (Safeway's ad flips on Wednesdays). Anchoring to the ad week — not the
    fetch day — means refetching the same weekly ad on different days
    collapses onto one captured_at instead of fabricating extra weeks."""
    if filename:
        m = re.search(r"(\d{4}-\d{2}-\d{2})", Path(filename).name)
        if m:
            return m.group(1)
    starts = sorted(d for d in (norm_date(o.get("start_date")) for o in offers)
                    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))
    if starts:
        return starts[0]
    d = datetime.now().date()
    return (d - timedelta(days=(d.weekday() - 2) % 7)).isoformat()


def record_run(conn: sqlite3.Connection, captured_at: str, store_id: str,
               count: int, source: str) -> None:
    conn.execute(
        "INSERT INTO runs (captured_at, store_id, offer_count, source) VALUES (?,?,?,?)",
        (captured_at, store_id, count, source),
    )


def ingest_offers(conn: sqlite3.Connection, offers: list[dict], store_id: str,
                  captured_at: str, source: str = "live") -> int:
    """Ingest one snapshot of normalized offers (046's Deal fields as dicts).

    One row per (product, week, store): when the same product appears twice in
    a week (a WeeklySpecial plus a coupon, say), the priced — and if both are
    priced, cheaper — offer wins, so downstream stats never double-count.
    """
    n = 0
    for o in offers:
        name = (o.get("title") or o.get("name") or "").strip()
        if not name:
            continue
        brand = (o.get("brand") or "").strip()
        key = product_key(brand, name)
        if not brand:
            # Brand fields flicker week to week on the live API; reattach
            # brandless offers to the existing product with the same name so
            # one product's history doesn't split across two keys.
            row = conn.execute(
                "SELECT product_key FROM products WHERE lower(name) = lower(?) "
                "ORDER BY last_seen DESC LIMIT 1", (name,)).fetchone()
            if row:
                key = row["product_key"]
        conn.execute(
            """INSERT INTO products (product_key, name, brand, category, image_url, first_seen, last_seen)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(product_key) DO UPDATE SET
                 first_seen = MIN(products.first_seen, excluded.first_seen),
                 last_seen  = MAX(products.last_seen,  excluded.last_seen),
                 category  = CASE WHEN products.category  = '' THEN excluded.category  ELSE products.category  END,
                 image_url = CASE WHEN products.image_url = '' THEN excluded.image_url ELSE products.image_url END""",
            (key, name, brand, o.get("category", ""), o.get("image_url", ""),
             captured_at, captured_at),
        )
        price_text = o.get("price") or o.get("price_text") or ""
        savings_text = o.get("savings") or o.get("savings_text") or ""
        cur = conn.execute(
            """INSERT INTO deal_snapshots
               (product_key, captured_at, store_id, offer_id, offer_type, title,
                description, price_text, savings_text, price_value, savings_value,
                start_date, end_date)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(product_key, captured_at, store_id) DO UPDATE SET
                 offer_id=excluded.offer_id, offer_type=excluded.offer_type,
                 title=excluded.title, description=excluded.description,
                 price_text=excluded.price_text, savings_text=excluded.savings_text,
                 price_value=excluded.price_value, savings_value=excluded.savings_value,
                 start_date=excluded.start_date, end_date=excluded.end_date
               WHERE excluded.price_value IS NOT NULL
                 AND (deal_snapshots.price_value IS NULL
                      OR excluded.price_value < deal_snapshots.price_value)""",
            (key, captured_at, store_id, str(o.get("offer_id", "")),
             o.get("offer_type", ""), name, o.get("description", ""),
             price_text, savings_text,
             o.get("price_value", parse_money(price_text)),
             o.get("savings_value", parse_money(savings_text)),
             norm_date(o.get("start_date", "")), norm_date(o.get("end_date", ""))),
        )
        n += cur.rowcount
    record_run(conn, captured_at, store_id, n, source)
    conn.commit()
    return n


# ── Demo data ────────────────────────────────────────────────────────────────
# Realistic products so the app is explorable before any live scrape. Prices
# drift week to week and items rotate on/off deal, which is exactly the shape
# real weekly-ad history has.

DEMO_PRODUCTS = [
    # (name, brand, category, base_price)
    ("Boneless Skinless Chicken Breast", "Foster Farms", "Meat & Seafood", 5.99),
    ("85% Lean Ground Beef, per lb", "Signature Farms", "Meat & Seafood", 6.49),
    ("Atlantic Salmon Fillet, per lb", "Waterfront Bistro", "Meat & Seafood", 12.99),
    ("Large Raw Shrimp 16-20 ct", "Waterfront Bistro", "Meat & Seafood", 10.99),
    ("Bacon, Hickory Smoked 16 oz", "Oscar Mayer", "Meat & Seafood", 8.49),
    ("Whole Rotisserie Chicken", "Signature Cafe", "Deli", 8.99),
    ("Half & Half, 32 oz", "Lucerne", "Dairy & Eggs", 3.49),
    ("Large Eggs, Grade AA, dozen", "Lucerne", "Dairy & Eggs", 4.99),
    ("2% Reduced Fat Milk, gallon", "Lucerne", "Dairy & Eggs", 4.29),
    ("Greek Yogurt, Vanilla 32 oz", "Chobani", "Dairy & Eggs", 6.49),
    ("Salted Butter, 16 oz", "Tillamook", "Dairy & Eggs", 5.99),
    ("Medium Cheddar Cheese, 32 oz", "Tillamook", "Dairy & Eggs", 9.99),
    ("Hass Avocados, each", "", "Produce", 2.49),
    ("Organic Bananas, per lb", "O Organics", "Produce", 0.99),
    ("Strawberries, 1 lb", "Driscoll's", "Produce", 4.99),
    ("Blueberries, 18 oz", "Driscoll's", "Produce", 6.99),
    ("Honeycrisp Apples, per lb", "", "Produce", 2.99),
    ("Baby Spinach, 16 oz", "Earthbound Farm", "Produce", 4.49),
    ("Sweet Corn, each", "", "Produce", 0.89),
    ("Roma Tomatoes, per lb", "", "Produce", 1.99),
    ("Sourdough Bread Loaf", "Signature Select", "Bakery", 3.99),
    ("Everything Bagels, 6 ct", "Signature Select", "Bakery", 3.49),
    ("Croissants, 4 ct", "Signature Select", "Bakery", 4.99),
    ("Orange Juice, 52 oz", "Simply", "Beverages", 4.99),
    ("Cold Brew Coffee, 48 oz", "Stok", "Beverages", 5.99),
    ("Sparkling Water 12-pack", "LaCroix", "Beverages", 5.49),
    ("Soda 12-pack cans", "Coca-Cola", "Beverages", 9.49),
    ("Ground Coffee, 28 oz", "Folgers", "Beverages", 12.99),
    ("Tortilla Chips, Party Size", "Tostitos", "Snacks", 5.49),
    ("Potato Chips, Family Size", "Lay's", "Snacks", 4.99),
    ("Ice Cream, 48 oz", "Tillamook", "Frozen", 6.99),
    ("Frozen Pizza, Rising Crust", "DiGiorno", "Frozen", 7.99),
    ("Frozen Mixed Vegetables, 32 oz", "Signature Select", "Frozen", 3.49),
    ("Pasta Sauce, Marinara 24 oz", "Rao's", "Pantry", 8.99),
    ("Spaghetti, 16 oz", "Barilla", "Pantry", 2.29),
    ("Extra Virgin Olive Oil, 25 oz", "Signature Select", "Pantry", 9.99),
    ("Peanut Butter, Creamy 28 oz", "Jif", "Pantry", 5.49),
    ("Cereal, Honey Nut 18.8 oz", "Cheerios", "Pantry", 5.99),
    ("White Rice, 5 lb", "Signature Select", "Pantry", 6.49),
    ("Paper Towels, 6 rolls", "Bounty", "Household", 12.99),
    ("Toilet Paper, 12 mega rolls", "Charmin", "Household", 15.99),
    ("Laundry Detergent, 92 oz", "Tide", "Household", 13.99),
]

DEMO_OFFER_TYPES = ["WeeklySpecial", "WeeklySpecial", "WeeklySpecial",
                    "PersonalizedDeal", "ManufactureCoupon"]


def seed_demo(conn: sqlite3.Connection, weeks: int = 12,
              store_id: str = "demo-safeway-davis") -> int:
    """Generate `weeks` of weekly-ad snapshots ending this week."""
    rng = random.Random(42)
    # Anchor snapshots to Wednesdays — Safeway's weekly ad flips on Wednesday.
    today = datetime.now().date()
    last_wed = today - timedelta(days=(today.weekday() - 2) % 7)
    total = 0
    for w in range(weeks - 1, -1, -1):
        wed = last_wed - timedelta(weeks=w)
        captured = wed.isoformat()
        offers = []
        for i, (name, brand, cat, base) in enumerate(DEMO_PRODUCTS):
            # Each product is on deal ~45% of weeks; discount depth varies so
            # every product ends up with a genuine "all-time low" somewhere.
            if rng.random() > 0.45:
                continue
            depth = rng.choice([0.10, 0.15, 0.20, 0.25, 0.30, 0.40])
            price = round(base * (1 - depth), 2)
            savings = round(base - price, 2)
            offers.append({
                "offer_id": f"demo-{wed.isoformat()}-{i}",
                "title": name,
                "brand": brand,
                "category": cat,
                "description": f"{brand + ' ' if brand else ''}{name}. Member price with digital coupon.",
                "price": f"${price:.2f}",
                "savings": f"Save ${savings:.2f}",
                "offer_type": rng.choice(DEMO_OFFER_TYPES),
                "start_date": wed.isoformat(),
                "end_date": (wed + timedelta(days=6)).isoformat(),
                "image_url": "",
            })
        total += ingest_offers(conn, offers, store_id, captured, source="demo")
    return total


# ── Live fetch (reuses 046 without duplicating its API code) ────────────────

def purge_demo(conn: sqlite3.Connection) -> None:
    """Real data replaces demo data — otherwise fabricated demo prices merge
    into live history and permanently skew every all-time-low verdict."""
    n = conn.execute("DELETE FROM deal_snapshots WHERE store_id LIKE 'demo-%'").rowcount
    conn.execute("DELETE FROM products WHERE product_key NOT IN "
                 "(SELECT DISTINCT product_key FROM deal_snapshots)")
    conn.execute("DELETE FROM runs WHERE source = 'demo'")
    conn.commit()
    if n:
        print(f"  purged {n} demo snapshots (replaced by real data)")


def load_scraper_module():
    spec = importlib.util.spec_from_file_location(
        "safeway_scraper", ROOT / "046_safeway_deals_scraper.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # required for @dataclass under Py3.11
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB_PATH), help="SQLite path")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true", help="seed demo history")
    mode.add_argument("--from-json", nargs="+", help="raw .json dump(s) from 046")
    mode.add_argument("--fetch", action="store_true", help="fetch live via 046")
    ap.add_argument("--store-id", help="Safeway store id")
    ap.add_argument("--zip", help="zip code (with --fetch)")
    ap.add_argument("--weeks", type=int, default=12, help="demo weeks to seed")
    args = ap.parse_args()

    conn = get_db(Path(args.db))

    if args.demo:
        n = seed_demo(conn, weeks=args.weeks)
        print(f"Seeded {n} demo deal snapshots across {args.weeks} weeks -> {args.db}")
        return 0

    if args.from_json:
        purge_demo(conn)
        scraper = load_scraper_module()
        from dataclasses import asdict
        for path in args.from_json:
            raw = json.loads(Path(path).read_text())
            offers = [asdict(scraper.parse_offer(o)) for o in raw]
            captured = ad_week_date(offers, filename=path)
            n = ingest_offers(conn, offers, args.store_id or "", captured)
            print(f"Ingested {n} offers from {path} as week {captured}")
        return 0

    # --fetch
    if not args.store_id and not args.zip:
        ap.error("--fetch needs --store-id or --zip")
    purge_demo(conn)
    scraper = load_scraper_module()
    from dataclasses import asdict
    store_id = args.store_id or scraper.resolve_store_id(args.zip)
    raw = scraper.fetch_gallery(store_id)
    offers = [asdict(scraper.parse_offer(o)) for o in raw]
    captured = ad_week_date(offers)
    n = ingest_offers(conn, offers, store_id, captured)
    print(f"Ingested {n} live offers for store {store_id} as week {captured} -> {args.db}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
