"""
Handshake Easy Apply — Auto-apply to all Handshake-native jobs (no external redirect).
Logs structured data for every job encountered (applied, skipped, error).

Usage:
  python 033_handshake_applications.py
  python 033_handshake_applications.py --resume runs/handshake_apply_2026-04-01_10-00-00
"""

import argparse
import logging
import random
import time
import json
import os
import re
import csv
import sys
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
from selenium.webdriver.common.keys import Keys
import pyautogui
from dotenv import load_dotenv

# ── CLI args ──────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--resume", metavar="RUN_DIR",
                    help="Resume a previous run (loads existing jobs.json, skips seen IDs)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_PAGES     = 400        # 400 pages × 25 = ~10,000 jobs
AUTO_APPLY      = True       # False = scrape only, logs apply_type but does not submit
SAVE_EVERY      = 5          # flush to disk every N jobs added
APPLY_PAUSE_MIN = 1.2
APPLY_PAUSE_MAX = 2.8

COVER_LETTER_NAME = "HandShake Cover Letter"
TRANSCRIPT_NAME   = "0JH7198571 | SJSU Transcript | Oscar Leung"
RESUME_NAME       = "Oscar Leung Resume"

# ── Run folder ────────────────────────────────────────────────────────────────
if args.resume:
    RUN_DIR = args.resume
    if not os.path.isdir(RUN_DIR):
        raise SystemExit(f"Resume dir not found: {RUN_DIR}")
    RUN_ID = os.path.basename(RUN_DIR)
else:
    RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    RUN_DIR = os.path.join("runs", f"handshake_apply_{RUN_ID}")
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
    "apply_type",   # "easy_apply" | "external" | "unknown"
    "status",       # "applied" | "skipped_*" | "error" | "scraped_only"
    "timestamp",
]

# Load existing jobs when resuming
all_jobs: list[dict] = []
seen_job_ids: set[str] = set()

if args.resume and os.path.exists(DATA_FILE):
    with open(DATA_FILE) as f:
        all_jobs = json.load(f)
    seen_job_ids = {j["job_id"] for j in all_jobs if j.get("job_id")}
    logging.info(f"Resumed: {len(all_jobs)} existing jobs, {len(seen_job_ids)} unique IDs")

logging.info(f"Run ID: {RUN_ID}  →  {RUN_DIR}/")

_unsaved = 0

def save_data(force: bool = False):
    global _unsaved
    if not force and _unsaved < SAVE_EVERY:
        return
    with open(DATA_FILE, "w") as f:
        json.dump(all_jobs, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_jobs)
    _unsaved = 0

def record_job(job_data: dict):
    """Append a job record and increment the unsaved counter."""
    global _unsaved
    all_jobs.append(job_data)
    _unsaved += 1
    save_data()

# ── Parsing ───────────────────────────────────────────────────────────────────

def parse_salary(raw: str) -> dict:
    """Parse salary strings like '$75–90K/yr', '$40-120/hr'. Handles K per-token."""
    out = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return out
    unit_match = re.search(r"/(yr|hr|mo|month|year|hour)", raw, re.I)
    out["salary_unit"] = unit_match.group(1).lower() if unit_match else None
    tokens = re.split(r"[–\-—to]+", raw)
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
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", raw)
    if m:
        try:
            return datetime.strptime(m.group(1).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def parse_posted(raw: str) -> tuple[str | None, int | None]:
    """Convert relative posted strings to ISO date + days count."""
    if not raw:
        return None, None
    now  = datetime.now()
    text = raw.lower()
    m = re.search(
        r"(\d+)\s*(day|days|d|week|weeks|wk|wks|month|months|mo|mos|hour|hours|hr|hrs|year|years|yr|yrs)",
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
        else:
            delta = timedelta(days=n * 365)
        return (now - delta).strftime("%Y-%m-%d"), delta.days
    if any(kw in text for kw in ("just now", "today", "moments ago")):
        return now.strftime("%Y-%m-%d"), 0
    if "yesterday" in text:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d"), 1
    return None, None

COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "vue", "angular",
    "node", "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "git", "ci/cd",
    "rest", "graphql", "grpc", "machine learning", "deep learning", "pytorch",
    "tensorflow", "scikit-learn", "llm", "rag", "langchain", "openai",
    "c++", "c#", "golang", "rust", "swift", "kotlin", "flutter",
    "html", "css", "tailwind", "django", "flask", "fastapi", "spring", "rails",
    "express", "linux", "bash", "agile", "scrum", "jira", "figma",
    "spark", "kafka", "airflow", "selenium", "playwright", "qa", "automation",
]

def extract_skills(text: str) -> str:
    low = text.lower()
    return ", ".join(s for s in COMMON_SKILLS if s in low)

# ── Browser helpers ───────────────────────────────────────────────────────────

def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)
    for _ in range(5):
        pyautogui.hotkey('command', '-')

