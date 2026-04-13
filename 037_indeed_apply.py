"""
Indeed Easy Apply — Local Script (NOT PythonAnywhere)
Searches for QA/SDET/SWE jobs on Indeed and auto-applies via Indeed's Easy Apply flow.

Run locally with a visible browser (Indeed is aggressive about detecting headless automation).

Usage:
  python 037_indeed_apply.py
  python 037_indeed_apply.py --dry-run    # scrape only, do not submit
  python 037_indeed_apply.py --pages 5    # how many result pages per keyword
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
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

load_dotenv()

# ── CLI ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--pages", type=int, default=5, help="Result pages per keyword")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME  = os.getenv("INDEED_EMAIL") or os.getenv("LINKIN_USERNAME")
PASSWORD  = os.getenv("INDEED_PASSWORD") or os.getenv("LINKIN_PASSWORD")
FULL_NAME = "Oscar Leung"
PHONE     = os.getenv("PHONE_NUMBER", "")     # add PHONE_NUMBER=<your number> to .env
RESUME_PATH = os.getenv("RESUME_PDF_PATH", "") # absolute path to your resume PDF

KEYWORDS = [
    # QA / Automation
    "QA Engineer",
    "SDET",
    "Software Engineer in Test",
    "Automation Engineer",
    "Test Automation",
    "QA Automation",
    # Software Engineering
    "Software Engineer Python",
    "Software Engineer Java",
    "Backend Engineer",
    "Full Stack Engineer",
    "Software Developer",
]
# Search multiple locations — Remote + Sacramento area + Davis
LOCATIONS = ["Remote", "Sacramento, CA", "Davis, CA"]
LOCATION       = "Remote"  # kept for legacy search_url() calls; loop overrides this
EASY_APPLY_FILTER = True    # &iafilter=1 adds "Easily Apply" filter on Indeed
RESULTS_PER_PAGE  = 15      # Indeed shows 15 results per page
WAIT_SEC          = 10
MODAL_MAX_STEPS   = 15

# ── Run folder ────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"indeed_apply_{RUN_ID}")
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

JSON_FILE   = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE    = os.path.join(RUN_DIR, "jobs.csv")
GMASS_FILE  = os.path.join(RUN_DIR, "gmass_contacts.csv")

# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class IndeedJob:
    job_id:           str
    title:            str
    company:          str
    location:         str
    keyword:          str
    status:           str     # applied | skipped | error | dry_run
    url:              str = ""
    apply_type:       str = "easy_apply"
    platform:         str = "Indeed"
    salary_raw:       str = ""
    salary_min:       Optional[float] = None
    salary_max:       Optional[float] = None
    salary_unit:      str = ""
    remote_type:      str = ""
    employment_type:  str = ""
    days_since_posted: Optional[int] = None
    skills_mentioned: str = ""
    contact_email:    str = ""
    description_full: str = ""
    note:             str = ""
    timestamp:        str = field(default_factory=lambda: datetime.now().isoformat())

_records: list[IndeedJob] = []
_seen_ids: set[str] = set()

_JS_CLICK = "arguments[0].click();"

_EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
_EMAIL_BLOCKLIST = {"indeed.com", "linkedin.com", "example.com", "sentry.io", "w3.org", "schema.org"}

def extract_email(text: str) -> str:
    for m in _EMAIL_RE.finditer(text):
        addr = m.group(0).lower()
        domain = addr.split("@")[-1]
        if domain not in _EMAIL_BLOCKLIST:
            return addr
    return ""

def save_all():
    rows = [asdict(r) for r in _records]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(IndeedJob.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(rows)
    gmass_rows = [
        {"Email": r.contact_email, "First Name": "", "Last Name": "",
         "Company": r.company, "Title": r.title, "Job URL": r.url,
         "Location": r.location, "Skills": r.skills_mentioned}
        for r in _records if r.contact_email
    ]
    if gmass_rows:
        with open(GMASS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(gmass_rows[0].keys()))
            w.writeheader()
            w.writerows(gmass_rows)
        log.info(f"  GMass contacts: {len(gmass_rows)} emails → {GMASS_FILE}")
    else:
        log.info("  GMass contacts: no emails found this run")

# ── Parsing ───────────────────────────────────────────────────────────────────
def parse_salary(raw: str) -> dict:
    out = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return out
    m = re.search(r"/(yr|hr|mo|year|hour|month|a year|an hour)", raw, re.I)
    out["salary_unit"] = "yr" if "year" in (m.group(1) if m else "").lower() else \
                         "hr" if "hour" in (m.group(1) if m else "").lower() else \
                         (m.group(1).lower() if m else None)
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

def parse_location(raw: str) -> str:
    low = raw.lower()
    if "remote" in low and ("hybrid" in low or "in-person" in low):
        return "hybrid"
    if "remote" in low:
        return "remote"
    return "onsite"

def parse_days_posted(raw: str) -> Optional[int]:
    if not raw:
        return None
    if "just posted" in raw.lower() or "today" in raw.lower():
        return 0
    m = re.search(r"(\d+)\s*day", raw.lower())
    if m:
        return int(m.group(1))
    if "30+" in raw:
        return 30
    return None

SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "selenium", "playwright", "cypress", "appium", "testng", "junit",
    "node", "sql", "postgresql", "mongodb", "aws", "azure", "docker",
    "kubernetes", "git", "ci/cd", "rest", "graphql", "django", "flask",
    "html", "css", "agile", "scrum", "jira", "linux", "bash",
    "qa", "automation", "testing",
]

def extract_skills(text: str) -> str:
    return ", ".join(s for s in SKILLS if s in text.lower())

# ── Driver ────────────────────────────────────────────────────────────────────
def init_driver() -> webdriver.Chrome:
    """Non-headless — Indeed detects headless and shows CAPTCHA."""
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return driver

# ── Helpers ───────────────────────────────────────────────────────────────────
def el_exists(driver, xpath, timeout=2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except Exception:
        return False

def safe_click(driver, wait, xpath, timeout=5) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script(_JS_CLICK, el)
        time.sleep(random.uniform(0.3, 0.7))
        return True
    except Exception:
        return False

def safe_text(driver, xpath, timeout=3) -> str:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        ).text.strip()
    except Exception:
        return ""

def human_wait(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))

def dismiss_modal(driver, wait):
    for xp in [
        "//button[@aria-label='Close']",
        "//button[normalize-space()='Close']",
        "//button[normalize-space()='Cancel']",
        "//div[@id='indeedApplyButtonContainer']//button[contains(@class,'close')]",
    ]:
        if el_exists(driver, xp, timeout=1):
            safe_click(driver, wait, xp)
            time.sleep(0.5)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.5)
    except Exception:
        pass

# ── Search URL builder ────────────────────────────────────────────────────────
def search_url(keyword: str, start: int) -> str:
    kw  = quote_plus(keyword)
    loc = quote_plus(LOCATION)
    url = f"https://www.indeed.com/jobs?q={kw}&l={loc}&start={start}"
    if EASY_APPLY_FILTER:
        url += "&iafilter=1"   # "Easily Apply" filter
    return url

# ── Job metadata ──────────────────────────────────────────────────────────────
def get_job_meta(driver, card_el) -> dict:
    """Extract metadata from an Indeed job card."""
    job_id = card_el.get_attribute("data-jk") or ""
    title = company = location = salary_raw = posted_raw = ""
    try:
        title = card_el.find_element(
            By.XPATH, ".//h2[contains(@class,'jobTitle')]//span"
        ).text.strip()
    except Exception:
        pass
    try:
        company = card_el.find_element(
            By.XPATH, ".//span[@data-testid='company-name']"
        ).text.strip()
    except Exception:
        pass
    try:
        location = card_el.find_element(
            By.XPATH, ".//div[@data-testid='text-location']"
        ).text.strip()
    except Exception:
        pass
    try:
        salary_raw = card_el.find_element(
            By.XPATH, ".//div[contains(@class,'salary-snippet')]"
        ).text.strip()
    except Exception:
        pass
    try:
        posted_raw = card_el.find_element(
            By.XPATH, ".//span[@data-testid='myJobsStateDate']"
        ).text.strip()
    except Exception:
        pass
    url = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else ""
    return {
        "job_id": job_id, "title": title, "company": company,
        "location": location, "salary_raw": salary_raw,
        "posted_raw": posted_raw, "url": url,
    }

def get_job_description(driver) -> str:
    for xp in [
        "//div[@id='jobDescriptionText']",
        "//div[contains(@class,'jobsearch-JobComponent-description')]",
        "//div[contains(@class,'job-description')]",
    ]:
        try:
            el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
            return el.text.strip()
        except Exception:
            pass
    return ""

# ── Indeed Easy Apply modal ───────────────────────────────────────────────────
#
# Indeed's modal flow typically has these steps:
#   1. Resume upload / confirm resume
#   2. Contact info (name, phone)
#   3. Qualifications / screening questions
#   4. Review & Submit
#
# The "Apply now" / "Easily apply" button opens an inline modal on the right panel.

INDEED_APPLY_BTN = (
    "//button[contains(@class,'ia-IndeedApplyButton')] | "
    "//button[@id='indeedApplyButton'] | "
    "//span[normalize-space()='Apply now']/parent::button"
)
INDEED_CONTINUE_BTN = (
    "//button[@id='form-action-continue'] | "
    "//button[normalize-space()='Continue'] | "
    "//button[contains(@class,'ia-continueButton')]"
)
INDEED_SUBMIT_BTN = (
    "//button[@id='form-action-submit'] | "
    "//button[normalize-space()='Submit your application'] | "
    "//button[contains(@class,'ia-ReviewedApplication-footer-button')]"
)

def fill_indeed_contact(driver, wait):
    """Fill contact info if shown."""
    # Phone number
    for xp in ["//input[@id='input-phoneNumber']", "//input[@name='phoneNumber']"]:
        if el_exists(driver, xp, timeout=1):
            try:
                el = driver.find_element(By.XPATH, xp)
                if not el.get_attribute("value"):
                    el.clear()
                    el.send_keys(PHONE)
            except Exception:
                pass
            break

def fill_indeed_questions(driver, wait):
    """Fill Yes/No and numeric screening questions generically."""
    # Radio button questions — try "Yes" for positive questions
    for radio_grp in driver.find_elements(By.XPATH, "//fieldset[.//input[@type='radio']]"):
        try:
            # Prefer Yes
            yes = radio_grp.find_elements(By.XPATH, ".//label[normalize-space()='Yes']")
            if yes:
                driver.execute_script(_JS_CLICK, yes[0])
                continue
            # Otherwise pick first option
            first = radio_grp.find_elements(By.XPATH, ".//input[@type='radio']")
            if first:
                driver.execute_script(_JS_CLICK, first[0])
        except Exception:
            pass
    # Select dropdowns
    for sel_el in driver.find_elements(By.XPATH, "//select"):
        try:
            sel = Select(sel_el)
            # Try "Yes" first
            try:
                sel.select_by_visible_text("Yes")
            except Exception:
                if len(sel.options) > 1:
                    sel.select_by_index(1)
        except Exception:
            pass
    # Text inputs — fill numeric ones with "1"
    for inp in driver.find_elements(By.XPATH, "//input[@type='text' or @type='number']"):
        try:
            if not inp.get_attribute("value"):
                inp.send_keys("1")
        except Exception:
            pass

def advance_indeed_modal(driver, wait) -> bool:
    """
    Detect current modal page, fill it, and advance.
    Returns True when application is submitted.
    """
    # Fill contact info if on that step
    fill_indeed_contact(driver, wait)

    # Fill screening / qualification questions
    fill_indeed_questions(driver, wait)

    # Submit?
    if el_exists(driver, INDEED_SUBMIT_BTN):
        safe_click(driver, wait, INDEED_SUBMIT_BTN)
        human_wait(1.5, 2.5)
        return True

    # Continue to next step
    if el_exists(driver, INDEED_CONTINUE_BTN):
        safe_click(driver, wait, INDEED_CONTINUE_BTN)
        human_wait(0.5, 1.2)
        return False

    raise RuntimeError("No Continue or Submit button found in Indeed modal")

def run_indeed_apply(driver, wait) -> str:
    """Click Apply and drive the full modal. Returns status string."""
    if not el_exists(driver, INDEED_APPLY_BTN, timeout=3):
        return "skipped"

    # Check if it's Easy Apply (not external redirect)
    apply_btn = driver.find_elements(By.XPATH, INDEED_APPLY_BTN)
    if not apply_btn:
        return "skipped"

    # Some jobs have "Apply on company site" — detect that
    btn_text = apply_btn[0].text.strip().lower()
    if "company site" in btn_text or "external" in btn_text:
        return "skipped_external"

    safe_click(driver, wait, INDEED_APPLY_BTN)
    human_wait(1.0, 2.0)

    if args.dry_run:
        dismiss_modal(driver, wait)
        return "dry_run"

    for step in range(1, MODAL_MAX_STEPS + 1):
        try:
            submitted = advance_indeed_modal(driver, wait)
            if submitted:
                log.info(f"    Applied (step {step})")
                return "applied"
            human_wait(0.5, 1.5)
        except RuntimeError as e:
            log.warning(f"    Stuck at step {step}: {e}")
            dismiss_modal(driver, wait)
            return "error"
        except Exception as e:
            log.error(f"    Modal error at step {step}: {e}")
            dismiss_modal(driver, wait)
            return "error"

    log.warning(f"    Exceeded {MODAL_MAX_STEPS} steps")
    dismiss_modal(driver, wait)
    return "error"

# ── Login ─────────────────────────────────────────────────────────────────────
def login(driver, wait):
    """
    Indeed uses Google OAuth — automated login is blocked.
    This function navigates to Indeed and pauses for up to 60 seconds so you
    can complete login manually in the browser window that pops up.
    On subsequent runs the browser session/cookies are already active.
    """
    driver.get("https://www.indeed.com")
    time.sleep(3)

    # Already logged in (session cookie active)?
    if el_exists(driver, "//a[contains(@href,'resume')]", timeout=3):
        log.info("Already logged in to Indeed.")
        driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))
        return

    log.info("=" * 60)
    log.info("  ACTION REQUIRED: Log in to Indeed in the browser window.")
    log.info("  You have 60 seconds. Script resumes automatically.")
    log.info("=" * 60)
    # Open login page and wait for user
    driver.get("https://secure.indeed.com/account/login")
    for _ in range(60):
        time.sleep(1)
        if "indeed.com" in driver.current_url and "login" not in driver.current_url:
            break
    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))
    log.info(f"Post-login URL: {driver.current_url}")

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Indeed Easy Apply  |  {len(KEYWORDS)} keywords × {args.pages} pages  |  {mode}")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    wait   = WebDriverWait(driver, WAIT_SEC)
    counts: dict[str, int] = {}

    try:
        login(driver, wait)

        for keyword in KEYWORDS:
            log.info(f"\n{'─'*60}")
            log.info(f"  Keyword: {keyword}")
            log.info(f"{'─'*60}")

            for page_num in range(args.pages):
                start = page_num * RESULTS_PER_PAGE
                url   = search_url(keyword, start)
                log.info(f"  Page {page_num+1}  (start={start})")

                driver.get(url)
                human_wait(2.0, 3.5)

                # Wait for job cards — Indeed uses li[@data-jk] or div[@data-jk]
                CARD_XPATHS = [
                    "//li[@data-jk]",
                    "//div[@data-jk]",
                    "//div[contains(@class,'job_seen_beacon')]",
                    "//div[contains(@class,'resultContent')]",
                ]
                cards = []
                found_cards = False
                for card_xp in CARD_XPATHS:
                    try:
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, card_xp))
                        )
                        cards = driver.find_elements(By.XPATH, card_xp)
                        if cards:
                            found_cards = True
                            log.info(f"  Cards via: {card_xp}")
                            break
                    except TimeoutException:
                        continue

                if not found_cards:
                    log.info(f"  Page {page_num+1}: no jobs — next keyword.")
                    # Screenshot for debugging
                    driver.save_screenshot(os.path.join(RUN_DIR, f"no_jobs_{keyword.replace(' ','_')}_p{page_num+1}.png"))
                    break

                log.info(f"  {len(cards)} cards")

                for idx, card in enumerate(cards):
                    try:
                        meta   = get_job_meta(driver, card)
                        job_id = meta["job_id"]

                        if not job_id or job_id in _seen_ids:
                            continue
                        _seen_ids.add(job_id)

                        log.info(f"  [{idx+1}/{len(cards)}] {meta['title']} @ {meta['company']}")

                        # Click card to load detail panel
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                        try:
                            card.click()
                        except Exception:
                            driver.execute_script(_JS_CLICK, card)
                        human_wait(1.2, 2.5)

                        desc = get_job_description(driver)
                        sal  = parse_salary(meta["salary_raw"])
                        remote_type = parse_location(meta["location"])
                        days        = parse_days_posted(meta["posted_raw"])
                        contact_email = extract_email(desc)
                        if contact_email:
                            log.info(f"    Found email: {contact_email}")

                        status = run_indeed_apply(driver, wait)
                        counts[status] = counts.get(status, 0) + 1

                        _records.append(IndeedJob(
                            job_id=job_id,
                            title=meta["title"],
                            company=meta["company"],
                            location=meta["location"],
                            keyword=keyword,
                            status=status,
                            url=meta["url"],
                            salary_raw=meta["salary_raw"],
                            salary_min=sal["salary_min"],
                            salary_max=sal["salary_max"],
                            salary_unit=sal["salary_unit"] or "",
                            remote_type=remote_type,
                            days_since_posted=days,
                            skills_mentioned=extract_skills(desc),
                            contact_email=contact_email,
                            description_full=desc[:5000],
                        ))
                        human_wait(0.8, 1.8)

                    except StaleElementReferenceException:
                        log.warning(f"  [{idx+1}] Stale element")
                    except Exception as e:
                        log.error(f"  [{idx+1}] Error: {e}")
                        counts["error"] = counts.get("error", 0) + 1
                        dismiss_modal(driver, wait)

                save_all()
                human_wait(1.5, 3.0)

    except Exception as e:
        log.error(f"Fatal: {e}")
    finally:
        save_all()
        try:
            driver.quit()
        except Exception:
            pass

    log.info("=" * 60)
    log.info(f"  DONE  |  {dict(counts)}")
    log.info(f"  Total unique jobs seen: {len(_seen_ids)}")

    # ── Sync to Google Sheets ──────────────────────────────────────────────────
    try:
        sys.path.insert(0, os.path.dirname(__file__))
        from library.gsheets import sync_jobs
        sync_jobs([asdict(r) for r in _records], platform="Indeed")
        log.info("  Synced to Google Sheets.")
    except Exception as e:
        log.warning(f"  Google Sheets sync skipped: {e}")

    log.info(f"  JSON → {JSON_FILE}")
    log.info(f"  CSV  → {CSV_FILE}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
