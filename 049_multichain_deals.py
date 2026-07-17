"""Multi-chain grocery deals — extends the Safeway tracker to every store.

Two adapter families cover most grocery chains:

  albertsons  Safeway's parent company runs the same xapi for all its
              banners — Safeway, Albertsons, Vons, Pavilions, Andronico's,
              Tom Thumb, Randalls, Jewel-Osco, Shaw's, ACME. Same endpoints,
              different domain.
  flipp       Flipp (backflipp.wishabi.com) hosts the digital weekly ads for
              hundreds of chains that don't run their own deals API —
              Grocery Outlet, FoodMaxx, Smart & Final, Raley's, WinCo,
              CHEF'STORE, Sprouts and more. One public JSON endpoint,
              searchable by zip code + merchant name.

Everything lands in the same history DB (047), so 048's app shows each
store's deals with verdicts and price timelines — pick the store from the
dropdown.

Usage:
    # What stores are near me? (Davis / Sacramento / Bay Area zips)
    python3 049_multichain_deals.py stores --zip 95616
    python3 049_multichain_deals.py stores --zip 95814 94107

    # Pull a chain's current weekly deals into the tracker:
    python3 049_multichain_deals.py fetch --chain safeway --store-id 2926
    python3 049_multichain_deals.py fetch --chain albertsons --zip 95616
    python3 049_multichain_deals.py fetch --chain flipp --merchant "Grocery Outlet" --zip 95616
    python3 049_multichain_deals.py fetch --chain flipp --merchant "CHEF'STORE" --zip 95814

    # Multi-store demo data (CHEF'STORE Sacramento + Grocery Outlet Davis):
    python3 049_multichain_deals.py demo

Note: like Safeway, these sites may 403 from cloud IPs (Akamai). Run from a
home network, or set <CHAIN>_COOKIE (falls back to SAFEWAY_COOKIE) with a
browser cookie from DevTools.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).parent

# ── Chain registry ───────────────────────────────────────────────────────────

ALBERTSONS_BANNERS = {
    "safeway": "www.safeway.com",
    "albertsons": "www.albertsons.com",
    "vons": "www.vons.com",
    "pavilions": "www.pavilions.com",
    "andronicos": "www.andronicos.com",
    "tomthumb": "www.tomthumb.com",
    "randalls": "www.randalls.com",
    "jewelosco": "www.jewelosco.com",
    "shaws": "www.shaws.com",
    "acmemarkets": "www.acmemarkets.com",
}

# Merchant names as Flipp knows them (searchable weekly-ad circulars).
FLIPP_MERCHANTS = [
    "Grocery Outlet", "FoodMaxx", "Smart & Final", "Raley's",
    "WinCo Foods", "CHEF'STORE", "Sprouts Farmers Market", "Lucky Supermarkets",
    "Safeway", "Save Mart", "99 Ranch Market", "Nugget Markets",
]

FLIPP_SEARCH_URL = "https://backflipp.wishabi.com/flipp/items/search"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def http_headers(chain: str = "") -> dict:
    h = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    cookie = os.environ.get(f"{chain.upper()}_COOKIE") or os.environ.get("SAFEWAY_COOKIE")
    if cookie:
        h["Cookie"] = cookie
    return h


def load_module(filename: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def history():
    return load_module("047_safeway_history_db.py", "safeway_history")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


# ── Albertsons-family adapter (Safeway, Vons, Albertsons, …) ────────────────

def albertsons_stores(banner: str, zip_code: str) -> list[dict]:
    domain = ALBERTSONS_BANNERS[banner]
    r = requests.get(
        f"https://{domain}/abs/pub/xapi/storeresolver/storesearch",
        params={"request-type": "google-search", "search-string": zip_code,
                "banner": banner},
        headers=http_headers(banner), timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    return data.get("stores") or data.get("response", {}).get("stores") or []


def albertsons_fetch(banner: str, store_id: str) -> list[dict]:
    """Fetch + normalize the weekly gallery for any Albertsons-family banner."""
    domain = ALBERTSONS_BANNERS[banner]
    r = requests.get(
        f"https://{domain}/abs/pub/xapi/offers/companiongalleryoffer",
        params={"storeId": store_id},
        headers={**http_headers(banner),
                 "Referer": f"https://{domain}/foru/coupons-deals.html"},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    raw = (data.get("companionGalleryOffer") or data.get("offers")
           or data.get("response", {}).get("companionGalleryOffer") or [])
    scraper = load_module("046_safeway_deals_scraper.py", "safeway_scraper")
    from dataclasses import asdict
    return [asdict(scraper.parse_offer(o)) for o in raw]


# ── Flipp adapter (Grocery Outlet, CHEF'STORE, FoodMaxx, …) ─────────────────

def flipp_search(zip_code: str, query: str, limit: int = 400) -> list[dict]:
    r = requests.get(
        FLIPP_SEARCH_URL,
        params={"locale": "en-us", "postal_code": zip_code, "q": query},
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    return (r.json().get("items") or [])[:limit]


def flipp_fetch(merchant: str, zip_code: str) -> list[dict]:
    """Normalize a merchant's current Flipp circular into 047-shaped offers."""
    items = [i for i in flipp_search(zip_code, merchant)
             if slug(merchant) in slug(str(i.get("merchant", "")))]
    offers = []
    for i in items:
        price = i.get("current_price")
        offers.append({
            "offer_id": str(i.get("flyer_item_id") or i.get("id") or ""),
            "title": (i.get("name") or "").strip(),
            "brand": (i.get("brand") or "").strip(),
            "category": i.get("category") or "",
            "description": i.get("description") or "",
            "price": f"${float(price):.2f}" if price not in (None, "") else "",
            "savings": i.get("pre_price_text") or "",
            "offer_type": "WeeklyAd",
            "start_date": str(i.get("valid_from") or "")[:10],
            "end_date": str(i.get("valid_to") or "")[:10],
            "image_url": i.get("clean_image_url") or i.get("image_url") or "",
        })
    return [o for o in offers if o["title"]]