_JS_CLICK = "arguments[0].click();"

def move_window_to_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i')
    time.sleep(0.2)

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

def element_exists(xpath, timeout=2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
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
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return [e.text.strip() for e in driver.find_elements(By.XPATH, xpath) if e.text.strip()]
    except Exception:
        return []

def close_modal():
    """Close any open modal — try buttons first, then Escape."""
    for xp in [
        "//button[@aria-label='Cancel application']",
        "//button[@aria-label='Close']",
        "//button[normalize-space()='Done']",
        "//button[normalize-space()='Close']",
    ]:
        if element_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass

def dismiss_post_submit_modal():
    """After successful submit, dismiss the Handshake confirmation modal."""
    for xp in [
        "//button[normalize-space()='Done']",
        "//button[normalize-space()='Close']",
        "//button[@aria-label='Close']",
        "//button[contains(normalize-space(),'View application')]",
    ]:
        if element_exists(xp, timeout=3):
            fast_click(xp)
            time.sleep(0.4)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.3)
    except Exception:
        pass

def get_current_job_id() -> str:
    m = re.search(r"/jobs/(\d+)", driver.current_url)
    return m.group(1) if m else ""

def expand_description():
    for xp in [
        "//button[contains(@aria-label,'Show more')]",
        "//button[contains(@class,'view-more-button')]",
        "//button[normalize-space()='More']",
    ]:
        if element_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return

# ── Card detection ────────────────────────────────────────────────────────────

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

    job_id = get_current_job_id()
    url    = f"https://app.joinhandshake.com/jobs/{job_id}" if job_id else driver.current_url

    title       = safe_text("//h1[contains(@class,'job-title')] | //h1[contains(@class,'dmTfkw')]")
    company     = safe_text("//div[contains(@class,'gBthqB')] | //*[contains(@data-hook,'employer-name')]")
    industry    = safe_text("//div[contains(@class,'hrTUzH')] | //*[contains(@data-hook,'employer-industry')]")
    posted_raw  = safe_text("//*[contains(@class,'fsLGJY')] | //*[contains(@data-hook,'posted-date')]")

    salary_raw   = safe_text("//*[contains(@class,'dVnqLS')][1]")
    location_raw = safe_text("//*[contains(@class,'dVnqLS')][2]")
    job_type     = safe_text("//*[contains(@class,'dVnqLS')][3]")

    work_auth_raw      = safe_text("//*[@data-hook='work-auth-title']", timeout=1)
    work_auth_required = "yes" if "required" in work_auth_raw.lower() else "no" if work_auth_raw else ""
    visa_text          = safe_text(
        "//*[contains(normalize-space(),'visa sponsor') or "
        "contains(normalize-space(),'OPT') or contains(normalize-space(),'CPT')]",
        timeout=1,
    )
    visa_sponsorship = "yes" if visa_text else "no"

    desc_full = safe_text(
        "//*[contains(@data-hook,'job-description')] | //div[contains(@style,'overflow-wrap')]",
        timeout=4,
    )
    if len(desc_full) < 200:
        desc_full = safe_text("//div[contains(@class,'hkJwbQ')][2]//div", timeout=2)

    deadline_raw = posted_raw if "Apply by" in posted_raw else \
                   safe_text("//*[contains(normalize-space(),'Apply by')]", timeout=1)

    benefits_raw       = " | ".join(safe_texts("//ul[contains(@class,'dpqcEU')]//li"))
    qualifications_raw = " | ".join(safe_texts("//*[contains(@class,'dsAqlh')]"))
    company_size       = safe_text("//*[contains(@class,'jCQffL')][1]", timeout=1)
    company_location   = safe_text("//*[contains(@class,'jCQffL')][2]//p", timeout=1)

    sal               = parse_salary(salary_raw)
    loc               = parse_location(location_raw)
    dl                = parse_deadline(deadline_raw)
    posted_date, days = parse_posted(posted_raw)

    return {
        "page": page, "index": index,
        "job_id": job_id, "url": url,
        "title": title, "company": company, "industry": industry,
        "location_raw": location_raw, **loc,
        "salary_raw": salary_raw, **sal,
        "job_type": job_type,
        "employment_type": (
            "full-time"  if "full"   in job_type.lower() else
            "internship" if "intern" in job_type.lower() else
            "part-time"  if "part"   in job_type.lower() else
            job_type.lower()
        ),
        "deadline_raw": deadline_raw, "deadline_date": dl,
        "posted_raw": posted_raw, "posted_date": posted_date, "days_since_posted": days,
        "work_auth_required": work_auth_required,
        "visa_sponsorship": visa_sponsorship,
        "description_full": desc_full[:8000],
        "skills_mentioned": extract_skills(desc_full),
        "qualifications_raw": qualifications_raw,
        "benefits_raw": benefits_raw,
        "company_size": company_size,
        "company_location": company_location,
        "apply_type": apply_type,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }

