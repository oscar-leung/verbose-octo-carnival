"""
Handshake Job Scraper — SCRAPE ONLY, NO APPLY
Goal: collect as much structured data as fast as possible
Output: runs/<timestamp>/jobs.json + jobs.csv

Usage:
  python 034_handshake_job_scraper.py
  python 034_handshake_job_scraper.py --resume runs/2026-04-01_10-00-00
"""

import argparse
import logging
import random
import time
import json
import os
import re
import csv
from collections import Counter
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, ElementClickInterceptedException,
    StaleElementReferenceException, TimeoutException, ElementNotInteractableException
)
import pyautogui
from dotenv import load_dotenv

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--resume", metavar="RUN_DIR",
                    help="Resume a previous run (loads existing jobs.json, skips seen IDs)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_PAGES   = 400          # 400 pages × ~25 = ~10k jobs
CARD_WAIT_MIN = 0.4          # jittered wait after clicking a card
CARD_WAIT_MAX = 0.8
PAGE_WAIT_MIN = 1.5          # between pages
PAGE_WAIT_MAX = 2.5
SAVE_EVERY    = 10           # flush to disk every N new jobs

# ── Run folder ────────────────────────────────────────────────────────────────
if args.resume:
    RUN_DIR = args.resume
    if not os.path.isdir(RUN_DIR):
        raise SystemExit(f"Resume dir not found: {RUN_DIR}")
    RUN_ID = os.path.basename(RUN_DIR)
else:
    RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RUN_DIR = os.path.join("runs", f"handshake_scraper_{RUN_ID}")
    os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log")),
        logging.StreamHandler(),
    ],
)
logging.info(f"Run ID: {RUN_ID}  →  {RUN_DIR}/")

DATA_FILE = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE  = os.path.join(RUN_DIR, "jobs.csv")

CSV_COLUMNS = [
    "job_id", "url", "page", "index",
    "title", "company", "industry",
    "location_raw", "city", "state", "country", "remote_type",
    "salary_raw", "salary_min", "salary_max", "salary_unit",
    "job_type", "employment_type",
    "deadline_raw", "deadline_date",
    "posted_raw", "posted_date", "days_since_posted",
    "work_auth_required", "visa_sponsorship",
    "description_full",
    "skills_mentioned",
    "qualifications_raw",
    "benefits_raw",
    "company_size", "company_location",
    "timestamp",
]

# Load existing jobs when resuming
all_jobs: list[dict] = []
seen_ids: set[str]   = set()

if args.resume and os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        all_jobs = json.load(f)
    seen_ids = {j["job_id"] for j in all_jobs if j.get("job_id")}
    logging.info(f"Resumed: {len(all_jobs)} existing jobs, {len(seen_ids)} unique IDs")

# ── Parsing helpers ───────────────────────────────────────────────────────────

def parse_salary(raw: str) -> dict:
    """
    Parse salary strings like '$75–90K/yr', '$40-120/hr', '$120,000/yr'.
    Applies K multiplier per token so mixed ranges work correctly.
    """
    out = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return out

    unit_match = re.search(r"/(yr|hr|mo|month|year|hour)", raw, re.I)
    out["salary_unit"] = unit_match.group(1).lower() if unit_match else None

    # Split on common range separators to handle K per-token
    tokens = re.split(r"[–\-–—to]+", raw)
    values = []
    for token in tokens:
        m = re.search(r"([\d,]+\.?\d*)\s*[Kk]?", token)
        if m:
            num = float(m.group(0).replace(",", "").rstrip("Kk").strip())
            if re.search(r"\d\s*[Kk]", token):
                num *= 1000
            values.append(num)

    if len(values) >= 2:
        out["salary_min"], out["salary_max"] = values[0], values[1]
    elif len(values) == 1:
        out["salary_min"] = values[0]
    return out


def parse_location(raw: str) -> dict:
    """Split 'Onsite, based in Redlands, CA' into city/state/remote_type."""
    out = {"city": None, "state": None, "country": "United States", "remote_type": "onsite"}
    if not raw:
        return out
    low = raw.lower()
    if "remote" in low and ("hybrid" in low or "onsite" in low):
        out["remote_type"] = "hybrid"
    elif "remote" in low:
        out["remote_type"] = "remote"

    m = re.search(r"(?:based in\s+)?([A-Za-z][A-Za-z\s\.]+),\s*([A-Z]{2})\b", raw)
    if m:
        out["city"]  = m.group(1).strip()
        out["state"] = m.group(2).strip()
    return out


