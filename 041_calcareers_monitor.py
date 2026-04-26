"""
CalCareers Monitor — California state jobs (calcareers.ca.gov)

Scrapes the public CalCareers job search page, detects NEW postings since the
last run (via a persistent seen-ids file), normalises rows into the shared
jobs.csv / jobs.json format, and syncs to Google Sheets.

Not an applier — CalCareers requires a logged-in session and a full-form
application that varies per job. This stage's job is discovery + alerting, so
the Handshake/LinkedIn appliers can focus on Easy Apply while we track state
roles on the side.

Usage:
  python 041_calcareers_monitor.py
  python 041_calcareers_monitor.py --dry-run          # no state file write, no gsheet sync
  python 041_calcareers_monitor.py --pages 5          # how many result pages to scan
  python 041_calcareers_monitor.py --keywords "QA Engineer,Software Engineer"
"""

import argparse
import csv
import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from library.gsheets import sync_jobs
except Exception:
    sync_jobs = None   # optional — monitor still writes local files

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="No state-file write, no sheet sync")
parser.add_argument("--pages", type=int, default=3, help="Result pages to scan per keyword")
parser.add_argument("--keywords", type=str,
                    default="QA Engineer,Software Engineer,Quality Assurance,Information Technology Specialist")
parser.add_argument("--locations", type=str, default="Sacramento,Davis,Remote")
args = parser.parse_args()

KEYWORDS  = [k.strip() for k in args.keywords.split(",") if k.strip()]
LOCATIONS = [l.strip() for l in args.locations.split(",") if l.strip()]

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
STATE_FILE  = os.path.join(SCRIPT_DIR, ".calcareers_seen.json")
RUN_ID      = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR     = os.path.join(SCRIPT_DIR, "runs", f"calcareers_monitor_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log")),
        logging.StreamHandler(sys.stdout),
    ],
)

# ── Constants ─────────────────────────────────────────────────────────────────
BASE       = "https://www.calcareers.ca.gov"
SEARCH_URL = f"{BASE}/CalHrPublic/Search/JobSearchResults.aspx"
JOB_URL    = f"{BASE}/CalHrPublic/Jobs/JobPosting.aspx"

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

JOBID_RE = re.compile(r"JobControlId=(\d+)", re.IGNORECASE)


# ── State ─────────────────────────────────────────────────────────────────────
def load_seen() -> set[str]:
    if not os.path.exists(STATE_FILE):
        return set()
    try:
        with open(STATE_FILE) as f:
            return set(json.load(f))
    except Exception as e:
        logging.warning(f"could not load seen-ids state: {e}")
        return set()


def save_seen(seen: set[str]):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


# ── Scraper ───────────────────────────────────────────────────────────────────
def fetch_search_page(keyword: str, page: int = 1) -> str:
    """GET the CalCareers search page. Returns HTML or empty string."""
    params = {
        "JobTitle": keyword,
        "PageNumber": page,
    }
    try:
        r = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logging.warning(f"fetch failed kw={keyword!r} page={page}: {e}")
        return ""


def parse_listings(html: str, keyword: str) -> list[dict]:
    """
    Extract (job_id, title, dept, location, salary, deadline, url) from the
    search results page. CalCareers' markup shifts occasionally, so we key off
    every anchor linking to JobPosting.aspx?JobControlId=… and read sibling
    cells defensively.
    """
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    jobs: list[dict] = []

    for a in soup.find_all("a", href=JOBID_RE):
        href = a.get("href", "")
        m = JOBID_RE.search(href)
        if not m:
            continue
        job_id = m.group(1)
        title = a.get_text(strip=True)
        if not title:
            continue

        # Walk up to the row / card that contains this anchor, then mine
        # nearby text blocks for metadata.
        row = a
        for _ in range(4):
            if row is None:
                break
            if row.name in ("tr", "li", "article", "div") and len(row.get_text(strip=True)) > len(title) + 10:
                break
            row = row.parent

        row_text = row.get_text(" | ", strip=True) if row else ""
        jobs.append({
            "job_id":        job_id,
            "title":         title,
            "url":           urljoin(BASE, href) if href.startswith("/") else f"{JOB_URL}?JobControlId={job_id}",
            "company":       _extract_near(row_text, r"(Department|Dept\.?|Agency):?\s*([^|]+)") or "State of California",
            "location_raw":  _extract_near(row_text, r"(Location|Worksite|Work Location):?\s*([^|]+)"),
            "salary_raw":    _extract_near(row_text, r"(Salary|Pay)[^:]*:\s*([^|]+)"),
            "deadline_raw":  _extract_near(row_text, r"(Final Filing Date|Closing Date|Deadline):?\s*([^|]+)"),
            "posted_raw":    _extract_near(row_text, r"(Publish Date|Posted|Date Posted):?\s*([^|]+)"),
            "keyword":       keyword,
            "raw_row":       row_text[:400],
        })
    return jobs


