"""
Handshake Easy Apply — PythonAnywhere Edition
Headless Chrome, no pyautogui. Applies only to Handshake-native jobs (no external redirects).

PythonAnywhere setup:
  Same as 035 — add as a separate daily task at a different time, e.g. 9:00 AM:
    python /home/<username>/verbose-octo-carnival/036_handshake_apply_pa.py

Usage (local):
  python 036_handshake_apply_pa.py
  python 036_handshake_apply_pa.py --dry-run
  python 036_handshake_apply_pa.py --resume runs/handshake_apply_pa_2026-04-06_09-00-00
"""

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timedelta

from dotenv import load_dotenv
import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import library.uc_compat  # noqa: F401
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true", help="Collect data, do not submit")
parser.add_argument("--resume", metavar="RUN_DIR", help="Resume a previous run")
parser.add_argument("--max-applies", type=int, default=30, help="Max applications per session (default 30)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_PAGES     = 20   # reduced — we iterate multiple searches instead
APPLY_PAUSE_MIN = 1.2
APPLY_PAUSE_MAX = 2.5
SAVE_EVERY      = 5
MAX_APPLIES     = args.max_applies

COVER_LETTER_NAME = "HandShake Cover Letter"
TRANSCRIPT_NAME   = "0JH7198571 | SJSU Transcript | Oscar Leung"
RESUME_NAME       = "Oscar Leung Resume"

# ── Target roles & locations ──────────────────────────────────────────────────
# Search keywords — each gets typed into the Handshake search bar
SEARCH_KEYWORDS = [
    "QA Automation Engineer",
    "QA Engineer",
    "Software Engineer in Test",
    "SDET",
    "Software Quality Engineer",
    "Software Engineer",
]

# Accepted locations — job must match one of these (or be remote/hybrid) to be applied to
LOCATION_ACCEPT = {"sacramento", "davis", "remote", "hybrid", "anywhere", "nationwide"}

# Titles to skip
TITLE_EXCLUDE = {
    "senior", " sr ", "sr.", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "intern", "internship",
    "founding", "sales", "field", "hardware", "firmware", "embedded",
}

def title_ok(title: str) -> bool:
    low = title.lower()
    return not any(tok in low for tok in TITLE_EXCLUDE)

def location_ok(location_raw: str) -> bool:
    """Accept Sacramento, Davis, remote, or empty (assume remote-friendly)."""
    if not location_raw:
        return True
    low = location_raw.lower()
    return any(tok in low for tok in LOCATION_ACCEPT)

# ── Run folder ────────────────────────────────────────────────────────────────
if args.resume:
    RUN_DIR = args.resume
    if not os.path.isdir(RUN_DIR):
        raise SystemExit(f"Resume dir not found: {RUN_DIR}")
    RUN_ID = os.path.basename(RUN_DIR)
else:
    RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RUN_DIR = os.path.join("runs", f"handshake_apply_pa_{RUN_ID}")
    os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log")),
        logging.StreamHandler(sys.stdout),
    ],
)

DATA_FILE = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE  = os.path.join(RUN_DIR, "jobs.csv")

CSV_COLUMNS = [
    "page", "index", "job_id", "url",
    "title", "company", "industry",
    "location_raw", "city", "state", "country", "remote_type",
    "salary_raw", "salary_min", "salary_max", "salary_unit",
    "job_type", "employment_type",
    "deadline_raw", "deadline_date",
    "posted_raw", "posted_date", "days_since_posted",
    "work_auth_required", "visa_sponsorship",
    "description_full", "skills_mentioned",
    "qualifications_raw", "benefits_raw",
    "company_size", "company_location",
    "apply_type", "status", "timestamp",
]

all_jobs: list[dict] = []
seen_ids: set[str]   = set()

if args.resume and os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        all_jobs = json.load(f)
    seen_ids = {j["job_id"] for j in all_jobs if j.get("job_id")}
    logging.info(f"Resumed: {len(all_jobs)} jobs, {len(seen_ids)} unique IDs")

_unsaved = 0
_JS_CLICK = "arguments[0].click();"

def record_job(job: dict):
    global _unsaved
    all_jobs.append(job)
    _unsaved += 1
    if _unsaved >= SAVE_EVERY:
        _flush()

