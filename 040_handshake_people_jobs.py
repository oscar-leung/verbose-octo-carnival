"""
Handshake People Follow + Email/Job Extraction + Auto-Apply
────────────────────────────────────────────────────────────
1. Follows active people on Handshake who are likely hiring or useful for networking:
     - Recruiters, hiring managers, HR, talent acquisition, engineering leads
     - At tech/software companies in California or remote
2. Extracts emails from people profiles and posts
3. Scrapes job postings from followed companies' job tabs
4. Auto-applies to eligible jobs (Easy Apply only)

Uses the persistent Chrome profile so no login needed after first run.

Usage:
  python 040_handshake_people_jobs.py
  python 040_handshake_people_jobs.py --dry-run
  python 040_handshake_people_jobs.py --skip-people   # jobs/emails only
  python 040_handshake_people_jobs.py --skip-jobs     # people only
  python 040_handshake_people_jobs.py --max-follows 200 --max-applies 20
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
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import Counter

import undetected_chromedriver as uc
from dotenv import load_dotenv
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

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",      action="store_true")
parser.add_argument("--skip-people",  action="store_true", help="Skip people follow step")
parser.add_argument("--skip-jobs",    action="store_true", help="Skip job extraction/apply step")
parser.add_argument("--max-follows",  type=int, default=300, help="Max people to follow")
parser.add_argument("--max-applies",  type=int, default=20,  help="Max job applications")
parser.add_argument("--people-pages", type=int, default=20,  help="Pages of people to scan")
parser.add_argument("--job-pages",    type=int, default=10,  help="Pages of jobs to scan")
args = parser.parse_args()

USERNAME = os.getenv("handshake_email")
PASSWORD = os.getenv("handshake_password")

# ── Run folder ─────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"handshake_people_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log")),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ── Persistent Chrome profile (same fingerprint every run) ─────────────────────
CHROME_PROFILE = os.path.expanduser("~/.chrome-handshake-profile")

# ── Output files ───────────────────────────────────────────────────────────────
EMAILS_FILE  = os.path.join(RUN_DIR, "extracted_emails.txt")
JOBS_FILE    = os.path.join(RUN_DIR, "jobs.csv")
PEOPLE_FILE  = os.path.join(RUN_DIR, "followed_people.csv")

# Master email list (accumulates across runs)
MASTER_DIR         = os.path.join("runs", "handshake_people_MASTER")
MASTER_EMAILS_FILE = os.path.join(MASTER_DIR, "MASTER_EMAILS.txt")
os.makedirs(MASTER_DIR, exist_ok=True)

EMAIL_RE = re.compile(r"\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b", re.I)
EMAIL_BLOCKLIST = {"handshake.com", "joinhandshake.com", "example.com", "sentry.io"}

def load_master_emails() -> set:
    if not os.path.exists(MASTER_EMAILS_FILE):
        return set()
    with open(MASTER_EMAILS_FILE) as f:
        return {l.strip() for l in f if l.strip()}

def save_master_emails(emails: set):
    existing = load_master_emails()
    new = sorted(emails - existing)
    if new:
        with open(MASTER_EMAILS_FILE, "a") as f:
            f.write("\n".join(new) + "\n")
        log.info(f"  {len(new)} new emails → {MASTER_EMAILS_FILE}")
    return new

session_emails: set = set()

def extract_emails_from_text(text: str) -> set:
    found = set()
    for m in EMAIL_RE.finditer(text):
        addr = m.group(0).lower()
        domain = addr.split("@")[-1]
        if domain not in EMAIL_BLOCKLIST:
            found.add(addr)
    return found

# ── People relevance ───────────────────────────────────────────────────────────
# Titles we want to follow — recruiters, hiring managers, engineers at tech cos
GOOD_TITLES = {
    "recruiter", "talent", "hiring", "hr ", "human resources",
    "engineer", "developer", "sdet", "qa", "quality",
    "software", "tech", "data", "product", "engineering manager",
    "cto", "vp of engineering", "director of engineering",
    "technical", "devops", "cloud", "platform",
}

BAD_TITLES = {
    "sales", "marketing", "account executive", "account manager",
    "real estate", "insurance agent", "financial advisor",
}

def person_relevant(title: str, company: str) -> bool:
    low_title   = title.lower()
    low_company = company.lower()
    if any(bad in low_title for bad in BAD_TITLES):
        return False
    # Always follow if recruiter/talent/HR
    if any(kw in low_title for kw in ("recruit", "talent", "hiring", "hr ")):
        return True
    # Follow engineers/tech at companies with tech keywords
    tech_company = any(kw in low_company for kw in (
        "tech", "software", "ai", "cloud", "data", "digital", "systems",
        "labs", "inc", "corp", "llc", "solutions",
    ))
    has_good_title = any(kw in low_title for kw in GOOD_TITLES)
    return has_good_title and tech_company

# ── Job relevance ──────────────────────────────────────────────────────────────
TITLE_EXCLUDE = {
    "senior", " sr ", "sr.", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "intern", "internship",
    "founding", "sales", "field", "hardware", "firmware", "embedded",
}

def job_title_ok(title: str) -> bool:
    low = title.lower()
    return not any(tok in low for tok in TITLE_EXCLUDE)

# ── Data models ────────────────────────────────────────────────────────────────
@dataclass
class Person:
    name:      str
    title:     str
    company:   str
    url:       str
    emails:    str
    status:    str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class Job:
    title:     str
    company:   str
    location:  str
    url:       str
    status:    str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

people_records: list[Person] = []
job_records:    list[Job]    = []

def save_people_csv():
    with open(PEOPLE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(Person.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(asdict(p) for p in people_records)

def save_jobs_csv():
    with open(JOBS_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(Job.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(asdict(j) for j in job_records)

# ── Driver ─────────────────────────────────────────────────────────────────────
def init_driver() -> uc.Chrome:
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    return uc.Chrome(options=opts, use_subprocess=True)

driver: uc.Chrome = None

# ── Browser helpers ────────────────────────────────────────────────────────────
def el_exists(xpath, timeout=3) -> bool:
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

def fast_click(xpath, timeout=5) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False

def human_pause(lo=0.6, hi=1.4):
    time.sleep(random.uniform(lo, hi))

def is_logged_in() -> bool:
    return el_exists("//nav | //a[contains(@href,'/jobs')] | //a[contains(@href,'/explore')]", timeout=5)

def ensure_logged_in():
    driver.get("https://app.joinhandshake.com/explore")
    time.sleep(3)
    if is_logged_in():
        log.info("Session active.")
        return
    log.info("Not logged in — doing fresh login.")
    driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
    time.sleep(3)
    wait = WebDriverWait(driver, 20)
    wait.until(EC.presence_of_element_located((By.ID, "email-address-identifier"))).send_keys(USERNAME)
    fast_click("//button[normalize-space()='Next']")
    time.sleep(1.5)
    fast_click("//a[normalize-space()='Log in another way']")
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(PASSWORD)
    fast_click("//button[normalize-space()='Log in']")
    time.sleep(5)
    log.info("Logged in.")

# ── PHASE 1: Follow people ─────────────────────────────────────────────────────
def run_follow_people():
    log.info("\n" + "="*60)
    log.info("  PHASE 1 — Follow active hiring people")
    log.info("="*60)

    follows = 0
    seen_urls: set[str] = set()

    # Search queries targeting recruiters + hiring engineers
    PEOPLE_SEARCHES = [
        "recruiter software california",
        "talent acquisition tech",
        "hiring manager software engineer",
        "software engineer QA california",
        "SDET recruiter",
        "technical recruiter bay area",
        "engineering recruiter remote",
        "HR tech california",
        "software engineer sacramento",
        "QA engineer hiring",
    ]

    for query in PEOPLE_SEARCHES:
        if follows >= args.max_follows:
            break

        log.info(f"\n  Search: {query!r}")
        # Navigate to network/people search and type query into search box
        driver.get("https://app.joinhandshake.com/stu/user-search")
        time.sleep(random.uniform(2.5, 4.0))

        # Try to type into the search box
        search_input_xp = (
            "//input[@type='search' or @type='text' or contains(@placeholder,'earch') "
            "or contains(@aria-label,'earch')]"
        )
        if el_exists(search_input_xp, timeout=4):
            try:
                inp = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, search_input_xp))
                )
                inp.clear()
                inp.send_keys(query)
                inp.send_keys(Keys.ENTER)
                time.sleep(random.uniform(2.0, 3.0))
            except Exception as e:
                log.warning(f"  Could not type search: {e}")
        else:
            log.warning("  No search input found on people page")

        for page in range(1, args.people_pages + 1):
            if follows >= args.max_follows:
                break

            # Find follow buttons on people cards — try multiple selectors
            btns = driver.find_elements(By.XPATH,
                "//button[@data-testid='follow-user-button'] | "
                "//button[contains(normalize-space(),'Follow') and "
                "not(contains(normalize-space(),'Following')) and "
                "not(contains(normalize-space(),'employer'))]"
            )
            if not btns:
                log.info(f"  No people cards found for {query!r}")
                break

            log.info(f"  Page {page}: {len(btns)} people")

            for btn in btns:
                if follows >= args.max_follows:
                    break
                try:
                    # Get card context
                    card_text = driver.execute_script("""
                        let el = arguments[0];
                        for (let i = 0; i < 8; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            if (el.innerText && el.innerText.split('\\n').filter(s=>s.trim()).length >= 2) return el.innerText;
                        }
                        return '';
                    """, btn)

                    lines = [l.strip() for l in (card_text or "").splitlines() if l.strip()]
                    name    = lines[0] if lines else ""
                    title   = lines[1] if len(lines) > 1 else ""
                    company = lines[2] if len(lines) > 2 else ""

                    # Get profile URL
                    profile_url = driver.execute_script("""
                        let el = arguments[0];
                        for (let i = 0; i < 10; i++) {
                            el = el.parentElement;
                            if (!el) break;
                            let a = el.querySelector('a[href*="/users/"]');
                            if (a) return a.href;
                        }
                        return '';
                    """, btn)

                    if profile_url in seen_urls:
                        continue
                    if profile_url:
                        seen_urls.add(profile_url)

                    already = btn.get_attribute("aria-pressed") == "true"
                    if already or "Following" in (btn.text or ""):
                        people_records.append(Person(
                            name=name, title=title, company=company,
                            url=profile_url, emails="", status="already_following"
                        ))
                        continue

                    if not person_relevant(title, company):
                        people_records.append(Person(
                            name=name, title=title, company=company,
                            url=profile_url, emails="", status="skipped_not_relevant"
                        ))
                        continue

                    log.info(f"    ✓ Following {name} — {title} @ {company}")

                    if not args.dry_run:
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        try:
                            btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", btn)
                        human_pause(0.5, 1.2)

                        # Visit profile to extract email
                        if profile_url:
                            driver.execute_script("window.open(arguments[0], '_blank');", profile_url)
                            driver.switch_to.window(driver.window_handles[-1])
                            time.sleep(2)
                            page_src = driver.page_source
                            emails = extract_emails_from_text(page_src)
                            if emails:
                                session_emails.update(emails)
                                log.info(f"      Emails: {emails}")
                            driver.close()
                            driver.switch_to.window(driver.window_handles[0])
                            time.sleep(0.5)
                        else:
                            emails = set()

                    else:
                        emails = set()

                    status = "dry_run" if args.dry_run else "followed"
                    people_records.append(Person(
                        name=name, title=title, company=company,
                        url=profile_url, emails=", ".join(sorted(emails)),
                        status=status
                    ))
                    follows += 1
                    human_pause(0.4, 0.9)

                except Exception as e:
                    log.error(f"    Person error: {e}")

            # Next page
            next_xp = "//button[contains(@aria-label,'Next') or normalize-space()='Next']"
            if el_exists(next_xp, timeout=3):
                fast_click(next_xp)
                time.sleep(random.uniform(2.0, 3.5))
            else:
                break

        time.sleep(random.uniform(1.5, 3.0))

    save_people_csv()
    log.info(f"\n  People phase done — followed: {follows}")
    return follows

# ── PHASE 2: Scrape jobs + auto-apply ─────────────────────────────────────────
COVER_LETTER_NAME = "HandShake Cover Letter"
TRANSCRIPT_NAME   = "0JH7198571 | SJSU Transcript | Oscar Leung"
RESUME_NAME       = "Oscar Leung Resume"

ALREADY_APPLIED_XPATH = (
    "//button[contains(normalize-space(),'Withdraw application')] | "
    "//*[contains(normalize-space(),'You already applied')] | "
    "//button[contains(normalize-space(),'View application')]"
)
EXTERNAL_XPATH = (
    "//button[contains(@aria-label,'Apply externally')] | "
    "//button[.//span[normalize-space()='Apply externally']]"
)
APPLY_XPATH  = "//button[@aria-label='Apply'] | //button[.//span[normalize-space()='Apply']]"
SUBMIT_XPATH = "//button[normalize-space()='Submit Application']"

def attach_doc(placeholder: str, doc_name: str):
    xp = f"//input[@placeholder='{placeholder}']"
    if not el_exists(xp, timeout=2):
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
        log.warning(f"    Attach error: {e}")

def close_modal():
    for xp in ["//button[@aria-label='Cancel application']", "//button[@aria-label='Close']",
               "//button[normalize-space()='Done']", "//button[normalize-space()='Close']"]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.3)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass

def try_apply_to_job(job_url: str) -> str:
    """Navigate to a Handshake job URL and attempt Easy Apply. Returns status."""
    driver.get(job_url)
    time.sleep(random.uniform(2.0, 3.5))

    title    = safe_text("//h1[contains(@class,'job-title')] | //h1", timeout=5)
    company  = safe_text("//*[contains(@data-hook,'employer-name')] | //h2", timeout=3)
    location = safe_text("//*[contains(@class,'dVnqLS')][2]", timeout=2)

    if not job_title_ok(title):
        log.info(f"    Skip (title): {title}")
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="skipped_title"))
        return "skipped_title"

    if el_exists(ALREADY_APPLIED_XPATH, timeout=2):
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="already_applied"))
        return "already_applied"

    if el_exists(EXTERNAL_XPATH, timeout=2):
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="skipped_external"))
        return "skipped_external"

    if not el_exists(APPLY_XPATH, timeout=3):
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="skipped_no_button"))
        return "skipped_no_button"

    log.info(f"    Applying: {title} @ {company}")

    if args.dry_run:
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="dry_run"))
        return "dry_run"

    fast_click(APPLY_XPATH)
    time.sleep(random.uniform(0.8, 1.4))
    attach_doc("Search your resumes",       RESUME_NAME)
    attach_doc("Search your cover letters", COVER_LETTER_NAME)
    attach_doc("Search your transcripts",   TRANSCRIPT_NAME)
    time.sleep(0.3)

    if not el_exists(SUBMIT_XPATH, timeout=3):
        log.warning("    No Submit button — closing")
        close_modal()
        job_records.append(Job(title=title, company=company, location=location,
                               url=job_url, status="skipped_no_submit"))
        return "skipped_no_submit"

    fast_click(SUBMIT_XPATH)
    time.sleep(random.uniform(1.2, 2.5))
    # Dismiss post-submit modal
    for xp in ["//button[normalize-space()='Done']", "//button[@aria-label='Close']"]:
        if el_exists(xp, timeout=3):
            fast_click(xp)
            break

    log.info(f"    ✓ Applied!")
    job_records.append(Job(title=title, company=company, location=location,
                           url=job_url, status="applied"))
    return "applied"

def run_jobs_and_emails():
    log.info("\n" + "="*60)
    log.info("  PHASE 2 — Scrape jobs + emails from Handshake feed")
    log.info("="*60)

    applies  = 0
    job_urls: set[str] = set()

    # ── A: Scan job search results ─────────────────────────────────────────────
    JOB_KEYWORDS = [
        "QA Automation Engineer",
        "Software Engineer in Test",
        "QA Engineer",
        "SDET",
        "Software Quality Engineer",
        "Software Engineer",
    ]

    for kw in JOB_KEYWORDS:
        if applies >= args.max_applies:
            break

        log.info(f"\n  Job search: {kw!r}")
        driver.get(f"https://app.joinhandshake.com/job-search/?keywords={kw.replace(' ', '+')}")
        time.sleep(random.uniform(2.5, 4.0))

        for page in range(1, args.job_pages + 1):
            if applies >= args.max_applies:
                break

            # Find job cards
            cards = driver.find_elements(By.XPATH,
                "//*[contains(@data-hook,'job-result-card')] | //div[contains(@class,'job-result-card')]"
            )
            if not cards:
                break

            log.info(f"    Page {page}: {len(cards)} jobs")

            for card in cards:
                if applies >= args.max_applies:
                    break
                try:
                    # Get job URL from card — use JS to find any <a href> regardless of path
                    href = driver.execute_script("""
                        let card = arguments[0];
                        // Direct anchor inside card
                        let a = card.querySelector('a[href]');
                        if (a) return a.href;
                        // Card itself or ancestor might be the link
                        let el = card;
                        for (let i = 0; i < 6; i++) {
                            if (!el) break;
                            if (el.tagName === 'A' && el.href) return el.href;
                            el = el.parentElement;
                        }
                        return '';
                    """, card)
                    if not href or href in job_urls:
                        continue
                    # Only follow internal Handshake job links
                    if "joinhandshake.com" not in href and not href.startswith("/"):
                        continue
                    job_urls.add(href)

                    # Extract email from card text (some cards show contact email)
                    card_text = card.text or ""
                    emails = extract_emails_from_text(card_text)
                    session_emails.update(emails)

                    status = try_apply_to_job(href)
                    if status in ("applied", "dry_run"):
                        applies += 1

                    # Go back to results
                    driver.back()
                    time.sleep(random.uniform(1.5, 2.5))

                except Exception as e:
                    log.error(f"    Job card error: {e}")

            # Next page
            next_xp = f"//button[@value='{page + 1}' and not(@aria-current='page')]"
            if el_exists(next_xp, timeout=3):
                fast_click(next_xp)
                time.sleep(random.uniform(2.0, 3.5))
            else:
                break

        time.sleep(random.uniform(1.5, 3.0))

    # ── B: Scan Handshake feed/posts for emails ────────────────────────────────
    log.info("\n  Scanning Handshake feed for emails...")
    driver.get("https://app.joinhandshake.com/feed")
    time.sleep(3)

    for scroll in range(10):
        page_text = driver.page_source
        emails = extract_emails_from_text(page_text)
        session_emails.update(emails)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1.5, 2.5))

    log.info(f"  Feed scan done — {len(session_emails)} emails found so far")

    save_jobs_csv()
    return applies

# ── Main ───────────────────────────────────────────────────────────────────────
def run():
    global driver

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Handshake People + Jobs  |  {mode}")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    ensure_logged_in()
    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))

    total_follows = 0
    total_applies = 0

    if not args.skip_people:
        total_follows = run_follow_people()

    if not args.skip_jobs:
        total_applies = run_jobs_and_emails()

    # ── Save emails ────────────────────────────────────────────────────────────
    new_emails = save_master_emails(session_emails)
    with open(EMAILS_FILE, "w") as f:
        f.write("\n".join(sorted(session_emails)))

    # ── Summary ────────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("DONE")
    log.info(f"  People followed:  {total_follows}")
    log.info(f"  Jobs applied:     {total_applies}")
    log.info(f"  Emails found:     {len(session_emails)} ({len(new_emails)} new)")
    log.info(f"  Emails file:      {EMAILS_FILE}")
    log.info(f"  Master emails:    {MASTER_EMAILS_FILE}")
    log.info(f"  Jobs CSV:         {JOBS_FILE}")
    log.info(f"  People CSV:       {PEOPLE_FILE}")

    people_counts = Counter(p.status for p in people_records)
    job_counts    = Counter(j.status for j in job_records)
    log.info("\n  People breakdown:")
    for s, c in sorted(people_counts.items()):
        log.info(f"    {s:<30} {c:>4}")
    log.info("\n  Job breakdown:")
    for s, c in sorted(job_counts.items()):
        log.info(f"    {s:<30} {c:>4}")

    try:
        driver.quit()
    except Exception:
        pass


if __name__ == "__main__":
    run()
