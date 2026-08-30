"""Safeway weekly deals scraper.

Pulls deals/coupons from Safeway's public "companion gallery" API for a given
store, writes them to CSV + Excel, and (optionally) pushes to Google Sheets.

Usage:
    python 046_safeway_deals_scraper.py --store-id 2926
    python 046_safeway_deals_scraper.py --zip 94107
    python 046_safeway_deals_scraper.py --store-id 2926 --sheet "Safeway Deals"

Find your store id by visiting safeway.com, picking a store, and copying the
number from the URL (e.g. /shop/aisles?storeId=2926). Or pass --zip and the
script will resolve the nearest store for you.

Note: Safeway's edge (Akamai) sometimes blocks requests from cloud IPs with a
403. If that happens, open safeway.com in your browser, copy the `Cookie`
header from DevTools -> Network on any xapi request, and set it in the
SAFEWAY_COOKIE env var before running this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

OUT_DIR = Path(__file__).parent / "runs" / "safeway"

# Safeway's site calls these internal "xapi" endpoints from the browser. They
# return JSON without auth as long as you send a normal User-Agent.
STORE_SEARCH_URL = "https://www.safeway.com/abs/pub/xapi/storeresolver/storesearch"
GALLERY_URL = "https://www.safeway.com/abs/pub/xapi/offers/companiongalleryoffer"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.safeway.com/foru/coupons-deals.html",
}
if os.environ.get("SAFEWAY_COOKIE"):
    HEADERS["Cookie"] = os.environ["SAFEWAY_COOKIE"]


@dataclass
class Deal:
    offer_id: str
    title: str
    description: str
    price: str           # e.g. "$2.99" or "BOGO"
    savings: str         # e.g. "Save $1.00"
    offer_type: str      # WeeklySpecial / ManufactureCoupon / PersonalizedDeal
    category: str
    brand: str
    start_date: str
    end_date: str
    image_url: str
    extra: dict = field(default_factory=dict)


def resolve_store_id(zip_code: str) -> str:
    """Look up the nearest Safeway store for a zip code."""
    r = requests.get(
        STORE_SEARCH_URL,
        params={"request-type": "google-search", "search-string": zip_code, "banner": "safeway"},
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    stores = data.get("stores") or data.get("response", {}).get("stores") or []
    if not stores:
        raise RuntimeError(f"No Safeway stores found for zip {zip_code}")
    store_id = str(stores[0].get("storeId") or stores[0].get("id"))
    print(f"  resolved zip {zip_code} -> store {store_id} ({stores[0].get('name', '?')})")
    return store_id


def fetch_gallery(store_id: str) -> list[dict[str, Any]]:
    """Fetch the full deals/coupons gallery for a store."""
    params = {
        "storeId": store_id,
        "rand": int(time.time() * 1000),
    }
    r = requests.get(GALLERY_URL, params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    data = r.json()
    # The API returns a list under one of these keys depending on version.
    offers = (
        data.get("companionGalleryOffer")
        or data.get("offers")
        or data.get("response", {}).get("companionGalleryOffer")
        or []
    )
    return offers


def parse_offer(raw: dict[str, Any]) -> Deal:
    """Normalize one raw API offer into a flat Deal record."""
    return Deal(
        offer_id=str(raw.get("offerId") or raw.get("id") or ""),
        title=raw.get("name") or raw.get("title") or "",
        description=raw.get("description") or raw.get("offerDescription") or "",
        price=raw.get("offerPrice") or raw.get("price") or "",
        savings=raw.get("savings") or raw.get("offerSummary") or "",
        offer_type=raw.get("offerPgmCd") or raw.get("offerType") or "",
        category=", ".join(raw.get("categories") or []) or raw.get("category", ""),
        brand=raw.get("brand") or "",
        start_date=raw.get("offerStartDate") or raw.get("startDate") or "",
        end_date=raw.get("offerEndDate") or raw.get("endDate") or "",
        image_url=raw.get("image") or raw.get("imageUrl") or "",
        extra={k: v for k, v in raw.items() if k not in {
            "offerId", "id", "name", "title", "description", "offerDescription",
            "offerPrice", "price", "savings", "offerSummary", "offerPgmCd",
            "offerType", "categories", "category", "brand", "offerStartDate",
            "startDate", "offerEndDate", "endDate", "image", "imageUrl",
        }},
    )


def write_csv(deals: list[Deal], path: Path) -> None:
    if not deals:
        return
    fields = [f for f in asdict(deals[0]).keys() if f != "extra"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for d in deals:
            row = asdict(d)
            row.pop("extra", None)
            w.writerow(row)


def write_excel(deals: list[Deal], path: Path) -> bool:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        print("  (skipping .xlsx — `pip install openpyxl` to enable)")
        return False
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Safeway Deals"
    headers = [f for f in asdict(deals[0]).keys() if f != "extra"] if deals else []
    ws.append(headers)
    for d in deals:
        row = asdict(d)
        ws.append([row[h] for h in headers])
    wb.save(path)
    return True


def push_to_google_sheet(deals: list[Deal], sheet_name: str) -> bool:
    """Push to Google Sheets if gspread + service account creds are available."""
    try:
        import gspread  # type: ignore
        from google.oauth2.service_account import Credentials  # type: ignore
    except ImportError:
        print("  (skipping Google Sheets — gspread / google-auth not installed)")
        return False
    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not Path(creds_path).exists():
        print("  (skipping Google Sheets — set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON)")
        return False
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc = gspread.authorize(creds)
    try:
        sh = gc.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(sheet_name)
    ws = sh.sheet1
    ws.clear()
    headers = [f for f in asdict(deals[0]).keys() if f != "extra"] if deals else []
    rows = [headers] + [[str(asdict(d)[h]) for h in headers] for d in deals]
    ws.update("A1", rows)
    print(f"  pushed {len(deals)} rows to Google Sheet '{sheet_name}'")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--store-id", help="Safeway store id (e.g. 2926)")
    g.add_argument("--zip", help="Zip code; resolves to nearest store")
    ap.add_argument("--sheet", help="Google Sheet name to push to (optional)")
    ap.add_argument("--out-dir", default=str(OUT_DIR), help="Output directory")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    store_id = args.store_id or resolve_store_id(args.zip)
    print(f"Fetching deals for store {store_id}...")
    raw = fetch_gallery(store_id)
    print(f"  got {len(raw)} raw offers")

    deals = [parse_offer(o) for o in raw]
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    base = out_dir / f"safeway_{store_id}_{stamp}"

    (base.with_suffix(".raw.json")).write_text(json.dumps(raw, indent=2))
    write_csv(deals, base.with_suffix(".csv"))
    write_excel(deals, base.with_suffix(".xlsx"))
    print(f"  wrote {base}.csv / .xlsx / .raw.json")

    if args.sheet:
        push_to_google_sheet(deals, args.sheet)

    return 0


if __name__ == "__main__":
    sys.exit(main())