def _extract_near(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(2).strip() if m else ""


# ── Filtering ─────────────────────────────────────────────────────────────────
def location_ok(raw: str) -> bool:
    if not raw:
        return True   # unknown location → keep, let a human decide
    low = raw.lower()
    return any(loc.lower() in low for loc in LOCATIONS)


EXCLUDE_TITLE = {
    "manager", "supervisor", "director", "chief", "administrator",
    "deputy", "executive", "lead", " sr.", " sr ", "senior", "principal",
}

def title_ok(title: str) -> bool:
    low = title.lower()
    return not any(tok in low for tok in EXCLUDE_TITLE)


# ── Normalisation ─────────────────────────────────────────────────────────────
SALARY_RE = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)\s*(?:[-–to]+\s*\$?\s*([\d,]+(?:\.\d+)?))?", re.IGNORECASE)

def parse_salary(raw: str) -> dict:
    out = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return out
    m = SALARY_RE.search(raw)
    if m:
        out["salary_min"] = float(m.group(1).replace(",", ""))
        if m.group(2):
            out["salary_max"] = float(m.group(2).replace(",", ""))
    low = raw.lower()
    if "hour" in low or "/hr" in low:
        out["salary_unit"] = "hr"
    elif "month" in low or "/mo" in low:
        out["salary_unit"] = "mo"
    else:
        out["salary_unit"] = "yr"
    return out


def normalise(job: dict) -> dict:
    sal = parse_salary(job.get("salary_raw", ""))
    loc_low = (job.get("location_raw") or "").lower()
    remote_type = "remote" if "remote" in loc_low else ("hybrid" if "hybrid" in loc_low else "onsite")
    return {
        "timestamp":         datetime.now().isoformat(),
        "platform":          "CalCareers",
        "job_id":            job["job_id"],
        "title":             job["title"],
        "company":           job.get("company", "State of California"),
        "location":          job.get("location_raw", ""),
        "location_raw":      job.get("location_raw", ""),
        "remote_type":       remote_type,
        "url":               job["url"],
        "employment_type":   "full-time",
        "salary_min":        sal["salary_min"],
        "salary_max":        sal["salary_max"],
        "salary_unit":       sal["salary_unit"],
        "salary_raw":        job.get("salary_raw", ""),
        "skills_mentioned":  "",
        "apply_type":        "external",
        "status":            "discovered",   # pipeline is monitor-only
        "deadline_raw":      job.get("deadline_raw", ""),
        "posted_raw":        job.get("posted_raw", ""),
        "days_since_posted": "",
        "notes":             f"search_keyword={job.get('keyword','')}",
    }


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> int:
    seen = load_seen()
    logging.info(f"loaded {len(seen)} previously-seen job IDs")
    logging.info(f"keywords={KEYWORDS} locations={LOCATIONS} pages={args.pages} dry_run={args.dry_run}")

    found: dict[str, dict] = {}      # job_id → raw job dict (dedup across keywords)

    for kw in KEYWORDS:
        for page in range(1, args.pages + 1):
            html = fetch_search_page(kw, page)
            if not html:
                break
            listings = parse_listings(html, kw)
            logging.info(f"  kw={kw!r} page={page}: {len(listings)} listings")
            if not listings:
                break
            for job in listings:
                found.setdefault(job["job_id"], job)
            time.sleep(1.5)   # be polite to calcareers.ca.gov

    new_jobs: list[dict] = []
    all_rows: list[dict] = []
    for jid, raw in found.items():
        row = normalise(raw)
        all_rows.append(row)
        if jid in seen:
            continue
        if not title_ok(row["title"]):
            row["status"] = "skipped_title"
            continue
        if not location_ok(row["location"]):
            row["status"] = "skipped_location"
            continue
        new_jobs.append(row)

    # ── Persist ───────────────────────────────────────────────────────────────
    data_file = os.path.join(RUN_DIR, "jobs.json")
    csv_file  = os.path.join(RUN_DIR, "jobs.csv")
    with open(data_file, "w") as f:
        json.dump(all_rows, f, indent=2)
    if all_rows:
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(all_rows[0].keys()), extrasaction="ignore")
            w.writeheader()
            w.writerows(all_rows)

    logging.info(f"found={len(found)} new={len(new_jobs)} total_rows={len(all_rows)}")
    for j in new_jobs[:20]:
        logging.info(f"  NEW  {j['job_id']:>8}  {j['title'][:60]:<60}  {j['location'][:30]}")

    # ── State + sheet sync ────────────────────────────────────────────────────
    if not args.dry_run:
        seen.update(found.keys())
        save_seen(seen)
        if sync_jobs and new_jobs:
            try:
                sync_jobs(new_jobs, platform="CalCareers")
            except Exception as e:
                logging.warning(f"gsheets sync failed (non-fatal): {e}")

    # Summary line consumed by the unified pipeline
    print(f"CALCAREERS_SUMMARY found={len(found)} new={len(new_jobs)} run_dir={RUN_DIR}")
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