# ── Document attachment ───────────────────────────────────────────────────────

def attach_document(placeholder_text: str, doc_name: str):
    """Type doc name into a search box and pick the first matching dropdown option."""
    search_xpath = f"//input[@placeholder='{placeholder_text}']"
    if not element_exists(search_xpath, timeout=2):
        return
    already = f"//input[@placeholder='{placeholder_text}']/ancestor::div[3]//h2"
    if element_exists(already, timeout=1):
        return
    try:
        box = driver.find_element(By.XPATH, search_xpath)
        box.click()
        box.send_keys(doc_name[:15])
        time.sleep(1.0)
        opt = f"//*[@role='option'][contains(normalize-space(),'{doc_name[:20]}')]"
        if element_exists(opt, timeout=2):
            fast_click(opt)
            logging.info(f"    Attached: {doc_name[:40]}")
        else:
            logging.warning(f"    No match for: {doc_name[:40]}")
    except Exception as e:
        logging.warning(f"    Attach error [{placeholder_text}]: {e}")

# ── Driver + Login ────────────────────────────────────────────────────────────

load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")

opts = webdriver.ChromeOptions()
opts.add_argument("--disable-blink-features=AutomationControlled")
opts.add_experimental_option("excludeSwitches", ["enable-automation"])
opts.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(options=opts)
driver.execute_cdp_cmd(
    "Page.addScriptToEvaluateOnNewDocument",
    {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
)
wait = WebDriverWait(driver, 5)

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

# ── XPath selectors ───────────────────────────────────────────────────────────

ALREADY_APPLIED_XPATH = (
    "//button[contains(normalize-space(),'Withdraw application')] | "
    "//*[contains(normalize-space(),'Application withdrawn')]  | "
    "//*[contains(normalize-space(),'You already applied')]    | "
    "//button[contains(normalize-space(),'View application')]"
)
EXTERNAL_XPATH = (
    "//button[contains(@aria-label,'Apply externally')] | "
    "//button[.//span[normalize-space()='Apply externally']]"
)
APPLY_XPATH = (
    "//button[@aria-label='Apply'] | "
    "//button[.//span[normalize-space()='Apply']]"
)
SUBMIT_XPATH = "//button[normalize-space()='Submit Application']"

# ── Pagination loop ───────────────────────────────────────────────────────────

for page in range(1, TOTAL_PAGES + 1):
    logging.info(f"\n{'='*60}")
    applied_count = Counter(j["status"] for j in all_jobs).get("applied", 0)
    logging.info(f"  PAGE {page}/{TOTAL_PAGES}  |  collected: {len(all_jobs)}  |  applied: {applied_count}")
    logging.info(f"{'='*60}")

    if page > 1:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.3)
        next_btn = f"//button[@value='{page}' and not(@aria-current='page')]"
        if not element_exists(next_btn, timeout=4):
            logging.info(f"No page {page} — done.")
            break
        fast_click(next_btn)
        time.sleep(random.uniform(1.5, 2.5))

    cards = find_cards()
    n = len(cards)
    logging.info(f"  {n} cards on page {page}")

    for idx in range(n):
        job_data = {"page": page, "index": idx + 1, "apply_type": "unknown",
                    "status": "pending", "timestamp": datetime.now().isoformat()}
        try:
            all_cards = find_cards()
            if idx >= len(all_cards):
                logging.warning(f"  Card {idx+1} gone — skipping")
                continue

            card = all_cards[idx]
            link = None
            for lxp in [".//a[@role='button']", ".//a[contains(@href,'/jobs/')]", ".//a"]:
                try:
                    link = card.find_element(By.XPATH, lxp)
                    break
                except Exception:
                    pass
            if link is None:
                driver.execute_script(_JS_CLICK,card)
            else:
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                driver.execute_script(_JS_CLICK,link)
            time.sleep(random.uniform(0.7, 1.3))

            # Determine apply_type before collecting full data (faster skip path)
            if element_exists(ALREADY_APPLIED_XPATH, timeout=1):
                apply_type = "easy_apply"
            elif element_exists(EXTERNAL_XPATH, timeout=1):
                apply_type = "external"
            elif element_exists(APPLY_XPATH, timeout=2):
                apply_type = "easy_apply"
            else:
                apply_type = "unknown"

            job_data = collect_job_data(idx + 1, page, apply_type=apply_type)

            # Dedup by job_id
            jid = job_data.get("job_id", "")
            if jid and jid in seen_job_ids:
                logging.info(f"  [{idx+1}/{n}] Duplicate job {jid} — skipping")
                continue
            if jid:
                seen_job_ids.add(jid)

            logging.info(
                f"  [{idx+1:02}/{n}] {job_data['title'][:40]:<40} | "
                f"{job_data['company'][:22]:<22} | {apply_type:<11} | "
                f"{job_data['location_raw'][:25]}"
            )

            # ── Already applied ──────────────────────────────────────────────
            if element_exists(ALREADY_APPLIED_XPATH, timeout=1):
                logging.info("    Already applied — skip")
                job_data["status"] = "skipped_already_applied"
                record_job(job_data)
                continue

            # ── External apply — skip (only easy-apply jobs get submitted) ──
            if apply_type == "external":
                logging.info("    External apply — skip")
                job_data["status"] = "skipped_external"
                record_job(job_data)
                continue

            # ── No apply button ──────────────────────────────────────────────
            if apply_type != "easy_apply":
                logging.info("    No Apply button — skip")
                job_data["status"] = "skipped_no_button"
                record_job(job_data)
                continue

            if not AUTO_APPLY:
                job_data["status"] = "scraped_only"
                record_job(job_data)
                continue

            # ── Open application modal ───────────────────────────────────────
            fast_click(APPLY_XPATH)
            time.sleep(random.uniform(0.8, 1.4))

            # ── Attach documents ─────────────────────────────────────────────
            attach_document("Search your resumes",       RESUME_NAME)
            attach_document("Search your cover letters", COVER_LETTER_NAME)
            attach_document("Search your transcripts",   TRANSCRIPT_NAME)
            time.sleep(0.3)

            # ── Submit ───────────────────────────────────────────────────────
            if not element_exists(SUBMIT_XPATH, timeout=3):
                logging.warning("    No Submit button — closing modal")
                close_modal()
                job_data["status"] = "skipped_no_submit_button"
                record_job(job_data)
                continue

            fast_click(SUBMIT_XPATH)
            time.sleep(random.uniform(APPLY_PAUSE_MIN, APPLY_PAUSE_MAX))

            dismiss_post_submit_modal()

            logging.info("    Applied!")
            job_data["status"] = "applied"

        except Exception as e:
            logging.error(f"  Card {idx+1} error: {type(e).__name__}: {e}")
            try:
                close_modal()
            except Exception:
                pass
            job_data["status"] = "error"

        record_job(job_data)

    # ── Page checkpoint ──────────────────────────────────────────────────────
    save_data(force=True)
    counts = Counter(j["status"] for j in all_jobs)
    logging.info(f"  Page {page} done: {dict(counts)}")
    time.sleep(random.uniform(2.0, 3.0))

