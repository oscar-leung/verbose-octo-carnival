"""
Glassdoor Easy Apply — Local Script
Applies to QA/SDET/SWE jobs on Glassdoor using the Easy Apply modal.

Uses undetected_chromedriver with a persistent Chrome profile so Cloudflare
doesn't block the session. Run locally with a visible browser.

Usage:
  python 041_glassdoor_apply.py
  python 041_glassdoor_apply.py --dry-run       # scrape only, do not submit
  python 041_glassdoor_apply.py --max-applies 20
  python 041_glassdoor_apply.py --pages 5       # result pages per keyword
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
import sys, os as _os; sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import library.uc_compat  # noqa: F401 — patches distutils for Python 3.12+
import undetected_chromedriver as uc
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
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
parser.add_argument("--dry-run",      action="store_true", help="Scrape only, do not submit")
parser.add_argument("--max-applies",  type=int, default=25, help="Max applications (default 25)")
parser.add_argument("--pages",        type=int, default=5,  help="Result pages per keyword (default 5)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
FULL_NAME    = "Oscar Leung"
EMAIL        = os.getenv("LINKIN_USERNAME", "oscarleung1@gmail.com")
PHONE        = os.getenv("PHONE_NUMBER", "")
RESUME_PATH  = os.getenv("RESUME_PDF_PATH", "")
LINKEDIN_URL = "https://www.linkedin.com/in/oscar-leung/"
GD_EMAIL     = os.getenv("GLASSDOOR_EMAIL") or EMAIL
GD_PASSWORD  = os.getenv("GLASSDOOR_PASSWORD") or os.getenv("LINKIN_PASSWORD", "")

# Target keywords
KEYWORDS = [
    "QA Automation Engineer",
    "SDET",
    "Software Engineer in Test",
    "QA Engineer",
    "Test Automation Engineer",
    "Software Quality Engineer",
    "Software Engineer Python",
    "Software Engineer Java",
    "Backend Engineer",
    "Full Stack Engineer",
]

# Locations — empty = all/remote, others are specific
LOCATIONS = [
    "",               # all / remote
    "Sacramento, CA",
    "San Francisco, CA",
    "San Jose, CA",
]

# Titles to skip
TITLE_EXCLUDE = {
    "senior", " sr ", "sr.", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "intern", "internship",
    "founding", "sales", "field", "hardware", "firmware", "embedded",
    "customer success", "solutions engineer", "forward deployed",
    "business development",
}

def title_ok(title: str) -> bool:
    low = title.lower()
    return not any(tok in low for tok in TITLE_EXCLUDE)

# ── Run folder ────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"glassdoor_apply_{RUN_ID}")
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

JSON_FILE  = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE   = os.path.join(RUN_DIR, "jobs.csv")
GMASS_FILE = os.path.join(RUN_DIR, "gmass_contacts.csv")

# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class GDJob:
    job_id:           str
    title:            str
    company:          str
    location:         str
    keyword:          str
    status:           str
    url:              str = ""
    apply_type:       str = "easy_apply"
    platform:         str = "Glassdoor"
    salary_raw:       str = ""
    salary_min:       Optional[float] = None
    salary_max:       Optional[float] = None
    remote_type:      str = ""
    days_since_posted: Optional[int] = None
    skills_mentioned: str = ""
    contact_email:    str = ""
    description_full: str = ""
    note:             str = ""
    timestamp:        str = field(default_factory=lambda: datetime.now().isoformat())

_records: list[GDJob] = []
_seen_ids: set[str] = set()
_JS_CLICK = "arguments[0].click();"

_EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
_EMAIL_BLOCKLIST = {
    "glassdoor.com", "linkedin.com", "indeed.com",
    "example.com", "sentry.io", "w3.org",
}

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
    if rows:
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(GDJob.__dataclass_fields__.keys()))
            w.writeheader()
            w.writerows(rows)
    gmass = [
        {"Email": r.contact_email, "First Name": "", "Last Name": "",
         "Company": r.company, "Title": r.title, "Job URL": r.url,
         "Location": r.location, "Skills": r.skills_mentioned}
        for r in _records if r.contact_email
    ]
    if gmass:
        with open(GMASS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(gmass[0].keys()))
            w.writeheader()
            w.writerows(gmass)

# ── Skill extraction ──────────────────────────────────────────────────────────
SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "selenium", "playwright", "cypress", "appium", "testng", "junit",
    "node", "sql", "postgresql", "mongodb", "aws", "azure", "docker",
    "kubernetes", "git", "ci/cd", "rest", "graphql", "django", "flask",
    "html", "css", "agile", "scrum", "jira", "linux", "bash",
    "qa", "automation", "testing", "salesforce",
]

def extract_skills(text: str) -> str:
    return ", ".join(s for s in SKILLS if s in text.lower())

# ── Salary ────────────────────────────────────────────────────────────────────
def parse_salary(raw: str) -> dict:
    out: dict = {"salary_min": None, "salary_max": None}
    if not raw:
        return out
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
    elif values:
        out["salary_min"] = values[0]
    return out

# ── Driver ────────────────────────────────────────────────────────────────────
CHROME_PROFILE = os.path.expanduser("~/.chrome-glassdoor-profile")

def init_driver() -> uc.Chrome:
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
    opts.add_argument("--window-size=1440,900")
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    return uc.Chrome(options=opts, use_subprocess=True)

driver: uc.Chrome = None

# ── Browser helpers ───────────────────────────────────────────────────────────
def el_exists(xpath, timeout=2) -> bool:
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
            driver.execute_script(_JS_CLICK, el)
        return True
    except Exception:
        return False

def human_pause(lo=0.5, hi=1.5):
    time.sleep(random.uniform(lo, hi))

def close_modal():
    for xp in [
        "//button[@aria-label='Close']",
        "//button[normalize-space()='Close']",
        "//button[normalize-space()='Cancel']",
        "//button[normalize-space()='Exit']",
    ]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.4)
            return
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.4)
    except Exception:
        pass

# ── Login ─────────────────────────────────────────────────────────────────────
def is_logged_in() -> bool:
    return el_exists(
        "//button[contains(@data-test,'profileMenu')] | "
        "//div[contains(@data-test,'header-menu')] | "
        "//a[contains(@href,'/profile/')]",
        timeout=4
    )

def ensure_logged_in():
    driver.get("https://www.glassdoor.com")
    time.sleep(3)
    if is_logged_in():
        log.info("Session active — already logged in to Glassdoor.")
        return

    log.info("Not logged in — attempting login...")
    driver.get("https://www.glassdoor.com/profile/login_input.htm")
    time.sleep(3)
    driver.save_screenshot(os.path.join(RUN_DIR, "login_page.png"))

    # Email
    for xp in ["//input[@name='username']", "//input[@type='email']", "//input[@id='userEmail']"]:
        if el_exists(xp, timeout=3):
            try:
                el = driver.find_element(By.XPATH, xp)
                el.clear()
                el.send_keys(GD_EMAIL)
                break
            except Exception:
                pass

    # Continue button (Glassdoor uses a two-step flow)
    for xp in [
        "//button[normalize-space()='Continue with Email']",
        "//button[normalize-space()='Continue']",
        "//button[@type='submit']",
    ]:
        if fast_click(xp):
            time.sleep(2)
            break

    # Password
    for xp in ["//input[@name='password']", "//input[@type='password']"]:
        if el_exists(xp, timeout=5):
            try:
                el = driver.find_element(By.XPATH, xp)
                el.clear()
                el.send_keys(GD_PASSWORD)
                break
            except Exception:
                pass

    fast_click("//button[@type='submit'] | //button[normalize-space()='Sign In']")
    time.sleep(4)
    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))

    if not is_logged_in():
        log.warning("Login may have failed — check post_login.png. Continuing anyway.")
    else:
        log.info("Logged in to Glassdoor successfully.")

# ── Job search URL ────────────────────────────────────────────────────────────
def build_search_url(keyword: str, location: str, page: int) -> str:
    kw = quote_plus(keyword)
    loc = quote_plus(location) if location else ""
    # applicationType=1 = Easy Apply only
    base = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={kw}&applicationType=1"
    if loc:
        base += f"&locKeyword={loc}"
    if page > 1:
        base += f"&p={page}"
    return base

# ── Job card selectors ────────────────────────────────────────────────────────
CARD_XPATHS = [
    "//li[contains(@data-test,'jobListing')]",
    "//li[contains(@class,'JobsList_jobListItem')]",
    "//article[contains(@class,'job-listing')]",
    "//li[@data-job-id]",
]

def find_job_cards():
    for xp in CARD_XPATHS:
        cards = driver.find_elements(By.XPATH, xp)
        if cards:
            return cards
    return []

def get_job_meta(card) -> dict:
    job_id = ""
    title = company = location = salary_raw = ""

    # job_id from data attributes
    for attr in ["data-job-id", "data-id", "data-listing-id"]:
        val = card.get_attribute(attr) or ""
        if val:
            job_id = val
            break

    # Try to extract job ID from any link href
    if not job_id:
        try:
            links = card.find_elements(By.XPATH, ".//a[@href]")
            for a in links:
                href = a.get_attribute("href") or ""
                m = re.search(r"jobListingId=(\d+)|_JD(\d+)\b|/job-listing/\D+-(\d+)", href)
                if m:
                    job_id = next(g for g in m.groups() if g)
                    break
        except Exception:
            pass

    # Title
    for xp in [
        ".//a[contains(@data-test,'job-title')]",
        ".//a[contains(@class,'jobTitle')]",
        ".//a[contains(@class,'JobCard_jobTitle')]",
        ".//h2//a",
        ".//h3//a",
    ]:
        try:
            el = card.find_element(By.XPATH, xp)
            title = el.text.strip()
            if not job_id:
                href = el.get_attribute("href") or ""
                m = re.search(r"jobListingId=(\d+)|_JD(\d+)\b", href)
                if m:
                    job_id = next(g for g in m.groups() if g)
            if title:
                break
        except Exception:
            pass

    # Company
    for xp in [
        ".//span[contains(@class,'EmployerProfile')]",
        ".//div[contains(@data-test,'employer-name')]",
        ".//span[contains(@data-test,'employer-name')]",
        ".//a[contains(@class,'employerName')]",
        ".//div[contains(@class,'companyName')]",
        ".//span[contains(@class,'companyName')]",
    ]:
        try:
            company = card.find_element(By.XPATH, xp).text.strip()
            if company:
                break
        except Exception:
            pass

    # Location
    for xp in [
        ".//div[contains(@data-test,'emp-location')]",
        ".//span[contains(@data-test,'job-location')]",
        ".//div[contains(@class,'location')]",
        ".//span[contains(@class,'location')]",
    ]:
        try:
            location = card.find_element(By.XPATH, xp).text.strip()
            if location:
                break
        except Exception:
            pass

    # Salary
    for xp in [
        ".//div[contains(@data-test,'detailSalary')]",
        ".//span[contains(@class,'salary')]",
        ".//div[contains(@class,'salaryEstimate')]",
    ]:
        try:
            salary_raw = card.find_element(By.XPATH, xp).text.strip()
            if salary_raw:
                break
        except Exception:
            pass

    url = ""
    if job_id:
        url = f"https://www.glassdoor.com/job-listing/x-JDIC_{job_id}.htm"

    return {
        "job_id": job_id or "",
        "title": title,
        "company": company,
        "location": location,
        "salary_raw": salary_raw,
        "url": url,
    }

# ── Apply flow ────────────────────────────────────────────────────────────────
EASY_APPLY_BTN = (
    "//button[contains(normalize-space(),'Easy Apply')] | "
    "//button[contains(@data-test,'easyApply')] | "
    "//button[normalize-space()='Apply Now' and not(contains(@class,'external'))]"
)
CONTINUE_BTN = (
    "//button[normalize-space()='Continue'] | "
    "//button[normalize-space()='Next'] | "
    "//button[contains(@class,'continueButton')]"
)
SUBMIT_BTN = (
    "//button[normalize-space()='Submit Application'] | "
    "//button[normalize-space()='Submit'] | "
    "//button[contains(normalize-space(),'Submit your application')] | "
    "//button[contains(@class,'submit') and @type='submit']"
)
SUCCESS_XP = (
    "//*[contains(normalize-space(),'application was submitted')] | "
    "//*[contains(normalize-space(),'successfully applied')] | "
    "//*[contains(normalize-space(),'Application submitted')] | "
    "//*[contains(normalize-space(),'Thank you for applying')]"
)

def fill_apply_form():
    """Fill standard application form fields generically."""
    # Name fields
    for xp, val in [
        ("//input[contains(@name,'firstName') or contains(@id,'firstName') or contains(@placeholder,'First')]", FULL_NAME.split()[0]),
        ("//input[contains(@name,'lastName') or contains(@id,'lastName') or contains(@placeholder,'Last')]", FULL_NAME.split()[-1]),
        ("//input[contains(@type,'email') or contains(@name,'email')]", EMAIL),
    ]:
        if el_exists(xp, timeout=1):
            try:
                el = driver.find_element(By.XPATH, xp)
                if not el.get_attribute("value"):
                    el.clear()
                    el.send_keys(val)
            except Exception:
                pass

    # Phone
    if PHONE:
        for xp in ["//input[@type='tel']", "//input[contains(@name,'phone')]"]:
            if el_exists(xp, timeout=1):
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if not el.get_attribute("value"):
                        el.send_keys(PHONE)
                except Exception:
                    pass

    # Resume upload
    if RESUME_PATH and os.path.isfile(RESUME_PATH):
        for xp in ["//input[@type='file']"]:
            if el_exists(xp, timeout=1):
                try:
                    driver.find_element(By.XPATH, xp).send_keys(RESUME_PATH)
                    time.sleep(2)
                except Exception:
                    pass

    # Radio buttons — default to Yes/first option
    for grp in driver.find_elements(By.XPATH, "//fieldset[.//input[@type='radio']]"):
        try:
            yes_opts = grp.find_elements(By.XPATH, ".//label[contains(translate(normalize-space(.),'YES','yes'),'yes')]")
            if yes_opts:
                driver.execute_script(_JS_CLICK, yes_opts[0])
            else:
                first = grp.find_elements(By.XPATH, ".//input[@type='radio']")
                if first:
                    driver.execute_script(_JS_CLICK, first[0])
        except Exception:
            pass

    # Selects
    for sel_el in driver.find_elements(By.XPATH, "//select"):
        try:
            sel = Select(sel_el)
            if not sel_el.get_attribute("value"):
                try:
                    sel.select_by_visible_text("Yes")
                except Exception:
                    if len(sel.options) > 1:
                        sel.select_by_index(1)
        except Exception:
            pass

def run_easy_apply(keyword: str, meta: dict) -> str:
    """Click Easy Apply and drive the modal. Returns status string."""
    if not el_exists(EASY_APPLY_BTN, timeout=3):
        return "skipped_no_button"

    if args.dry_run:
        return "dry_run"

    fast_click(EASY_APPLY_BTN)
    human_pause(1.0, 2.0)

    # Switch to popup window if opened
    main_window = driver.current_window_handle
    if len(driver.window_handles) > 1:
        for h in driver.window_handles:
            if h != main_window:
                driver.switch_to.window(h)
                break

    for step in range(1, 20):
        try:
            fill_apply_form()
            human_pause(0.5, 1.2)

            if el_exists(SUCCESS_XP, timeout=2):
                log.info(f"    ✓ Applied at step {step}")
                return "applied"

            if el_exists(SUBMIT_BTN, timeout=2):
                fast_click(SUBMIT_BTN)
                human_pause(2.0, 3.5)
                if el_exists(SUCCESS_XP, timeout=5):
                    log.info(f"    ✓ Applied (submit step {step})")
                    return "applied"
                return "applied"  # page transition = assume success

            if el_exists(CONTINUE_BTN, timeout=2):
                fast_click(CONTINUE_BTN)
                human_pause(0.8, 1.5)
                continue

            # Fallback: any primary/submit button
            fallback = driver.find_elements(
                By.XPATH,
                "//button[@type='submit'] | //button[contains(@class,'btn-primary')]"
            )
            if fallback:
                driver.execute_script(_JS_CLICK, fallback[0])
                human_pause(1.5, 2.5)
                if el_exists(SUCCESS_XP, timeout=4):
                    return "applied"
                continue

            log.warning(f"    No advance button at step {step}")
            break

        except Exception as e:
            log.error(f"    Modal error step {step}: {e}")
            break

    # Switch back to main window if we're in a popup
    try:
        if driver.current_window_handle != main_window and main_window in driver.window_handles:
            driver.switch_to.window(main_window)
    except Exception:
        pass

    close_modal()
    return "error"

# ── Job description ───────────────────────────────────────────────────────────
def get_description() -> str:
    for xp in [
        "//div[contains(@class,'JobDetails_jobDescription')]",
        "//div[contains(@data-test,'job-description')]",
        "//div[contains(@class,'desc')][@id]",
        "//div[@id='JobDescriptionContainer']",
    ]:
        try:
            el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
            return el.text.strip()
        except Exception:
            pass
    return ""

# ── Close job signup modal ────────────────────────────────────────────────────
def dismiss_popups():
    """Close login/signup modals that Glassdoor aggressively shows."""
    for xp in [
        "//button[@aria-label='Close']",
        "//button[normalize-space()='Close']",
        "//span[@aria-label='Close']",
        "//button[contains(@class,'modal_closeIcon')]",
        "//button[contains(@data-test,'x-btn')]",
    ]:
        if el_exists(xp, timeout=1):
            fast_click(xp)
            time.sleep(0.5)
            return

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    global driver

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Glassdoor Easy Apply  |  {len(KEYWORDS)} keywords  |  {mode}")
    log.info(f"  Max applies: {args.max_applies}  |  Pages/keyword: {args.pages}")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    ensure_logged_in()
    driver.save_screenshot(os.path.join(RUN_DIR, "session_start.png"))

    counts: Counter = Counter()

    for location in LOCATIONS:
        for keyword in KEYWORDS:
            applied = counts.get("applied", 0) + counts.get("dry_run", 0)
            if applied >= args.max_applies:
                break

            loc_tag = f" [{location}]" if location else " [any/remote]"
            log.info(f"\n{'='*60}")
            log.info(f"  SEARCH: {keyword!r}{loc_tag}")
            log.info(f"{'='*60}")

            for page in range(1, args.pages + 1):
                applied = counts.get("applied", 0) + counts.get("dry_run", 0)
                if applied >= args.max_applies:
                    break

                url = build_search_url(keyword, location, page)
                log.info(f"  Page {page}/{args.pages}  →  {url[:80]}")
                driver.get(url)
                human_pause(3.0, 5.0)
                dismiss_popups()

                driver.save_screenshot(os.path.join(RUN_DIR, f"search_{keyword[:15].replace(' ','_')}_p{page}.png"))

                cards = find_job_cards()
                if not cards:
                    # Try scrolling to trigger lazy-load
                    driver.execute_script("window.scrollTo(0, 500);")
                    time.sleep(2)
                    dismiss_popups()
                    cards = find_job_cards()

                if not cards:
                    log.info(f"  No cards on page {page} — stopping this search.")
                    break

                log.info(f"  {len(cards)} job cards")

                for idx, card in enumerate(cards):
                    applied = counts.get("applied", 0) + counts.get("dry_run", 0)
                    if applied >= args.max_applies:
                        break

                    try:
                        meta = get_job_meta(card)
                        job_id = meta["job_id"]

                        if not meta["title"]:
                            continue
                        if job_id and job_id in _seen_ids:
                            continue
                        if job_id:
                            _seen_ids.add(job_id)

                        title    = meta["title"]
                        company  = meta["company"] or "?"
                        location_str = meta["location"] or "?"

                        if not title_ok(title):
                            log.info(f"  [{idx+1:02}/{len(cards)}] SKIP:title  {title[:42]}")
                            counts["skipped_title"] += 1
                            _records.append(GDJob(
                                job_id=job_id, title=title, company=company,
                                location=location_str, keyword=keyword, status="skipped_title",
                                url=meta["url"],
                            ))
                            continue

                        log.info(
                            f"  [{idx+1:02}/{len(cards)}] {title[:38]:<38} | "
                            f"{company[:18]:<18} | {location_str[:20]}"
                        )

                        # Click card to open detail panel
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                        try:
                            card.click()
                        except Exception:
                            driver.execute_script(_JS_CLICK, card)
                        human_pause(1.5, 2.5)
                        dismiss_popups()

                        desc  = get_description()
                        email = extract_email(desc)
                        sal   = parse_salary(meta["salary_raw"])
                        remote_type = (
                            "hybrid" if "hybrid" in (location_str + desc).lower() else
                            "remote" if "remote" in (location_str + desc).lower() else "onsite"
                        )

                        if email:
                            log.info(f"    Found email: {email}")

                        status = run_easy_apply(keyword, meta)
                        counts[status] += 1

                        _records.append(GDJob(
                            job_id=job_id,
                            title=title,
                            company=company,
                            location=location_str,
                            keyword=keyword,
                            status=status,
                            url=meta["url"],
                            salary_raw=meta["salary_raw"],
                            salary_min=sal["salary_min"],
                            salary_max=sal["salary_max"],
                            remote_type=remote_type,
                            skills_mentioned=extract_skills(desc),
                            contact_email=email,
                            description_full=desc[:6000],
                        ))

                        log.info(f"    → {status}")
                        save_all()

                        if status == "applied":
                            human_pause(8.0, 15.0)
                        else:
                            human_pause(1.5, 3.0)

                    except StaleElementReferenceException:
                        log.warning(f"  [{idx+1}] Stale element — skip")
                    except Exception as e:
                        log.error(f"  [{idx+1}] Error: {e}")
                        counts["error"] += 1
                        close_modal()

                human_pause(2.0, 4.0)

    save_all()

    try:
        driver.quit()
    except Exception:
        pass

    # ── Summary ────────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("  RUN SUMMARY  —  Glassdoor Easy Apply")
    log.info("=" * 60)
    total = sum(counts.values())
    log.info(f"  Total processed : {total}")
    for status, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(cnt, 20)
        log.info(f"  {status:<35} {cnt:>4}  {bar}")
    applied_jobs = [r for r in _records if r.status == "applied"]
    if applied_jobs:
        log.info("")
        log.info("  Jobs applied to:")
        for r in applied_jobs:
            log.info(f"    ✓ {r.title[:40]:<40} @ {r.company[:25]:<25}  {r.location[:20]}")

    # ── Google Sheets sync ────────────────────────────────────────────────────
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from library.gsheets import sync_jobs
        sync_jobs([asdict(r) for r in _records], platform="Glassdoor")
        log.info("  Synced to Google Sheets.")
    except Exception as e:
        log.warning(f"  Google Sheets sync skipped: {e}")

    log.info(f"  JSON → {JSON_FILE}")
    log.info(f"  CSV  → {CSV_FILE}")
    log.info(f"  Run  → {RUN_DIR}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