def _flush(force=False):
    global _unsaved
    if not force and _unsaved < SAVE_EVERY:
        return
    with open(DATA_FILE, "w") as f:
        json.dump(all_jobs, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(all_jobs)
    _unsaved = 0

# ── Parsing ───────────────────────────────────────────────────────────────────
def parse_salary(raw: str) -> dict:
    out = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return out
    m = re.search(r"/(yr|hr|mo|month|year|hour)", raw, re.I)
    out["salary_unit"] = m.group(1).lower() if m else None
    tokens = re.split(r"[–\-—to]+", raw)
    values = []
    for token in tokens:
        match = re.search(r"([\d,]+\.?\d*)\s*[Kk]?", token)
        if match:
            num = float(match.group(0).replace(",", "").rstrip("Kk").strip())
            if re.search(r"\d\s*[Kk]", token):
                num *= 1000
            values.append(num)
    if len(values) >= 2:
        out["salary_min"], out["salary_max"] = values[0], values[1]
    elif values:
        out["salary_min"] = values[0]
    return out

def parse_location(raw: str) -> dict:
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

def parse_deadline(raw: str):
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", raw)
    if m:
        try:
            return datetime.strptime(m.group(1).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def parse_posted(raw: str):
    if not raw:
        return None, None
    now  = datetime.now()
    text = raw.lower()
    m = re.search(r"(\d+)\s*(day|days|d|week|weeks|wk|month|months|mo|hour|hours|hr|year|years|yr)", text)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        if unit in ("hour", "hours", "hr"):
            delta = timedelta(hours=n)
        elif unit in ("day", "days", "d"):
            delta = timedelta(days=n)
        elif unit in ("week", "weeks", "wk"):
            delta = timedelta(weeks=n)
        elif unit in ("month", "months", "mo"):
            delta = timedelta(days=n * 30)
        else:
            delta = timedelta(days=n * 365)
        return (now - delta).strftime("%Y-%m-%d"), delta.days
    if any(kw in text for kw in ("just now", "today")):
        return now.strftime("%Y-%m-%d"), 0
    if "yesterday" in text:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d"), 1
    return None, None

SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "selenium", "playwright", "cypress", "appium", "testng", "junit",
    "node", "sql", "postgresql", "mongodb", "aws", "azure", "docker",
    "kubernetes", "git", "ci/cd", "rest", "graphql", "django", "flask",
    "html", "css", "agile", "scrum", "jira", "linux", "bash",
    "qa", "automation", "testing", "machine learning",
]

def extract_skills(text: str) -> str:
    low = text.lower()
    return ", ".join(s for s in SKILLS if s in low)

# ── Driver ────────────────────────────────────────────────────────────────────
CHROME_PROFILE = os.path.expanduser("~/.chrome-handshake-profile")

def init_driver() -> uc.Chrome:
    # Clear Chrome singleton lock files so a fresh session can start even if
    # a previous Chrome instance was killed mid-run.
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = os.path.join(CHROME_PROFILE, lock)
        if os.path.exists(p) or os.path.islink(p):
            try:
                os.remove(p)
            except Exception:
                pass
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    # Use persistent profile — preserves Cloudflare fingerprint + logged-in
    # session so we never have to re-do the Cloudflare challenge.
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    # NOT headless — Cloudflare Turnstile blocks headless browsers
    return uc.Chrome(options=opts, use_subprocess=True)

# ── Browser helpers ───────────────────────────────────────────────────────────
driver: webdriver.Chrome = None   # set in main

def el_exists(xpath, timeout=2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except Exception:
        return False

def fast_click(xpath, timeout=5) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script(_JS_CLICK, el)
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

def safe_texts(xpath, timeout=3) -> list:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return [e.text.strip() for e in driver.find_elements(By.XPATH, xpath) if e.text.strip()]
    except Exception:
        return []

def close_modal():
    for xp in ["//button[@aria-label='Cancel application']", "//button[@aria-label='Close']",
               "//button[normalize-space()='Done']", "//button[normalize-space()='Close']"]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass

def dismiss_post_submit():
    for xp in ["//button[normalize-space()='Done']", "//button[normalize-space()='Close']",
               "//button[@aria-label='Close']"]:
        if el_exists(xp, timeout=3):
            fast_click(xp)
            time.sleep(0.4)
            return

def get_job_id() -> str:
    m = re.search(r"/jobs/(\d+)", driver.current_url)
    return m.group(1) if m else ""

def expand_description():
    for xp in ["//button[contains(@aria-label,'Show more')]",
               "//button[contains(@class,'view-more-button')]",
               "//button[normalize-space()='More']"]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return

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

# ── Job data collector ────────────────────────────────────────────────────────
def collect_job_data(index: int, page: int, apply_type: str = "unknown") -> dict:
    expand_description()
    job_id = get_job_id()
    url    = f"https://app.joinhandshake.com/jobs/{job_id}" if job_id else driver.current_url

    # Title: try stable selectors first, fall back to any h1 on the page
    title = (
        safe_text("//*[contains(@data-hook,'job-title')] | //h1[contains(@class,'job-title')]", timeout=2)
        or safe_text("//h1", timeout=2)
        or safe_text("//h2[contains(translate(@class,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'title')]", timeout=1)
    )
    # Company: data-hook is more stable than obfuscated CSS class names
    company = (
        safe_text("//*[contains(@data-hook,'employer-name')]", timeout=2)
        or safe_text("//*[contains(@data-hook,'company-name')]", timeout=1)
        or safe_text("//a[contains(@href,'/employers/')]", timeout=1)
    )
    industry    = safe_text("//*[contains(@data-hook,'employer-industry')]", timeout=1)
    posted_raw  = safe_text("//*[contains(@data-hook,'posted-date')] | //*[contains(normalize-space(),'Posted')]", timeout=2)
    # Salary/location: use exact data-hook matches (Handshake's obfuscated CSS classes
    # change frequently; data-hook attributes are more stable but still not guaranteed).
    # location_raw left empty if we can't reliably detect it — location_ok() treats
    # empty as "accept" so we don't accidentally reject valid remote jobs.
    salary_raw   = safe_text("//*[@data-hook='salary'] | //*[@data-hook='compensation']", timeout=1)
    location_raw = safe_text("//*[@data-hook='location'] | //*[@data-hook='job-location']", timeout=1)
    job_type     = safe_text("//*[@data-hook='job-type'] | //*[@data-hook='employment-type']", timeout=1)

    work_auth_raw      = safe_text("//*[@data-hook='work-auth-title']", timeout=1)
    work_auth_required = "yes" if "required" in work_auth_raw.lower() else "no" if work_auth_raw else ""
    visa_text          = safe_text(
        "//*[contains(normalize-space(),'visa sponsor') or contains(normalize-space(),'OPT')]", timeout=1
    )
    visa_sponsorship = "yes" if visa_text else "no"

    desc = safe_text(
        "//*[contains(@data-hook,'job-description')] | //div[contains(@style,'overflow-wrap')]", timeout=4
    )
    if len(desc) < 200:
        desc = safe_text("//div[contains(@class,'hkJwbQ')][2]//div", timeout=2)

    deadline_raw = posted_raw if "Apply by" in posted_raw else \
                   safe_text("//*[contains(normalize-space(),'Apply by')]", timeout=1)
    benefits_raw       = " | ".join(safe_texts("//ul[contains(@class,'dpqcEU')]//li"))
    qualifications_raw = " | ".join(safe_texts("//*[contains(@class,'dsAqlh')]"))
    company_size       = safe_text("//*[contains(@class,'jCQffL')][1]", timeout=1)
    company_location   = safe_text("//*[contains(@class,'jCQffL')][2]//p", timeout=1)

    sal  = parse_salary(salary_raw)
    loc  = parse_location(location_raw)
    dl   = parse_deadline(deadline_raw)
    pd, days = parse_posted(posted_raw)
    emp  = ("full-time" if "full" in job_type.lower() else
            "internship" if "intern" in job_type.lower() else
            "part-time" if "part" in job_type.lower() else job_type.lower())

    return {
        "page": page, "index": index,
        "job_id": job_id, "url": url,
        "title": title, "company": company, "industry": industry,
        "location_raw": location_raw, **loc,
        "salary_raw": salary_raw, **sal,
        "job_type": job_type, "employment_type": emp,
        "deadline_raw": deadline_raw, "deadline_date": dl,
        "posted_raw": posted_raw, "posted_date": pd, "days_since_posted": days,
        "work_auth_required": work_auth_required, "visa_sponsorship": visa_sponsorship,
        "description_full": desc[:8000],
        "skills_mentioned": extract_skills(desc),
        "qualifications_raw": qualifications_raw, "benefits_raw": benefits_raw,
        "company_size": company_size, "company_location": company_location,
        "apply_type": apply_type, "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }

# ── Document attachment ───────────────────────────────────────────────────────
def attach_doc(placeholder: str, doc_name: str):
    xp = f"//input[@placeholder='{placeholder}']"
    if not el_exists(xp, timeout=2):
        return
    if el_exists(f"{xp}/ancestor::div[3]//h2", timeout=1):
        return
    try:
        box = driver.find_element(By.XPATH, xp)
        box.click()
        box.send_keys(doc_name[:15])
        time.sleep(1.0)
        opt = f"//*[@role='option'][contains(normalize-space(),'{doc_name[:20]}')]"
        if el_exists(opt, timeout=2):
            fast_click(opt)
    except Exception as e:
        logging.warning(f"    Attach error [{placeholder}]: {e}")

# ── XPaths ────────────────────────────────────────────────────────────────────
ALREADY_APPLIED_XPATH = (
    "//button[contains(normalize-space(),'Withdraw application')] | "
    "//*[contains(normalize-space(),'You already applied')] | "
    "//button[contains(normalize-space(),'View application')]"
)
EXTERNAL_XPATH = (
    "//button[contains(@aria-label,'Apply externally')] | "
    "//button[.//span[normalize-space()='Apply externally']]"
)
APPLY_XPATH   = "//button[@aria-label='Apply'] | //button[.//span[normalize-space()='Apply']]"
SUBMIT_XPATH  = "//button[normalize-space()='Submit Application']"

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    global driver

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    logging.info(f"Run ID: {RUN_ID}  |  {mode}  →  {RUN_DIR}/")

    username = os.getenv("handshake_email")
    password = os.getenv("handshake_password")

    driver = init_driver()

    # ── Session restore via persistent Chrome profile ─────────────────────────
    # The persistent profile keeps the Cloudflare fingerprint + session cookies
    # so we rarely need to log in again. If the session did expire, do a fresh
    # login and it will be persisted for next time.
    def is_logged_in() -> bool:
        return el_exists("//nav | //a[contains(@href,'/jobs')] | //a[contains(@href,'/explore')]", timeout=5)

    def ensure_logged_in():
        driver.get("https://app.joinhandshake.com/explore")
        time.sleep(3)
        if is_logged_in():
            logging.info("Session active (persistent profile).")
            return
        logging.info("Not logged in — doing fresh login.")
        driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
        time.sleep(3)
        driver.save_screenshot(os.path.join(RUN_DIR, "login_page.png"))
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "email-address-identifier"))
        ).send_keys(username)
        fast_click("//button[normalize-space()='Next']")
        time.sleep(1.5)
        fast_click("//a[normalize-space()='Log in another way']")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        ).send_keys(password)
        fast_click("//button[normalize-space()='Log in']")
        time.sleep(5)
        logging.info("Logged in.")

    ensure_logged_in()
    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))

    def process_card(idx, page, n):
        """Open one card, collect data, and apply if eligible. Returns new status."""
        job_data = {"page": page, "index": idx + 1, "apply_type": "unknown",
                    "status": "pending", "timestamp": datetime.now().isoformat()}
        try:
            all_cards = find_cards()
            if idx >= len(all_cards):
                return None

            card = all_cards[idx]
            link = None
            for lxp in [".//a[@role='button']", ".//a[contains(@href,'/jobs/')]", ".//a"]:
                try:
                    link = card.find_element(By.XPATH, lxp)
                    break
                except Exception:
                    pass
            if link is None:
                driver.execute_script(_JS_CLICK, card)
            else:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                driver.execute_script(_JS_CLICK, link)
            time.sleep(random.uniform(0.7, 1.3))

            if el_exists(ALREADY_APPLIED_XPATH, timeout=1):
                apply_type = "easy_apply"
            elif el_exists(EXTERNAL_XPATH, timeout=1):
                apply_type = "external"
            elif el_exists(APPLY_XPATH, timeout=2):
                apply_type = "easy_apply"
            else:
                apply_type = "unknown"

            job_data = collect_job_data(idx + 1, page, apply_type)

            jid = job_data.get("job_id", "")
            if jid and jid in seen_ids:
                logging.info(f"  [{idx+1}/{n}] Duplicate {jid} — skip")
                return None
            if jid:
                seen_ids.add(jid)

            title   = job_data.get("title", "") or "???"
            company = job_data.get("company", "") or "???"
            loc_str = job_data.get("location_raw", "") or "location unknown"
            sal_str = job_data.get("salary_raw", "")
            sal_tag = f"  💰{sal_str[:18]}" if sal_str else ""

            # Determine outcome tag for the log line
            if not title_ok(title):
                outcome = "SKIP:title"
            elif not location_ok(loc_str):
                outcome = f"SKIP:location({loc_str[:20]})"
            elif el_exists(ALREADY_APPLIED_XPATH, timeout=1):
                outcome = "SKIP:already_applied"
            elif apply_type == "external":
                outcome = "SKIP:external"
            elif apply_type != "easy_apply":
                outcome = "SKIP:no_button"
            elif args.dry_run:
                outcome = "DRY_RUN"
            else:
                outcome = f"✓ APPLY ({apply_type})"

            logging.info(
                f"  [{idx+1:02}/{n}] {title[:36]:<36} | {company[:18]:<18} | "
                f"{loc_str[:20]:<20} | {outcome}{sal_tag}"
            )

            # Now execute the outcome
            if not title_ok(title):
                job_data["status"] = "skipped_title"
                record_job(job_data)
                return "skipped_title"

            if not location_ok(loc_str):
                job_data["status"] = "skipped_location"
                record_job(job_data)
                return "skipped_location"

            if el_exists(ALREADY_APPLIED_XPATH, timeout=1):
                job_data["status"] = "skipped_already_applied"
                record_job(job_data)
                return "skipped_already_applied"

            if apply_type == "external":
                job_data["status"] = "skipped_external"
                record_job(job_data)
                return "skipped_external"

            if apply_type != "easy_apply":
                job_data["status"] = "skipped_no_button"
                record_job(job_data)
                return "skipped_no_button"

            if args.dry_run:
                job_data["status"] = "dry_run"
                record_job(job_data)
                return "dry_run"

            fast_click(APPLY_XPATH)
            time.sleep(random.uniform(0.8, 1.4))
            attach_doc("Search your resumes",       RESUME_NAME)
            attach_doc("Search your cover letters", COVER_LETTER_NAME)
            attach_doc("Search your transcripts",   TRANSCRIPT_NAME)
            time.sleep(0.3)

            if not el_exists(SUBMIT_XPATH, timeout=3):
                logging.warning("    No Submit button — closing modal")
                close_modal()
                job_data["status"] = "skipped_no_submit_button"
                record_job(job_data)
                return "skipped_no_submit_button"

            fast_click(SUBMIT_XPATH)
            time.sleep(random.uniform(APPLY_PAUSE_MIN, APPLY_PAUSE_MAX))
            dismiss_post_submit()
            logging.info(f"    ✓ Applied to {title[:40]} @ {company[:25]}")
            job_data["status"] = "applied"
            record_job(job_data)
            return "applied"

        except Exception as e:
            logging.error(f"  Card {idx+1} error: {type(e).__name__}: {e}")
            try:
                close_modal()
            except Exception:
                pass
            job_data["status"] = "error"
            record_job(job_data)
            return "error"

    def run_search(search_kw, search_loc):
        """Type keyword into Handshake search bar and paginate through results."""
        logging.info(f"\n{'='*60}")
        logging.info(f"  SEARCH: {search_kw!r}  |  location filter: {search_loc or 'any (post-filter)'}")
        logging.info(f"{'='*60}")

        # Navigate to base search page and type keyword into the search input
        driver.get("https://app.joinhandshake.com/job-search/")
        time.sleep(random.uniform(2.0, 3.0))

        search_input_xpaths = [
            "//input[@placeholder='Search jobs, companies, or keywords']",
            "//input[contains(@placeholder,'Search jobs')]",
            "//input[contains(@placeholder,'Search')][@type='search']",
            "//input[@type='search']",
            "//input[@name='query']",
        ]
        typed = False
        for xp in search_input_xpaths:
            if el_exists(xp, timeout=3):
                try:
                    box = driver.find_element(By.XPATH, xp)
                    box.clear()
                    box.send_keys(search_kw)
                    box.send_keys(Keys.RETURN)
                    time.sleep(random.uniform(2.5, 3.5))
                    typed = True
                    break
                except Exception:
                    pass
        if not typed:
            logging.warning("  Could not find search input — skipping this keyword.")
            return False

        for page in range(1, TOTAL_PAGES + 1):
            applied_count = Counter(j["status"] for j in all_jobs).get("applied", 0)
            if applied_count >= MAX_APPLIES:
                return True  # cap hit

            logging.info(f"  PAGE {page}/{TOTAL_PAGES}  |  applied so far: {applied_count}")

            if page > 1:
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(0.3)
                next_btn = f"//button[@value='{page}' and not(@aria-current='page')]"
                if not el_exists(next_btn, timeout=4):
                    logging.info("  No next page — moving to next search.")
                    return False
                fast_click(next_btn)
                time.sleep(random.uniform(1.5, 2.5))

            cards = find_cards()
            n = len(cards)
            logging.info(f"  {n} cards on page {page}")

            for idx in range(n):
                # Cap counts both "applied" (live) and "dry_run" so --max-applies
                # limits iterations the same way in both modes.
                processed = Counter(j["status"] for j in all_jobs)
                action_count = processed.get("applied", 0) + processed.get("dry_run", 0)
                if action_count >= MAX_APPLIES:
                    return True  # cap hit
                process_card(idx, page, n)

            _flush(force=True)
            counts = Counter(j["status"] for j in all_jobs)
            logging.info(f"  Page {page} done: {dict(counts)}")
            time.sleep(random.uniform(2.0, 3.0))

        return False

    for search_kw in SEARCH_KEYWORDS:
        processed = Counter(j["status"] for j in all_jobs)
        action_count = processed.get("applied", 0) + processed.get("dry_run", 0)
        if action_count >= MAX_APPLIES:
            logging.info(f"  Session cap ({MAX_APPLIES}) reached — stopping.")
            break
        cap_hit = run_search(search_kw, "")
        if cap_hit:
            logging.info(f"  Session cap ({MAX_APPLIES}) reached — stopping.")
            break

    _flush(force=True)
    try:
        driver.quit()
    except Exception:
        pass

    logging.info("\n" + "=" * 60)
    logging.info("  RUN SUMMARY")
    logging.info("=" * 60)
    counts = Counter(j["status"] for j in all_jobs)
    total   = len(all_jobs)
    applied = counts.get("applied", 0)
    skipped = sum(v for k, v in counts.items() if k.startswith("skipped"))
    errors  = counts.get("error", 0)
    logging.info(f"  Total processed : {total}")
    logging.info(f"  Applied         : {applied}")
    logging.info(f"  Skipped         : {skipped}")
    logging.info(f"  Errors          : {errors}")
    logging.info("")
    logging.info("  Breakdown by status:")
    for status, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt, 20)
        logging.info(f"    {status:<35} {cnt:>4}  {bar}")
    if applied > 0:
        logging.info("")
        logging.info("  Jobs applied to:")
        for j in all_jobs:
            if j.get("status") == "applied":
                logging.info(f"    ✓ {j.get('title','?')[:40]:<40} @ {j.get('company','?')[:25]:<25}  {j.get('location_raw','')[:20]}")

    # ── Sync to Google Sheets ──────────────────────────────────────────────────
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from library.gsheets import sync_jobs
        sync_jobs(all_jobs, platform="Handshake")
        logging.info("  Synced to Google Sheets.")
    except Exception as e:
        logging.warning(f"  Google Sheets sync skipped: {e}")

    logging.info(f"  JSON → {DATA_FILE}")
    logging.info(f"  CSV  → {CSV_FILE}")


if __name__ == "__main__":
    run()