# ── Final ─────────────────────────────────────────────────────────────────────
save_data(force=True)
logging.info("\n" + "=" * 60)
logging.info("DONE")
logging.info(f"Total processed: {len(all_jobs)}")

counts = Counter(j["status"] for j in all_jobs)
for status, n in sorted(counts.items()):
    logging.info(f"  {status:<35} {n:>5}")

# Apply type breakdown
type_counts = Counter(j.get("apply_type", "unknown") for j in all_jobs)
logging.info(f"\nApply types: {dict(type_counts)}")

# Top companies applied to
applied_jobs = [j for j in all_jobs if j.get("status") == "applied"]
if applied_jobs:
    top_cos = Counter(j["company"] for j in applied_jobs if j.get("company")).most_common(10)
    logging.info("\nTop companies applied to:")
    for company, cnt in top_cos:
        logging.info(f"  {company:<35} {cnt:>4}")

# Skills in applied jobs
all_skills: list[str] = []
for j in applied_jobs:
    if j.get("skills_mentioned"):
        all_skills.extend(s.strip() for s in j["skills_mentioned"].split(",") if s.strip())
if all_skills:
    top_skills = Counter(all_skills).most_common(15)
    logging.info("\nTop skills in applied jobs:")
    for skill, cnt in top_skills:
        logging.info(f"  {skill:<20} {cnt:>4}")

# Employment type breakdown
emp_counts = Counter(j.get("employment_type", "unknown") for j in all_jobs)
logging.info(f"\nEmployment types: {dict(emp_counts)}")

logging.info(f"\nJSON → {DATA_FILE}")
logging.info(f"CSV  → {CSV_FILE}")
logging.info(f"Log  → {os.path.join(RUN_DIR, 'run.log')}")

driver.quit()

# ── Sync to Google Sheets ──────────────────────────────────────────────────────
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from library.gsheets import sync_jobs
    sync_jobs(all_jobs, platform="Handshake")
    logging.info("Synced to Google Sheets.")
except Exception as _gs_err:
    logging.warning(f"Google Sheets sync skipped: {_gs_err}")