def parse_deadline(raw: str) -> str | None:
    """Extract ISO date from 'Apply by May 1, 2026 at 11:59 PM'."""
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", raw)
    if m:
        try:
            return datetime.strptime(m.group(1).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


def parse_posted(raw: str) -> tuple[str | None, int | None]:
    """
    Convert relative posted strings to an ISO date + days count.

    Handles:
      "Posted 1 day ago", "Posted 3 days ago", "Posted 2 weeks ago"
      "1wk ago", "33mo ago", "4d ago"
      "just now", "today", "yesterday"
    """
    if not raw:
        return None, None

    now  = datetime.now()
    text = raw.lower()

    m = re.search(
        r"(\d+)\s*"
        r"(day|days|d|week|weeks|wk|wks|month|months|mo|mos|hour|hours|hr|hrs|year|years|yr|yrs)",
        text,
    )
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit in ("hour", "hours", "hr", "hrs"):
            delta = timedelta(hours=n)
        elif unit in ("day", "days", "d"):
            delta = timedelta(days=n)
        elif unit in ("week", "weeks", "wk", "wks"):
            delta = timedelta(weeks=n)
        elif unit in ("month", "months", "mo", "mos"):
            delta = timedelta(days=n * 30)
        else:  # year/yr
            delta = timedelta(days=n * 365)
        return (now - delta).strftime("%Y-%m-%d"), delta.days

    if any(kw in text for kw in ("just now", "today", "moments ago")):
        return now.strftime("%Y-%m-%d"), 0
    if "yesterday" in text:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d"), 1

    return None, None


SKILLS = [
    "python", "java", "javascript", "typescript", "react", "vue", "angular",
    "node", "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "git", "ci/cd",
    "rest", "graphql", "grpc", "machine learning", "deep learning", "pytorch",
    "tensorflow", "scikit-learn", "llm", "rag", "langchain", "openai", "hugging face",
    "c++", "c#", "golang", "rust", "swift", "kotlin", "flutter", "dart",
    "html", "css", "tailwind", "django", "flask", "fastapi", "spring", "rails",
    "express", "linux", "bash", "agile", "scrum", "jira", "figma",
    "spark", "kafka", "airflow",
]

def extract_skills(text: str) -> str:
    low = text.lower()
    return ", ".join(s for s in SKILLS if s in low)


# ── Browser helpers ───────────────────────────────────────────────────────────

def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)
    for _ in range(5):
        pyautogui.hotkey('command', '-')

def move_window_to_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i')
    time.sleep(0.2)

def el_exists(xpath, timeout=2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return True
    except Exception:
        return False

def safe_text(xpath, timeout=3) -> str:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        ).text.strip()
    except Exception:
        return ""

