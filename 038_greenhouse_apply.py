"""
Greenhouse Job Apply — my.greenhouse.io
Searches for QA/SDET/SWE roles on Greenhouse's candidate portal and applies via
the Quick Apply flow (one-click for jobs that support it, full form for the rest).

Run locally — Greenhouse uses Google OAuth so automated login is blocked headless.
The script opens a visible browser, pauses for manual login if needed, then takes over.

Usage:
  python 038_greenhouse_apply.py
  python 038_greenhouse_apply.py --dry-run     # navigate + collect data, do not submit
  python 038_greenhouse_apply.py --pages 3     # how many search result pages per keyword
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
parser.add_argument("--dry-run", action="store_true", help="Collect data, do not submit")
parser.add_argument("--pages", type=int, default=10, help="Result pages per keyword")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
FULL_NAME   = "Oscar Leung"
EMAIL       = os.getenv("LINKIN_USERNAME") or os.getenv("handshake_email", "")
PHONE       = os.getenv("PHONE_NUMBER", "")
LINKEDIN_URL = "https://www.linkedin.com/in/oscar-leung/"
RESUME_PATH = os.getenv("RESUME_PDF_PATH", "")   # set in .env: RESUME_PDF_PATH=/abs/path/resume.pdf

KEYWORDS = [
    "QA Engineer",
    "SDET",
    "Software Engineer in Test",
    "Automation Engineer",
    "Software Engineer",
    "Frontend Engineer",
    "React Developer",
    "Full Stack Engineer",
    "QA Automation",
]

# Title tokens that disqualify a job (case-insensitive)
TITLE_EXCLUDE = {
    "founding", "sr.", " sr ", "sales", "senior", "product", "robotics",
    "campus", "customer", "manager", "digital", "firmware", "lead", "field",
    "principal", "director", "staff",
}

WAIT_SEC       = 10
MODAL_MAX_STEPS = 15
BASE_URL = "https://my.greenhouse.io"

# ── Run folder ────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"greenhouse_apply_{RUN_ID}")
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

JSON_FILE = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE  = os.path.join(RUN_DIR, "jobs.csv")

# ── Data model ────────────────────────────────────────────────────────────────
@dataclass
class GHJob:
    job_id:           str
    title:            str
    company:          str
    location:         str
    keyword:          str
    status:           str       # applied | skipped | error | dry_run | skipped_external
    url:              str = ""
    apply_type:       str = ""  # quick_apply | full_form | external | unknown
    platform:         str = "Greenhouse"
    remote_type:      str = ""
    employment_type:  str = ""
    salary_raw:       str = ""
    skills_mentioned: str = ""
    description_full: str = ""
    note:             str = ""
    timestamp:        str = field(default_factory=lambda: datetime.now().isoformat())

_records: list[GHJob] = []
_seen_ids: set[str] = set()
_JS_CLICK = "arguments[0].click();"

def save_all():
    rows = [asdict(r) for r in _records]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(GHJob.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(rows)

# ── Helpers ───────────────────────────────────────────────────────────────────
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

def title_is_excluded(title: str) -> bool:
    low = title.lower()
    return any(tok in low for tok in TITLE_EXCLUDE)

def human_wait(min_s=0.5, max_s=1.5):
    time.sleep(random.uniform(min_s, max_s))

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
        human_wait(0.3, 0.8)
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

def dismiss_modal(driver):
    for xp in [
        "//button[@aria-label='Close']",
        "//button[normalize-space()='Close']",
        "//button[normalize-space()='Cancel']",
        "//button[normalize-space()='Dismiss']",
    ]:
        if el_exists(driver, xp, timeout=1):
            try:
                driver.find_element(By.XPATH, xp).click()
                time.sleep(0.4)
                return
            except Exception:
                pass
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        time.sleep(0.4)
    except Exception:
        pass

# ── Driver ────────────────────────────────────────────────────────────────────
def init_driver() -> webdriver.Chrome:
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

# ── Login ─────────────────────────────────────────────────────────────────────
def login(driver, wait):
    """
    Greenhouse login flow:
      1. Enter email → click "Send security code"
      2. Check your email for the OTP → script pauses, you type it in the browser
      3. Script detects the redirect to /dashboard and continues automatically.

    On subsequent runs within the same session the cookie is active and step 1-2 are skipped.
    """
    driver.get(f"{BASE_URL}/dashboard")
    time.sleep(3)

    # Already logged in?
    if "dashboard" in driver.current_url and "login" not in driver.current_url:
        log.info("Already logged in to Greenhouse.")
        driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))
        return

    # Step 1 — enter email and request security code
    email_xp = "//input[@type='email' or @id='email' or @name='email' or contains(@placeholder,'email')]"
    try:
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, email_xp))
        )
        email_field.clear()
        email_field.send_keys(EMAIL)
        log.info(f"Entered email: {EMAIL}")
    except TimeoutException:
        log.warning("Could not find email field — check screenshot.")
        driver.save_screenshot(os.path.join(RUN_DIR, "login_page.png"))
        sys.exit(1)

    # Click "Send security code"
    send_code_xp = (
        "//button[contains(normalize-space(),'Send security code')] | "
        "//button[contains(normalize-space(),'Send code')] | "
        "//input[@type='submit']"
    )
    safe_click(driver, wait, send_code_xp)
    time.sleep(1)
    driver.save_screenshot(os.path.join(RUN_DIR, "after_send_code.png"))

    # Step 2 — wait for OTP entry and redirect to dashboard
    log.info("=" * 60)
    log.info("  CHECK YOUR EMAIL for the Greenhouse security code.")
    log.info("  Enter it in the browser window — you have 120 seconds.")
    log.info("=" * 60)

    try:
        WebDriverWait(driver, 120).until(EC.url_contains("/dashboard"))
        log.info("Login successful.")
    except TimeoutException:
        log.warning("Login timeout. Check the browser and re-run.")
        driver.save_screenshot(os.path.join(RUN_DIR, "login_timeout.png"))
        sys.exit(1)

    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))

# ── Job search ────────────────────────────────────────────────────────────────
def search_url(keyword: str, page: int) -> str:
    """
    Greenhouse job board search URL.
    page is 1-based. Each page shows ~10 results.
    """
    return f"{BASE_URL}/job_board/search?keyword={quote_plus(keyword)}&page={page}"

def get_job_cards(driver) -> list:
    """Return all job card elements on the current search results page."""
    # Greenhouse renders job cards as <div> with class containing 'job-result' or as <li> items
    for xp in [
        "//div[contains(@class,'job-result')]",
        "//div[contains(@class,'job-post')]",
        "//li[contains(@class,'job-result')]",
        "//div[@data-job-id]",
        "//div[contains(@class,'opening')]",
    ]:
        cards = driver.find_elements(By.XPATH, xp)
        if cards:
            return cards
    return []

def get_card_meta(card) -> dict:
    """Extract job_id, title, company, location from a search result card."""
    job_id = (
        card.get_attribute("data-job-id") or
        card.get_attribute("data-id") or
        card.get_attribute("id") or ""
    )
    title = company = location = url = ""
    try:
        title = card.find_element(By.XPATH, ".//h2 | .//h3 | .//a[contains(@class,'title')]").text.strip()
    except Exception:
        pass
    try:
        company = card.find_element(
            By.XPATH, ".//*[contains(@class,'company')] | .//*[contains(@class,'employer')]"
        ).text.strip()
    except Exception:
        pass
    try:
        location = card.find_element(
            By.XPATH, ".//*[contains(@class,'location')] | .//*[contains(@class,'city')]"
        ).text.strip()
    except Exception:
        pass
    try:
        link = card.find_element(By.XPATH, ".//a[@href]")
        href = link.get_attribute("href") or ""
        url  = href if href.startswith("http") else f"{BASE_URL}{href}"
        if not job_id:
            m = re.search(r"/jobs/(\d+)|job_id=(\d+)", href)
            if m:
                job_id = m.group(1) or m.group(2)
    except Exception:
        pass
    return {"job_id": job_id, "title": title, "company": company, "location": location, "url": url}

# ── Job detail page ───────────────────────────────────────────────────────────
def get_job_detail(driver) -> dict:
    """Extract description, remote_type, employment_type, salary from the job detail page."""
    desc = ""
    for xp in [
        "//div[@id='content']",
        "//div[contains(@class,'job-post-description')]",
        "//div[contains(@class,'description')]",
        "//section[contains(@class,'content')]",
    ]:
        try:
            el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
            desc = el.text.strip()
            if len(desc) > 100:
                break
        except Exception:
            pass

    low = desc.lower()
    if "remote" in low and ("hybrid" in low or "onsite" in low or "in-office" in low):
        remote_type = "hybrid"
    elif "remote" in low:
        remote_type = "remote"
    else:
        remote_type = "onsite"

    emp_type = (
        "full-time"  if "full-time" in low or "full time" in low else
        "part-time"  if "part-time" in low or "part time" in low else
        "internship" if "intern" in low or "co-op" in low else
        "contract"   if "contract" in low else ""
    )

    salary_raw = ""
    m = re.search(r"\$[\d,]+(?:\s*[–\-—]\s*\$[\d,]+)?(?:\s*/\s*(?:yr|hr|year|hour))?", desc)
    if m:
        salary_raw = m.group(0)

    return {
        "description_full": desc[:8000],
        "remote_type": remote_type,
        "employment_type": emp_type,
        "salary_raw": salary_raw,
        "skills_mentioned": extract_skills(desc),
    }

# ── Apply flow ────────────────────────────────────────────────────────────────

# Greenhouse quick apply button (profile-based one-click apply)
QUICK_APPLY_BTN = (
    "//button[contains(normalize-space(),'Quick apply')] | "
    "//button[contains(normalize-space(),'quick apply')] | "
    "//a[contains(normalize-space(),'Quick apply')]"
)

# Standard "Apply" button that opens the full application form
FULL_APPLY_BTN = (
    "//button[contains(normalize-space(),'Apply for this job')] | "
    "//button[contains(normalize-space(),'Apply now')] | "
    "//a[contains(normalize-space(),'Apply for this job')] | "
    "//a[contains(normalize-space(),'Apply now')] | "
    "//button[normalize-space()='Apply']"
)

# External apply redirects away from Greenhouse
EXTERNAL_APPLY_BTN = (
    "//a[contains(@href,'http') and ("
    "  contains(normalize-space(),'Apply on company') or "
    "  contains(normalize-space(),'Apply externally') or "
    "  contains(normalize-space(),'Visit company site')"
    ")]"
)

# Greenhouse full-form navigation buttons
GH_NEXT_BTN   = (
    "//button[normalize-space()='Next'] | "
    "//button[normalize-space()='Continue'] | "
    "//input[@type='submit' and @value='Next']"
)
GH_SUBMIT_BTN = (
    "//button[normalize-space()='Submit Application'] | "
    "//button[normalize-space()='Submit'] | "
    "//input[@type='submit' and contains(@value,'Submit')]"
)


def detect_apply_type(driver) -> str:
    if el_exists(driver, QUICK_APPLY_BTN, timeout=2):
        return "quick_apply"
    if el_exists(driver, EXTERNAL_APPLY_BTN, timeout=1):
        return "external"
    if el_exists(driver, FULL_APPLY_BTN, timeout=2):
        return "full_form"
    return "unknown"


def fill_greenhouse_form(driver, wait):
    """
    Fill standard Greenhouse application form fields.
    Handles: name, email, phone, LinkedIn, resume upload, cover letter,
    education, work experience, and generic text/select inputs.
    """
    # ── Name ──────────────────────────────────────────────────────────────────
    for xp in [
        "//input[@id='first_name' or contains(@name,'first_name')]",
        "//input[@placeholder='First name' or @placeholder='First Name']",
    ]:
        if el_exists(driver, xp, timeout=1):
            el = driver.find_element(By.XPATH, xp)
            if not el.get_attribute("value"):
                el.send_keys(FULL_NAME.split()[0])
            break

    for xp in [
        "//input[@id='last_name' or contains(@name,'last_name')]",
        "//input[@placeholder='Last name' or @placeholder='Last Name']",
    ]:
        if el_exists(driver, xp, timeout=1):
            el = driver.find_element(By.XPATH, xp)
            if not el.get_attribute("value"):
                el.send_keys(FULL_NAME.split()[-1])
            break

    # ── Email ──────────────────────────────────────────────────────────────────
    for xp in [
        "//input[@id='email' or contains(@name,'email')]",
        "//input[@type='email']",
    ]:
        if el_exists(driver, xp, timeout=1):
            el = driver.find_element(By.XPATH, xp)
            if not el.get_attribute("value"):
                el.send_keys(EMAIL)
            break

    # ── Phone ──────────────────────────────────────────────────────────────────
    if PHONE:
        for xp in [
            "//input[@id='phone' or contains(@name,'phone')]",
            "//input[@type='tel']",
        ]:
            if el_exists(driver, xp, timeout=1):
                el = driver.find_element(By.XPATH, xp)
                if not el.get_attribute("value"):
                    el.send_keys(PHONE)
                break

    # ── LinkedIn ───────────────────────────────────────────────────────────────
    for xp in [
        "//input[contains(@id,'linkedin') or contains(@name,'linkedin')]",
        "//input[contains(@placeholder,'LinkedIn')]",
        "//input[@id='job_application_answers_attributes_0_text_value']",
    ]:
        if el_exists(driver, xp, timeout=1):
            el = driver.find_element(By.XPATH, xp)
            if not el.get_attribute("value"):
                el.send_keys(LINKEDIN_URL)
            break

    # ── Resume upload ──────────────────────────────────────────────────────────
    if RESUME_PATH and os.path.isfile(RESUME_PATH):
        for xp in [
            "//input[@type='file' and contains(@accept,'.pdf')]",
            "//input[@type='file' and contains(@id,'resume')]",
            "//input[@type='file']",
        ]:
            if el_exists(driver, xp, timeout=1):
                try:
                    driver.find_element(By.XPATH, xp).send_keys(RESUME_PATH)
                    time.sleep(1.5)   # wait for upload processing
                except Exception:
                    pass
                break

    # ── Work authorization radio buttons ────────────────────────────────────────
    # Greenhouse custom questions are rendered as radio groups
    for radio_grp in driver.find_elements(By.XPATH, "//div[contains(@class,'field') and .//input[@type='radio']]"):
        label_text = ""
        try:
            label_text = radio_grp.find_element(By.XPATH, ".//label[not(@for)]").text.lower()
        except Exception:
            pass

        if any(kw in label_text for kw in ("sponsor", "visa", "authorized", "legally")):
            # Work auth → Yes (authorized), sponsorship → No
            answer = "no" if "sponsor" in label_text else "yes"
            try:
                radio = radio_grp.find_element(
                    By.XPATH, f".//label[contains(translate(normalize-space(.),'YES','yes'),'{answer}')]"
                )
                driver.execute_script(_JS_CLICK, radio)
            except Exception:
                pass
        else:
            # Generic — pick "Yes" if available, else first option
            try:
                yes = radio_grp.find_elements(
                    By.XPATH, ".//label[contains(translate(normalize-space(.),'YES','yes'),'yes')]"
                )
                if yes:
                    driver.execute_script(_JS_CLICK, yes[0])
                    continue
                first = radio_grp.find_elements(By.XPATH, ".//input[@type='radio']")
                if first:
                    driver.execute_script(_JS_CLICK, first[0])
            except Exception:
                pass

    # ── Select dropdowns ─────────────────────────────────────────────────────
    for sel_el in driver.find_elements(By.XPATH, "//select"):
        try:
            sel = Select(sel_el)
            if sel_el.get_attribute("value"):
                continue    # already filled
            try:
                sel.select_by_visible_text("Yes")
            except Exception:
                if len(sel.options) > 1:
                    sel.select_by_index(1)
        except Exception:
            pass

    # ── Generic text inputs ────────────────────────────────────────────────────
    for inp in driver.find_elements(By.XPATH, "//input[@type='text' and not(@value)]"):
        try:
            placeholder = (inp.get_attribute("placeholder") or "").lower()
            if "website" in placeholder or "portfolio" in placeholder:
                inp.send_keys(LINKEDIN_URL)
            elif "salary" in placeholder or "compensation" in placeholder:
                inp.send_keys("100000")
        except Exception:
            pass


def run_quick_apply(driver, wait) -> str:
    """One-click Quick Apply (Greenhouse profile-based)."""
    if not safe_click(driver, wait, QUICK_APPLY_BTN):
        return "error"

    # Confirmation modal may appear
    confirm_xp = (
        "//button[contains(normalize-space(),'Confirm') or "
        "normalize-space()='Submit' or normalize-space()='Apply']"
    )
    if el_exists(driver, confirm_xp, timeout=3):
        safe_click(driver, wait, confirm_xp)

    # Wait for success indicator
    success_xp = (
        "//div[contains(@class,'success')] | "
        "//*[contains(normalize-space(),'application has been submitted')] | "
        "//*[contains(normalize-space(),'successfully applied')] | "
        "//*[contains(normalize-space(),'Thank you')]"
    )
    if el_exists(driver, success_xp, timeout=5):
        return "applied"

    # Fallback: if confirmation appeared and we clicked it, assume success
    return "applied"


def run_full_form_apply(driver, wait) -> str:
    """Drive the multi-step Greenhouse application form."""
    if not safe_click(driver, wait, FULL_APPLY_BTN):
        return "error"
    human_wait(1.0, 2.0)

    for step in range(1, MODAL_MAX_STEPS + 1):
        try:
            fill_greenhouse_form(driver, wait)
            human_wait(0.5, 1.0)

            # Submit?
            if el_exists(driver, GH_SUBMIT_BTN, timeout=2):
                safe_click(driver, wait, GH_SUBMIT_BTN)
                human_wait(1.5, 2.5)
                # Confirm success
                success_xp = (
                    "//*[contains(normalize-space(),'application has been submitted')] | "
                    "//*[contains(normalize-space(),'successfully applied')] | "
                    "//*[contains(normalize-space(),'Thank you for applying')] | "
                    "//h1[contains(normalize-space(),'Thank you')]"
                )
                if el_exists(driver, success_xp, timeout=5):
                    log.info(f"    Applied (step {step})")
                    return "applied"
                return "applied"   # page changed — assume success

            # Next page?
            if el_exists(driver, GH_NEXT_BTN, timeout=2):
                safe_click(driver, wait, GH_NEXT_BTN)
                human_wait(0.5, 1.2)
                continue

            log.warning(f"    No Next/Submit at step {step}")
            break

        except Exception as e:
            log.error(f"    Form error at step {step}: {e}")
            break

    dismiss_modal(driver)
    return "error"


def apply_to_job(driver, wait) -> tuple[str, str]:
    """
    Detect apply type and drive the correct flow.
    Returns (status, apply_type).
    """
    apply_type = detect_apply_type(driver)

    if apply_type == "external":
        return "skipped_external", "external"

    if apply_type == "unknown":
        return "skipped_no_button", "unknown"

    if args.dry_run:
        return "dry_run", apply_type

    if apply_type == "quick_apply":
        status = run_quick_apply(driver, wait)
    else:
        status = run_full_form_apply(driver, wait)

    return status, apply_type

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Greenhouse Apply  |  {len(KEYWORDS)} keywords × {args.pages} pages  |  {mode}")
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

            for page_num in range(1, args.pages + 1):
                url = search_url(keyword, page_num)
                log.info(f"  Page {page_num}  →  {url}")
                driver.get(url)
                human_wait(2.0, 3.5)
                driver.save_screenshot(os.path.join(RUN_DIR, f"search_{keyword.replace(' ','_')}_p{page_num}.png"))

                cards = get_job_cards(driver)
                if not cards:
                    log.info(f"  No job cards on page {page_num} — next keyword.")
                    break

                log.info(f"  {len(cards)} cards")

                for idx, card in enumerate(cards):
                    try:
                        meta   = get_card_meta(card)
                        job_id = meta["job_id"] or meta["url"]

                        if not job_id or job_id in _seen_ids:
                            continue
                        _seen_ids.add(job_id)

                        if title_is_excluded(meta["title"]):
                            log.info(f"  [{idx+1}] Title excluded: {meta['title']}")
                            counts["skipped"] = counts.get("skipped", 0) + 1
                            _records.append(GHJob(
                                job_id=job_id, title=meta["title"], company=meta["company"],
                                location=meta["location"], keyword=keyword,
                                status="skipped", note="title_excluded", url=meta["url"],
                            ))
                            continue

                        log.info(f"  [{idx+1}/{len(cards)}] {meta['title']} @ {meta['company']}")

                        # Navigate to job detail page
                        if meta["url"]:
                            driver.get(meta["url"])
                            human_wait(1.5, 2.5)
                        else:
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                            try:
                                card.click()
                            except Exception:
                                driver.execute_script(_JS_CLICK, card)
                            human_wait(1.5, 2.5)

                        detail = get_job_detail(driver)
                        status, apply_type = apply_to_job(driver, wait)

                        log.info(f"    {apply_type} → {status}")
                        counts[status] = counts.get(status, 0) + 1

                        _records.append(GHJob(
                            job_id=job_id,
                            title=meta["title"],
                            company=meta["company"],
                            location=meta["location"],
                            keyword=keyword,
                            status=status,
                            url=meta["url"],
                            apply_type=apply_type,
                            remote_type=detail["remote_type"],
                            employment_type=detail["employment_type"],
                            salary_raw=detail["salary_raw"],
                            skills_mentioned=detail["skills_mentioned"],
                            description_full=detail["description_full"],
                        ))

                        # Navigate back to search results
                        driver.back()
                        human_wait(1.5, 2.5)

                    except StaleElementReferenceException:
                        log.warning(f"  [{idx+1}] Stale element — re-fetching page")
                        driver.refresh()
                        human_wait(1.5, 2.0)
                        break
                    except Exception as e:
                        log.error(f"  [{idx+1}] Error: {e}")
                        counts["error"] = counts.get("error", 0) + 1
                        dismiss_modal(driver)

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

    # Status breakdown
    for status, cnt in sorted(counts.items()):
        log.info(f"  {status:<35} {cnt:>5}")

    # ── Sync to Google Sheets ──────────────────────────────────────────────────
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from library.gsheets import sync_jobs
        sync_jobs([asdict(r) for r in _records], platform="Greenhouse")
        log.info("  Synced to Google Sheets.")
    except Exception as e:
        log.warning(f"  Google Sheets sync skipped: {e}")

    log.info(f"  JSON → {JSON_FILE}")
    log.info(f"  CSV  → {CSV_FILE}")
    log.info("=" * 60)


if __name__ == "__main__":
    run()