# ── Demo data: CHEF'STORE + Grocery Outlet ──────────────────────────────────

CHEFSTORE_PRODUCTS = [
    ("Long Grain White Rice, 50 lb", "Harvest Value", "Pantry", 24.99),
    ("Canola Fryer Oil, 35 lb", "Chef's Line", "Pantry", 42.99),
    ("Chicken Leg Quarters, 40 lb case", "", "Meat & Seafood", 39.99),
    ("80/20 Ground Beef, 10 lb chub", "", "Meat & Seafood", 41.99),
    ("Bacon, 15 lb layout pack", "Patuxent Farms", "Meat & Seafood", 52.99),
    ("Shredded Mozzarella, 5 lb", "Glenview Farms", "Dairy & Eggs", 18.99),
    ("Jumbo Eggs, 15 dozen case", "", "Dairy & Eggs", 54.99),
    ("Salted Butter Solids, 36 lb", "Glenview Farms", "Dairy & Eggs", 129.99),
    ("All-Purpose Flour, 25 lb", "Harvest Value", "Pantry", 12.99),
    ("Granulated Sugar, 25 lb", "Harvest Value", "Pantry", 16.99),
    ("Mayonnaise, 4/1 gal case", "Chef's Line", "Pantry", 34.99),
    ("Russet Potatoes, 50 lb", "", "Produce", 22.99),
    ("Yellow Onions, 50 lb", "", "Produce", 26.99),
    ("Tomato Sauce, 6/#10 cans", "Roseli", "Pantry", 21.99),
    ("16 oz Deli Containers, 240 ct", "Cater Choice", "Supplies", 28.99),
    ("Nitrile Gloves L, 1000 ct", "Daymark", "Supplies", 32.99),
]

GROCERYOUTLET_PRODUCTS = [
    ("Organic Granola, 12 oz", "Nature's Path", "Pantry", 4.99),
    ("Frozen Margherita Pizza", "Screamin' Sicilian", "Frozen", 6.99),
    ("Kombucha, 16 oz", "GT's", "Beverages", 3.49),
    ("Aged White Cheddar, 8 oz", "Tillamook", "Dairy & Eggs", 4.49),
    ("Almond Butter, 16 oz", "Justin's", "Pantry", 9.99),
    ("Sparkling Water 8-pack", "LaCroix", "Beverages", 3.99),
    ("Ice Cream Pint", "Ben & Jerry's", "Frozen", 4.99),
    ("Organic Pasta Sauce, 24 oz", "Newman's Own", "Pantry", 3.99),
    ("Cold Brew Concentrate, 32 oz", "Chameleon", "Beverages", 7.99),
    ("Protein Bars, 12 ct", "KIND", "Snacks", 12.99),
    ("Organic Baby Kale, 5 oz", "Earthbound Farm", "Produce", 2.99),
    ("Uncured Salami, 6 oz", "Applegate", "Deli", 5.99),
    ("Oat Milk, 64 oz", "Oatly", "Dairy & Eggs", 4.49),
    ("Dark Chocolate Bar", "Theo", "Snacks", 2.99),
]