def safe_texts(xpath, timeout=3) -> list[str]:
    """Wait for the first match, then collect all visible text items."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return [e.text.strip() for e in driver.find_elements(By.XPATH, xpath) if e.text.strip()]
    except Exception:
        return []

def fast_click(xpath, timeout=3):
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].click();", el)
    except Exception:
        pass

def get_job_id() -> str:
    m = re.search(r"/jobs/(\d+)", driver.current_url)
    return m.group(1) if m else ""

def expand_description():
    """Click view-more button to reveal the full job description."""
    for xp in [
        "//button[contains(@class,'view-more-button')]",
        "//button[contains(@aria-label,'Show more')]",
        "//button[normalize-space()='More']",
    ]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return


# ── Job data collector ────────────────────────────────────────────────────────

def collect_job_data(index: int, page: int) -> dict:
    expand_description()

    job_id = get_job_id()
    url    = f"https://app.joinhandshake.com/jobs/{job_id}" if job_id else driver.current_url

    title      = safe_text("//h1[contains(@class,'job-title')] | //h1[contains(@class,'dmTfkw')]")
    company    = safe_text("//div[contains(@class,'gBthqB')] | //*[@data-hook='employer-name']")
    industry   = safe_text("//div[contains(@class,'hrTUzH')] | //*[@data-hook='employer-industry']")
    posted_raw = safe_text("//*[contains(@class,'fsLGJY')] | //*[@data-hook='posted-date']")

    # "At a glance" fields — use indexed safe_text so order mismatches don't shift values
    salary_raw   = safe_text("//*[contains(@class,'dVnqLS')][1]")
    location_raw = safe_text("//*[contains(@class,'dVnqLS')][2]")
    job_type     = safe_text("//*[contains(@class,'dVnqLS')][3]")

    # Work authorisation
    work_auth_raw = safe_text("//*[@data-hook='work-auth-title']", timeout=1)
    work_auth_req = "yes" if "required" in work_auth_raw.lower() else ("no" if work_auth_raw else "")

    visa_text        = safe_text(
        "//*[contains(normalize-space(),'visa sponsor') or "
        "contains(normalize-space(),'OPT') or contains(normalize-space(),'CPT')]",
        timeout=1,
    )
    visa_sponsorship = "yes" if visa_text else "no"

    # Full description — try two selectors, fall back if result is short
    desc = safe_text(
        "//*[@data-hook='job-description'] | //div[contains(@style,'overflow-wrap')]",
        timeout=4,
    )
    if len(desc) < 200:
        desc = safe_text("//div[contains(@class,'hkJwbQ')][2]//div", timeout=2)

    # Deadline
    deadline_raw = posted_raw if "Apply by" in posted_raw else \
        safe_text("//*[contains(normalize-space(),'Apply by')]", timeout=1)

    # Benefits & qualifications
    benefits_raw = " | ".join(safe_texts("//ul[contains(@class,'dpqcEU')]//li"))
    quals_raw    = " | ".join(safe_texts("//*[contains(@class,'dsAqlh')]"))

    # Company info sidebar
    company_size     = safe_text("//*[contains(@class,'jCQffL')][1]", timeout=1)
    company_location = safe_text("//*[contains(@class,'jCQffL')][2]//p", timeout=1)

    # Parse structured fields
    sal               = parse_salary(salary_raw)
    loc               = parse_location(location_raw)
    deadline_date     = parse_deadline(deadline_raw)
    posted_date, days = parse_posted(posted_raw)
    emp = (
        "full-time"  if "full"   in job_type.lower() else
        "internship" if "intern" in job_type.lower() else
        "part-time"  if "part"   in job_type.lower() else
        job_type.lower()
    )

    return {
        "job_id": job_id, "url": url,
        "page": page, "index": index,
        "title": title, "company": company, "industry": industry,
        "location_raw": location_raw, **loc,
        "salary_raw": salary_raw, **sal,
        "job_type": job_type, "employment_type": emp,
        "deadline_raw": deadline_raw, "deadline_date": deadline_date,
        "posted_raw": posted_raw, "posted_date": posted_date, "days_since_posted": days,
        "work_auth_required": work_auth_req, "visa_sponsorship": visa_sponsorship,
        "description_full": desc[:8000],
        "skills_mentioned": extract_skills(desc),
        "qualifications_raw": quals_raw,
        "benefits_raw": benefits_raw,
        "company_size": company_size,
        "company_location": company_location,
        "timestamp": datetime.now().isoformat(),
    }


# ── Persistence ───────────────────────────────────────────────────────────────

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(all_jobs, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_jobs)


# ── Login & navigation ────────────────────────────────────────────────────────

load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")

driver = webdriver.Chrome()

driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
zoom_out()
move_window_to_topright()

driver.find_element(By.ID, "email-address-identifier").send_keys(username)
fast_click("//button[normalize-space()='Next']")
time.sleep(1)
fast_click("//a[normalize-space()='Log in another way']")
time.sleep(0.5)
driver.find_element(By.ID, "password").send_keys(password)
fast_click("//button[normalize-space()='Log in']")
time.sleep(3)

driver.get("https://app.joinhandshake.com/job-search/")
time.sleep(2)

# ── Pagination loop ───────────────────────────────────────────────────────────

# Try multiple selectors: the inner div index can shift; fall back to any data-hook card
CARDS_XPATHS = [
    "//div[@aria-label='Jobs List']//div[contains(@data-hook,'job-result-card')]",
    "//*[contains(@data-hook,'job-result-card')]",
    "//div[contains(@class,'job-result-card')]",
]

def find_cards():
    for xp in CARDS_XPATHS:
        cards = driver.find_elements(By.XPATH, xp)
        if cards:
            return cards
    return []
unsaved_count = 0

for page in range(1, TOTAL_PAGES + 1):
    logging.info(f"\n{'='*60}")
    logging.info(f"  PAGE {page}/{TOTAL_PAGES}  |  scraped so far: {len(all_jobs)}")
    logging.info(f"{'='*60}")

    if page > 1:
        next_btn = f"//button[@value='{page}' and not(@aria-current='page')]"
        if not el_exists(next_btn, timeout=5):
            logging.info("No next-page button — done.")
            break
        fast_click(next_btn)
        time.sleep(random.uniform(PAGE_WAIT_MIN, PAGE_WAIT_MAX))

    cards = find_cards()
    n = len(cards)
    logging.info(f"  {n} cards on page {page}")

    for idx in range(n):
        try:
            all_cards = find_cards()
            if idx >= len(all_cards):
                continue

            card = all_cards[idx]
            # Try multiple link selectors — Handshake UI varies
            link = None
            for lxp in [".//a[@role='button']", ".//a[contains(@href,'/jobs/')]", ".//a"]:
                try:
                    link = card.find_element(By.XPATH, lxp)
                    break
                except Exception:
                    pass
            if link is None:
                driver.execute_script("arguments[0].click();", card)
            else:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                driver.execute_script("arguments[0].click();", link)
            time.sleep(random.uniform(CARD_WAIT_MIN, CARD_WAIT_MAX))

            job = collect_job_data(idx + 1, page)

            # Skip duplicates (can arise when resuming or across paginated results)
            if job["job_id"] and job["job_id"] in seen_ids:
                logging.info(f"  [{idx+1:02}/{n}] Duplicate job_id {job['job_id']} — skipping")
                continue

            logging.info(
                f"  [{idx+1:02}/{n}] {job['title'][:36]:<36} | "
                f"{job['company'][:20]:<20} | {job['salary_raw'] or '—':<12} | "
                f"posted {job['days_since_posted']}d ago"
            )
            all_jobs.append(job)
            if job["job_id"]:
                seen_ids.add(job["job_id"])
            unsaved_count += 1

            if unsaved_count >= SAVE_EVERY:
                save_data()
                unsaved_count = 0

        except Exception as e:
            logging.error(f"  Card {idx+1} error: {type(e).__name__}: {e}")

    save_data()
    unsaved_count = 0
    logging.info(f"  Saved. Total: {len(all_jobs)} jobs")
    time.sleep(random.uniform(PAGE_WAIT_MIN, PAGE_WAIT_MAX))

# ── Done ──────────────────────────────────────────────────────────────────────

save_data()

logging.info("\n" + "=" * 60)
logging.info(f"DONE  —  {len(all_jobs)} jobs scraped")

# Top companies
top_companies = Counter(j["company"] for j in all_jobs if j.get("company")).most_common(10)
logging.info("\nTop companies:")
for company, count in top_companies:
    logging.info(f"  {company:<35} {count:>4}")

# Skills distribution
all_skills: list[str] = []
for j in all_jobs:
    if j.get("skills_mentioned"):
        all_skills.extend(s.strip() for s in j["skills_mentioned"].split(",") if s.strip())
top_skills = Counter(all_skills).most_common(15)
logging.info("\nTop skills mentioned:")
for skill, count in top_skills:
    logging.info(f"  {skill:<20} {count:>4}")

# Employment type breakdown
emp_counts = Counter(j.get("employment_type", "unknown") for j in all_jobs)
logging.info(f"\nEmployment types: {dict(emp_counts)}")

logging.info(f"\n  JSON  →  {DATA_FILE}")
logging.info(f"  CSV   →  {CSV_FILE}")
logging.info(f"  Log   →  {os.path.join(RUN_DIR, 'run.log')}")

driver.quit()

# ── Sync to Google Sheets ──────────────────────────────────────────────────────
try:
    import sys as _sys, os as _os
    _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
    from library.gsheets import sync_jobs
    sync_jobs(all_jobs, platform="Handshake")
    logging.info("Synced to Google Sheets.")
except Exception as _gs_err:
    logging.warning(f"Google Sheets sync skipped: {_gs_err}")
