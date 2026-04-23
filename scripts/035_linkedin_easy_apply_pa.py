"""
LinkedIn Easy Apply — PythonAnywhere Edition
Headless Chrome, no pyautogui. Designed to run as a PythonAnywhere scheduled task.

Targets Oscar's background: QA Engineer / SDET / Software Engineer
  - Selenium, Python, Java, JavaScript, React, CI/CD, TestNG, Appium

PythonAnywhere setup:
  1. Upload this file + library/gsheets.py + .env to PythonAnywhere
  2. Install: pip install selenium python-dotenv gspread google-auth
  3. Download chromedriver matching your PythonAnywhere chromium version:
       chromium-browser --version
       https://chromedriver.chromium.org/downloads
  4. Dashboard → Tasks → Add a new task (daily at 8:00 AM):
       python /home/<username>/verbose-octo-carnival/035_linkedin_easy_apply_pa.py
  5. Check runs/linkedin_easy_apply_pa_*/run.log for results

Note: LinkedIn may occasionally require CAPTCHA. If the script fails to log in,
      use a session cookie approach instead (save cookies after manual login).

Usage (local):
  python 035_linkedin_easy_apply_pa.py
  python 035_linkedin_easy_apply_pa.py --dry-run    # scrape only, do not submit
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

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSessionIdException,
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
parser.add_argument("--dry-run", action="store_true", help="Scrape only, do not submit")
parser.add_argument("--max-applies", type=int, default=None, help="Override MAX_APPLIES_PER_SESSION")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
USERNAME      = os.getenv("LINKIN_USERNAME")
PASSWORD      = os.getenv("LINKIN_PASSWORD")
FULL_NAME     = "Oscar Leung"
LINKEDIN_URL  = "https://www.linkedin.com/in/oscar-leung/"
HOME_CITY     = "Santa Clara"

# ── Keywords matched to Oscar's resume ───────────────────────────────────────
# Target: QA/SDET/Automation roles using Selenium, Python, Java, Salesforce,
# pytest, Espresso, React — based on actual work history at Maxar + State of IL
KEYWORDS = [
    # QA / Automation
    "QA Automation Engineer",
    "SDET",
    "Software Engineer in Test",
    "QA Engineer Selenium",
    "Test Automation Engineer Python",
    "Software Quality Engineer",
    "QA Engineer Salesforce",
    "Automation Engineer Python",
    # Software Engineering
    "Software Engineer Python",
    "Software Engineer Java",
    "Backend Engineer Python",
    "Full Stack Engineer",
    "Software Developer Python",
]

# Title tokens that don't match Oscar's level/background — skip on sight
TITLE_EXCLUDE = {
    "senior", " sr ", "sr.", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "intern", "founding",
    "sales", "field", "hardware", "firmware", "embedded", "mechanical",
    "electrical", "civil", "manufacturing", "supply chain", "customer success",
    "account", "business analyst", "product manager", "data scientist",
    "devops", "security engineer", "network", "database admin",
}

# Location targeting — searches each keyword in each location
# Empty string = LinkedIn default (all locations / remote-friendly)
LOCATIONS = [
    "",                  # general / remote
    "Sacramento, CA",
    "Davis, CA",
    "San Francisco, CA",
    "San Jose, CA",
    "Santa Clara, CA",
    "Sunnyvale, CA",
]

PAGES_PER_KEYWORD = 2    # 25 jobs/page → 50 per keyword — enough without over-scraping
JOBS_PER_PAGE     = 25
MODAL_MAX_STEPS   = 20
WAIT_SEC          = 10
MAX_APPLIES_PER_SESSION = args.max_applies if args.max_applies is not None else 8    # Conservative cap — well under detection threshold
SESSION_BREAK_EVERY     = 4    # Break every 4 applications
SESSION_BREAK_SECS      = (60, 120)  # 1-2 min break (more human-like)

# ── Run folder ────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"linkedin_easy_apply_pa_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log"), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

JSON_FILE   = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE    = os.path.join(RUN_DIR, "jobs.csv")
GMASS_FILE  = os.path.join(RUN_DIR, "gmass_contacts.csv")

# ── XPath selectors ───────────────────────────────────────────────────────────
EASY_BTN    = "//button[@id='jobs-apply-button-id']"
NEXT_BTN    = "//button[@aria-label='Continue to next step']"
REVIEW_BTN  = "//button[@aria-label='Review your application']"
SUBMIT_BTN  = "//button[@aria-label='Submit application']"
DISMISS_BTN = "//button[@aria-label='Dismiss']"
_JS_CLICK   = "arguments[0].click();"

# ── Data ──────────────────────────────────────────────────────────────────────
@dataclass
class JobRecord:
    job_id:           str
    title:            str
    company:          str
    location:         str
    keyword:          str
    status:           str       # applied | skipped | error
    url:              str = ""
    apply_type:       str = "easy_apply"
    platform:         str = "LinkedIn"
    days_since_posted: Optional[int] = None
    skills_mentioned: str = ""
    contact_email:    str = ""
    note:             str = ""
    timestamp:        str = field(default_factory=lambda: datetime.now().isoformat())

_records: list[JobRecord] = []

def save_all():
    if not _records:
        return
    rows = [asdict(r) for r in _records]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(JobRecord.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(rows)

    # ── GMass-ready contacts CSV (only rows with a scraped email) ─────────────
    # GMass expects: Email, First Name, Last Name, Company, Title, Job URL
    gmass_rows = [
        {
            "Email":      r.contact_email,
            "First Name": "",       # recruiter name unknown from job post
            "Last Name":  "",
            "Company":    r.company,
            "Title":      r.title,
            "Job URL":    r.url,
            "Location":   r.location,
            "Skills":     r.skills_mentioned,
        }
        for r in _records if r.contact_email
    ]
    if gmass_rows:
        with open(GMASS_FILE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(gmass_rows[0].keys()))
            w.writeheader()
            w.writerows(gmass_rows)
        log.info(f"  GMass contacts: {len(gmass_rows)} emails → {GMASS_FILE}")
    else:
        log.info("  GMass contacts: no emails found in job descriptions this run")

# ── Driver ────────────────────────────────────────────────────────────────────
def init_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=opts)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return driver


# ── Helpers ───────────────────────────────────────────────────────────────────
def el_exists(driver, xpath: str, timeout: int = 2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except Exception:
        return False

def safe_click(driver, wait, xpath: str, timeout: int = 5) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script(_JS_CLICK, el)
        time.sleep(random.uniform(0.3, 0.8))
        return True
    except Exception:
        return False

def human_wait(min_s=0.4, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))

def xpath_literal(s: str) -> str:
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    parts = s.split("'")
    return "concat(" + ",\"'\",".join(f"'{p}'" for p in parts) + ")"

SKILLS = [
    "python", "java", "javascript", "typescript", "react", "angular", "vue",
    "selenium", "playwright", "cypress", "appium", "testng", "junit",
    "node", "sql", "postgresql", "mongodb", "aws", "azure", "gcp",
    "docker", "kubernetes", "git", "ci/cd", "jenkins", "github actions",
    "rest", "graphql", "django", "flask", "fastapi", "spring",
    "html", "css", "tailwind", "agile", "scrum", "jira",
    "linux", "bash", "terraform", "qa", "automation", "testing",
    "machine learning", "pytorch", "tensorflow",
]

def extract_skills(text: str) -> str:
    low = text.lower()
    return ", ".join(s for s in SKILLS if s in low)

_EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)
# Domains to ignore — LinkedIn system addresses, image placeholders, etc.
_EMAIL_BLOCKLIST = {"linkedin.com", "example.com", "sentry.io", "w3.org", "schema.org"}

def extract_email(text: str) -> str:
    """Return first recruiter/contact email found in job description text."""
    for m in _EMAIL_RE.finditer(text):
        addr = m.group(0).lower()
        domain = addr.split("@")[-1]
        if domain not in _EMAIL_BLOCKLIST:
            return addr
    return ""

def get_job_description(driver) -> str:
    for xp in [
        "//div[contains(@class,'jobs-description__content')]",
        "//div[@id='job-details']",
        "//article[contains(@class,'jobs-description')]",
    ]:
        try:
            el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
            return el.text.strip()
        except Exception:
            pass
    return ""

# ── Work auth form filler ─────────────────────────────────────────────────────
WORK_AUTH_ANSWERS = [
    {"text": "Will you now, or in the future, require sponsorship for employment visa status", "answer": "No"},
    {"text": "Are you legally authorized to work in the United States", "answer": "Yes"},
    {"text": "Are you willing to take a drug test", "answer": "Yes"},
    {"text": "Are you comfortable commuting to this job's location?", "answer": "Yes"},
    {"text": "Are you comfortable working in a remote setting?", "answer": "Yes"},
    {"text": "How did you hear about this job?", "answer": "LinkedIn"},
    {"text": "What is your target salary range?", "answer": "100k-110k"},
]

def fill_work_auth(driver, wait):
    for q in WORK_AUTH_ANSWERS:
        try:
            radio_xpath = (
                f"//fieldset[.//legend[contains(normalize-space(.), {xpath_literal(q['text'])})]]"
                f"//label[@data-test-text-selectable-option__label={xpath_literal(q['answer'])}]"
            )
            el = driver.find_element(By.XPATH, radio_xpath)
            driver.execute_script(_JS_CLICK, el)
            continue
        except Exception:
            pass
        try:
            label_el = driver.find_element(
                By.XPATH, f"//label[contains(normalize-space(.), {xpath_literal(q['text'])})]"
            )
            sel_el = driver.find_element(By.ID, label_el.get_attribute("for"))
            Select(sel_el).select_by_visible_text(q["answer"])
        except Exception:
            pass

def fill_voluntary_self_id(driver, wait):
    for label, value in [("Gender", "Male"), ("Race/Ethnicity", "Asian (Not Hispanic or Latino)")]:
        try:
            Select(
                wait.until(EC.element_to_be_clickable((
                    By.XPATH, f"//label[.//strong[normalize-space()='{label}']]/following::select[1]"
                )))
            ).select_by_visible_text(value)
        except Exception:
            pass
    for opt_text, xp in [
        ("I am not a protected veteran",
         "(//select[.//option[normalize-space()='I am not a protected veteran']])[1]"),
        ("No, I do not have a disability and have not had one in the past",
         "(//select[.//option[normalize-space()='No, I do not have a disability and have not had one in the past']])[1]"),
    ]:
        try:
            Select(driver.find_element(By.XPATH, xp)).select_by_visible_text(opt_text)
        except Exception:
            pass
    try:
        inp = driver.find_element(By.XPATH, "//label[normalize-space()='Your Name']/following::input[1]")
        inp.clear(); inp.send_keys(FULL_NAME)
    except Exception:
        pass
    try:
        from datetime import date
        inp = driver.find_element(By.XPATH, "//label[normalize-space()=\"Today's Date\"]/following::input[1]")
        inp.clear(); inp.send_keys(date.today().strftime("%m/%d/%Y"))
    except Exception:
        pass

def fill_additional_questions(driver, wait):
    for box in driver.find_elements(By.XPATH, "//div[@class='ph5']/div[1]/div"):
        try:
            inp = box.find_element(By.XPATH, ".//input")
            inp.clear(); inp.send_keys("1")
        except Exception:
            pass
        try:
            Select(box.find_element(By.XPATH, ".//select")).select_by_visible_text("Yes")
        except Exception:
            pass
    fill_work_auth(driver, wait)

def fill_home_city(driver):
    if el_exists(driver, "//input[contains(@id,'city-HOME-CITY')]"):
        try:
            inp = driver.find_element(By.XPATH, "//input[contains(@id,'city-HOME-CITY')]")
            inp.send_keys(HOME_CITY)
            time.sleep(0.8)
            inp.send_keys(Keys.DOWN)
            inp.send_keys(Keys.RETURN)
            time.sleep(0.5)
        except Exception:
            pass

def fill_resume_linkedin(driver):
    if el_exists(driver, "//label[normalize-space()='LinkedIn']"):
        try:
            inp = driver.find_element(
                By.XPATH,
                "//div[@data-test-single-line-text-form-component]"
                "[.//label[normalize-space()='LinkedIn']]//input",
            )
            inp.clear(); inp.send_keys(LINKEDIN_URL)
        except Exception:
            pass

_STEP_HANDLERS = {
    "Contact info":                   None,
    "Resume":                         None,
    "Work experience":                None,
    "Education":                      None,
    "Screening questions":            None,
    "Privacy policy":                 lambda d, w: safe_click(
        d, w, "//label[@data-test-text-selectable-option__label='I Agree Terms & Conditions']"
    ),
    "Additional Questions":           fill_additional_questions,
    "Work authorization":             fill_work_auth,
    "Voluntary self identification":  fill_voluntary_self_id,
}

def modal_heading(driver) -> str:
    try:
        els = driver.find_elements(By.XPATH, "//div[@data-test-modal]//h3")
        return els[0].text.strip() if els else ""
    except Exception:
        return ""

def advance_modal(driver, wait) -> bool:
    """Fill current step and advance. Returns True when submitted."""
    heading = modal_heading(driver)
    for h_text, handler in _STEP_HANDLERS.items():
        if h_text.lower() in heading.lower():
            if h_text == "Resume":
                fill_resume_linkedin(driver)
            elif handler:
                try:
                    handler(driver, wait)
                except Exception as e:
                    log.warning(f"    handler '{h_text}': {e}")
            break

    fill_home_city(driver)

    if el_exists(driver, REVIEW_BTN):
        safe_click(driver, wait, REVIEW_BTN)
        human_wait(0.5, 1.2)
        if el_exists(driver, SUBMIT_BTN):
            safe_click(driver, wait, SUBMIT_BTN)
            _dismiss_post_apply(driver, wait)
            return True
        return False

    if el_exists(driver, SUBMIT_BTN):
        safe_click(driver, wait, SUBMIT_BTN)
        _dismiss_post_apply(driver, wait)
        return True

    if el_exists(driver, NEXT_BTN):
        safe_click(driver, wait, NEXT_BTN)
        return False

    raise RuntimeError("No advance button found")

def _dismiss_post_apply(driver, wait):
    for xpath in [DISMISS_BTN, "//button[@aria-label='Done']"]:
        try:
            el = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script(_JS_CLICK, el)
            time.sleep(0.5)
            return
        except Exception:
            pass

def emergency_close(driver, wait):
    safe_click(driver, wait, DISMISS_BTN)
    time.sleep(0.4)
    safe_click(driver, wait,
               "//div[@role='alertdialog']//button[@data-control-name='discard_application_confirm_btn']")

def run_easy_apply(driver, wait) -> str:
    if not safe_click(driver, wait, EASY_BTN):
        return "skipped"
    if args.dry_run:
        # Close modal immediately without submitting
        emergency_close(driver, wait)
        return "dry_run"
    for step in range(1, MODAL_MAX_STEPS + 1):
        try:
            submitted = advance_modal(driver, wait)
            if submitted:
                log.info(f"    Applied (step {step})")
                return "applied"
            human_wait(0.5, 1.5)
        except RuntimeError as e:
            log.warning(f"    Stuck at step {step}: {e}")
            emergency_close(driver, wait)
            return "error"
        except Exception as e:
            log.error(f"    Modal error step {step}: {e}")
            emergency_close(driver, wait)
            return "error"
    log.warning(f"    Exceeded {MODAL_MAX_STEPS} steps — aborting")
    emergency_close(driver, wait)
    return "error"

# ── Job metadata ──────────────────────────────────────────────────────────────
def get_job_meta(driver, job_el) -> dict:
    job_id = job_el.get_attribute("data-occludable-job-id") or ""
    title = company = location = ""
    try:
        title = job_el.find_element(
            By.XPATH, ".//a[contains(@class,'job-card-container__link')]"
        ).text.strip()
    except Exception:
        pass
    try:
        company = job_el.find_element(
            By.XPATH, ".//span[contains(@class,'job-card-container__primary-description')]"
        ).text.strip()
    except Exception:
        pass
    try:
        location = job_el.find_element(
            By.XPATH, ".//li[contains(@class,'job-card-container__metadata-item')]"
        ).text.strip()
    except Exception:
        pass
    url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else ""
    return {"job_id": job_id, "title": title, "company": company, "location": location, "url": url}

# ── Search URL ────────────────────────────────────────────────────────────────
def search_url(keyword: str, start: int, location: str = "") -> str:
    from urllib.parse import quote_plus
    kw = quote_plus(keyword)
    loc = f"&location={quote_plus(location)}" if location else ""
    # f_LF=f_AL filters for Easy Apply only
    return f"https://www.linkedin.com/jobs/search/?keywords={kw}&f_LF=f_AL{loc}&start={start}"

# ── Login ─────────────────────────────────────────────────────────────────────
def login(driver, wait):
    driver.get("https://www.linkedin.com/login")
    time.sleep(5)  # Give React login page extra time to hydrate

    # LinkedIn uses id="username" on most regions but falls back to name/type selectors
    EMAIL_XPATHS = [
        "//input[@id='username']",
        "//input[@name='session_key']",
        "//input[@type='email']",
        "//input[@autocomplete='username']",
        # New LinkedIn React login page — first visible text input
        "(//input[@type='text'])[1]",
        # LinkedIn inputs may have no explicit type attr (defaults to text)
        "//input[not(@type) or @type='text' or @type='email'][1]",
        # Match by placeholder label
        "//input[contains(@placeholder,'Email') or contains(@placeholder,'email') or contains(@placeholder,'phone')]",
        # Absolute last resort: first input on page that isn't a button/checkbox/hidden
        "(//input[@type!='password' and @type!='submit' and @type!='checkbox' and @type!='hidden'])[1]",
        "(//input)[1]",
    ]
    PWD_XPATHS = [
        "//input[@id='password']",
        "//input[@name='session_password']",
        "//input[@autocomplete='current-password']",
        "//input[@type='password']",
    ]

    email_field = None
    for xp in EMAIL_XPATHS:
        try:
            candidates = driver.find_elements(By.XPATH, xp)
            for el in candidates:
                if el.is_displayed() and el.is_enabled():
                    email_field = el
                    break
            if email_field:
                break
        except Exception:
            continue

    if not email_field:
        driver.save_screenshot(os.path.join(RUN_DIR, "login_page.png"))
        raise RuntimeError("Could not find LinkedIn email field — check login_page.png")

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", email_field)
    human_wait(0.3, 0.6)
    email_field.clear()
    email_field.send_keys(USERNAME)
    human_wait(0.5, 1.2)

    for xp in PWD_XPATHS:
        try:
            candidates = driver.find_elements(By.XPATH, xp)
            for el in candidates:
                if el.is_displayed() and el.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    human_wait(0.2, 0.4)
                    el.clear()
                    el.send_keys(PASSWORD)
                    break
            else:
                continue
            break
        except Exception:
            continue

    human_wait(0.5, 1.0)
    safe_click(driver, wait, "//button[@type='submit'] | //button[@data-litms-control-urn='login-submit']")
    time.sleep(4)

    if "feed" not in driver.current_url and "checkpoint" not in driver.current_url:
        log.warning("Login may have failed — check screenshot in run folder.")
        driver.save_screenshot(os.path.join(RUN_DIR, "login_check.png"))
    else:
        log.info("Logged in to LinkedIn.")
        driver.save_screenshot(os.path.join(RUN_DIR, "login_success.png"))

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    mode = "DRY-RUN (no submissions)" if args.dry_run else "LIVE"
    log.info("=" * 60)
    loc_label = ", ".join(l if l else "general" for l in LOCATIONS)
    log.info(f"  LinkedIn Easy Apply PA  |  {len(KEYWORDS)} keywords × {len(LOCATIONS)} locations × {PAGES_PER_KEYWORD} pages  |  {mode}")
    log.info(f"  Locations: {loc_label}")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    wait   = WebDriverWait(driver, WAIT_SEC)
    counts  = {"applied": 0, "skipped": 0, "error": 0, "dry_run": 0}
    seen_ids: set[str] = set()

    try:
        login(driver, wait)

        for location in LOCATIONS:
            for keyword in KEYWORDS:
                loc_tag = f" [{location}]" if location else " [general]"
                log.info(f"\n{'─'*60}")
                log.info(f"  Keyword: {keyword}{loc_tag}")
                log.info(f"{'─'*60}")

                for page in range(PAGES_PER_KEYWORD):
                    start = page * JOBS_PER_PAGE
                    log.info(f"  Page {page+1} (start={start})")
                    try:
                        driver.get(search_url(keyword, start, location))
                        human_wait(2.0, 3.5)
                    except InvalidSessionIdException:
                        log.error("Chrome session lost — exiting.")
                        raise

                    try:
                        WebDriverWait(driver, WAIT_SEC).until(
                            EC.presence_of_element_located((By.XPATH, "//li[@data-occludable-job-id]"))
                        )
                    except TimeoutException:
                        log.info(f"  Page {page+1}: no jobs — stopping keyword.")
                        break

                    job_els = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
                    log.info(f"  Page {page+1}: {len(job_els)} jobs")

                    for idx, job_el in enumerate(job_els):
                        try:
                            meta   = get_job_meta(driver, job_el)
                            job_id = meta["job_id"]
                            if not job_id or job_id in seen_ids:
                                continue
                            seen_ids.add(job_id)

                            title_low = meta["title"].lower()
                            loc_str   = meta.get("location", "") or "?"
                            title_skip = any(tok in title_low for tok in TITLE_EXCLUDE)
                            log.info(
                                f"  [{idx+1:02}/{len(job_els)}] {meta['title'][:38]:<38} | "
                                f"{meta['company'][:18]:<18} | {loc_str[:22]:<22} | "
                                f"{'SKIP:title' if title_skip else '→ checking'}"
                            )

                            # Skip titles that don't match Oscar's background
                            if title_skip:
                                counts["skipped"] = counts.get("skipped", 0) + 1
                                _records.append(JobRecord(
                                    job_id=job_id, title=meta["title"],
                                    company=meta["company"], location=meta["location"],
                                    keyword=keyword, status="skipped", url=meta["url"],
                                    note="title_excluded",
                                ))
                                human_wait(0.5, 1.0)
                                continue

                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", job_el)
                            try:
                                job_el.click()
                            except Exception:
                                driver.execute_script(_JS_CLICK, job_el)
                            human_wait(1.0, 2.5)

                            desc = get_job_description(driver)
                            contact_email = extract_email(desc)
                            if contact_email:
                                log.info(f"    Found email: {contact_email}")

                            if not el_exists(driver, EASY_BTN):
                                status = "skipped"
                            else:
                                status = run_easy_apply(driver, wait)

                            counts[status] = counts.get(status, 0) + 1
                            _records.append(JobRecord(
                                job_id=job_id,
                                title=meta["title"],
                                company=meta["company"],
                                location=meta["location"],
                                keyword=keyword,
                                status=status,
                                url=meta["url"],
                                skills_mentioned=extract_skills(desc),
                                contact_email=contact_email,
                            ))

                            # ── Anti-detection: paced delays ──────────────────
                            # Longer wait after each apply (looks human)
                            if status == "applied":
                                human_wait(8.0, 18.0)
                                # Extra break every N applications
                                if counts["applied"] % SESSION_BREAK_EVERY == 0:
                                    pause = random.uniform(*SESSION_BREAK_SECS)
                                    log.info(f"  [anti-detect] Session break {pause:.0f}s after {counts['applied']} applies")
                                    time.sleep(pause)
                                # Hard cap
                                if counts["applied"] >= MAX_APPLIES_PER_SESSION:
                                    log.info(f"  [anti-detect] Hit session cap ({MAX_APPLIES_PER_SESSION}) — stopping.")
                                    raise StopIteration
                            else:
                                human_wait(2.0, 4.5)

                        except (InvalidSessionIdException, StopIteration):
                            raise
                        except StaleElementReferenceException:
                            log.warning(f"  [{idx+1}] Stale element — skip")
                        except Exception as e:
                            log.error(f"  [{idx+1}] Error: {e}")
                            counts["error"] += 1
                            emergency_close(driver, wait)

    except StopIteration:
        log.info("  Session cap reached — wrapping up cleanly.")
    except (InvalidSessionIdException, Exception) as e:
        if not isinstance(e, InvalidSessionIdException):
            log.error(f"Fatal error: {e}")
    finally:
        save_all()
        try:
            driver.quit()
        except Exception:
            pass

    log.info("=" * 60)
    log.info("  RUN SUMMARY")
    log.info("=" * 60)
    log.info(f"  Applied  : {counts['applied']}")
    log.info(f"  Skipped  : {counts['skipped']}")
    log.info(f"  Errors   : {counts['error']}")
    log.info(f"  Dry-run  : {counts.get('dry_run', 0)}")
    log.info(f"  Unique jobs seen: {len(seen_ids)}")
    if _records:
        applied_recs = [r for r in _records if r.status == "applied"]
        if applied_recs:
            log.info("")
            log.info("  Jobs applied to:")
            for r in applied_recs:
                log.info(f"    ✓ {r.title[:40]:<40} @ {r.company[:25]:<25}  {r.location[:20]}")
        skipped_by_reason: dict = {}
        for r in _records:
            if r.status == "skipped":
                reason = r.note or "unknown"
                skipped_by_reason[reason] = skipped_by_reason.get(reason, 0) + 1
        if skipped_by_reason:
            log.info("")
            log.info("  Skipped reasons:")
            for reason, cnt in sorted(skipped_by_reason.items(), key=lambda x: -x[1]):
                log.info(f"    {reason:<30} {cnt:>4}")

    # ── Sync to Google Sheets ──────────────────────────────────────────────────
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(__file__))
        from library.gsheets import sync_jobs
        sync_jobs([asdict(r) for r in _records], platform="LinkedIn")
        log.info("  Synced to Google Sheets.")
    except Exception as e:
        log.warning(f"  Google Sheets sync skipped: {e}")

    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