def seed_multichain_demo(weeks: int = 10) -> None:
    h = history()
    conn = h.get_db()
    rng = random.Random(7)
    today = datetime.now().date()
    last_wed = today - timedelta(days=(today.weekday() - 2) % 7)
    specs = [
        ("demo-chefstore-sacramento", CHEFSTORE_PRODUCTS, (0.05, 0.25), "MonthlySpecial"),
        ("demo-groceryoutlet-davis", GROCERYOUTLET_PRODUCTS, (0.30, 0.60), "WOW Deal"),
    ]
    for store_id, products, (dmin, dmax), offer_type in specs:
        total = 0
        for w in range(weeks - 1, -1, -1):
            wed = last_wed - timedelta(weeks=w)
            offers = []
            for i, (name, brand, cat, base) in enumerate(products):
                if rng.random() > 0.5:
                    continue
                depth = rng.uniform(dmin, dmax)
                price = round(base * (1 - depth), 2)
                offers.append({
                    "offer_id": f"{store_id}-{wed}-{i}",
                    "title": name, "brand": brand, "category": cat,
                    "description": f"{brand + ' ' if brand else ''}{name}.",
                    "price": f"${price:.2f}",
                    "savings": f"Save ${base - price:.2f}",
                    "offer_type": offer_type,
                    "start_date": wed.isoformat(),
                    "end_date": (wed + timedelta(days=6)).isoformat(),
                    "image_url": "",
                })
            total += h.ingest_offers(conn, offers, store_id, wed.isoformat(), source="demo")
        print(f"Seeded {total} snapshots for {store_id}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def cmd_stores(args) -> int:
    for zip_code in args.zip:
        print(f"\n=== Stores near {zip_code} ===")
        for banner in (args.banner or ["safeway", "albertsons"]):
            try:
                stores = albertsons_stores(banner, zip_code)
            except Exception as e:  # noqa: BLE001 — report and move on per banner
                print(f"  {banner}: lookup failed ({e})")
                continue
            for s in stores[:args.limit]:
                print(f"  {banner} #{s.get('storeId') or s.get('id')}: "
                      f"{s.get('address', {}).get('line1', s.get('name', '?'))} "
                      f"({s.get('address', {}).get('city', '')})")
        print("  — Flipp circulars (fetch with: fetch --chain flipp --merchant NAME):")
        for m in FLIPP_MERCHANTS:
            try:
                n = len(flipp_fetch(m, zip_code))
                if n:
                    print(f"    {m}: {n} deal items this week")
            except Exception as e:  # noqa: BLE001
                print(f"    {m}: unavailable ({e})")
                break  # if Flipp is blocked entirely, don't spam every merchant
    return 0


def cmd_fetch(args) -> int:
    h = history()
    conn = h.get_db()
    h.purge_demo(conn)
    if args.chain == "flipp":
        if not args.merchant or not args.zip:
            print("flipp needs --merchant and --zip"); return 2
        offers = flipp_fetch(args.merchant, args.zip[0])
        store_key = f"{slug(args.merchant)}-{args.zip[0]}"
    elif args.chain in ALBERTSONS_BANNERS:
        store_id = args.store_id
        if not store_id:
            if not args.zip:
                print(f"{args.chain} needs --store-id or --zip"); return 2
            stores = albertsons_stores(args.chain, args.zip[0])
            if not stores:
                print(f"no {args.chain} stores near {args.zip[0]}"); return 1
            store_id = str(stores[0].get("storeId") or stores[0].get("id"))
            print(f"  nearest {args.chain} store: {store_id}")
        offers = albertsons_fetch(args.chain, store_id)
        store_key = f"{args.chain}-{store_id}"
    else:
        print(f"unknown chain {args.chain!r} — choose from: "
              f"{', '.join(ALBERTSONS_BANNERS)} or flipp"); return 2
    captured = h.ad_week_date(offers)
    n = h.ingest_offers(conn, offers, store_key, captured)
    print(f"Ingested {n} offers for {store_key} as week {captured}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("stores", help="find stores/circulars near zip codes")
    sp.add_argument("--zip", nargs="+", required=True)
    sp.add_argument("--banner", nargs="+", choices=list(ALBERTSONS_BANNERS))
    sp.add_argument("--limit", type=int, default=3)

    fp = sub.add_parser("fetch", help="fetch one chain's deals into the tracker")
    fp.add_argument("--chain", required=True)
    fp.add_argument("--store-id")
    fp.add_argument("--zip", nargs="+")
    fp.add_argument("--merchant", help="Flipp merchant name, e.g. \"Grocery Outlet\"")

    dp = sub.add_parser("demo", help="seed multi-chain demo data")
    dp.add_argument("--weeks", type=int, default=10)

    args = ap.parse_args()
    if args.cmd == "stores":
        return cmd_stores(args)
    if args.cmd == "fetch":
        return cmd_fetch(args)
    seed_multichain_demo(args.weeks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
