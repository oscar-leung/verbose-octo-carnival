"""
Greenhouse Job Apply — boards.greenhouse.io via Google site: search
────────────────────────────────────────────────────────────────────
Strategy (from the LinkedIn tip):
  Use Google's site: operator to find jobs posted directly on
  boards.greenhouse.io that never appear on LinkedIn or Indeed.

No Greenhouse account login needed to apply — each job has a public
application form. my.greenhouse.io login (OTP) is only used once at
the end to sync your applications to your profile.

Flow:
  1. Google search: site:boards.greenhouse.io inurl:/jobs/ <role> <location>
  2. Collect all boards.greenhouse.io/*/jobs/* URLs from results
  3. Navigate to each job page
  4. Fill the Greenhouse application form (name, email, phone, resume, etc.)
  5. Submit — or pause for OTP code if my.greenhouse.io quick-apply is triggered

Usage:
  python 038_greenhouse_apply.py
  python 038_greenhouse_apply.py --dry-run       # scrape + log, do not submit
  python 038_greenhouse_apply.py --google-pages 5  # Google result pages (default 10)
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
parser.add_argument("--google-pages", type=int, default=10,
                    help="Google result pages to scrape per query (default 10, ~100 jobs)")
args = parser.parse_args()

# ── Config ────────────────────────────────────────────────────────────────────
FULL_NAME    = "Oscar Leung"
EMAIL        = os.getenv("LINKIN_USERNAME") or os.getenv("handshake_email", "")
PHONE        = os.getenv("PHONE_NUMBER", "")
LINKEDIN_URL = "https://www.linkedin.com/in/oscar-leung/"
RESUME_PATH  = os.getenv("RESUME_PDF_PATH", "")   # RESUME_PDF_PATH=/abs/path/Oscar_Leung_Resume.pdf

# Oscar's optimised Google site: search query
GOOGLE_QUERY = (
    'site:boards.greenhouse.io inurl:/jobs/ '
    '(SDET OR "Software Engineer in Test" OR "QA Engineer" OR '
    '"Test Automation Engineer" OR "Quality Engineer" OR "Software Quality Engineer") '
    '(remote OR "San Francisco" OR "Bay Area" OR "San Jose" OR "Santa Clara" OR '
    'Cupertino OR Sunnyvale OR "Mountain View" OR "Palo Alto" OR '
    '"Redwood City" OR Fremont OR Milpitas OR Davis) '
    '-staff -senior -principal -lead -manager -director -vp -head -architect -intern -internship'
)

# Title tokens to skip at the application level (catches cases Google doesn't filter)
TITLE_EXCLUDE = {
    "senior", "sr.", " sr ", "staff", "principal", "lead", "manager", "director",
    "vp ", "head of", "architect", "intern", "founding", "sales", "field",
}

WAIT_SEC       = 10
MODAL_MAX_STEPS = 15
RESULTS_PER_GOOGLE_PAGE = 10

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
    status:           str       # applied | skipped | error | dry_run | skipped_external
    url:              str = ""
    apply_type:       str = ""  # full_form | external | unknown
    platform:         str = "Greenhouse"
    remote_type:      str = ""
    employment_type:  str = ""
    salary_raw:       str = ""
    skills_mentioned: str = ""
    description_full: str = ""
    note:             str = ""
    timestamp:        str = field(default_factory=lambda: datetime.now().isoformat())

_records: list[GHJob] = []
_seen_urls: set[str] = set()
_JS_CLICK = "arguments[0].click();"

def save_all():
    rows = [asdict(r) for r in _records]
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(GHJob.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(rows)

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

def title_is_excluded(title: str) -> bool:
    low = title.lower()
    return any(tok in low for tok in TITLE_EXCLUDE)

# ── Browser helpers ───────────────────────────────────────────────────────────
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
    for xp in ["//button[@aria-label='Close']", "//button[normalize-space()='Close']",
               "//button[normalize-space()='Cancel']"]:
        if el_exists(driver, xp, timeout=1):
            try:
                driver.find_element(By.XPATH, xp).click()
                time.sleep(0.4)
                return
            except Exception:
                pass
    try:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
    except Exception:
        pass

# ── Driver ────────────────────────────────────────────────────────────────────
def init_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--start-maximized")
    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    return d

# ── Google site: search ───────────────────────────────────────────────────────
def google_search_url(query: str, start: int) -> str:
    """Build a Google search URL. start is 0-based (0, 10, 20 …)."""
    return f"https://www.google.com/search?q={quote_plus(query)}&start={start}"

def collect_greenhouse_urls(driver, wait) -> list[str]:
    """
    Scrape all boards.greenhouse.io/*/jobs/* URLs visible on the current Google results page.
    Handles Google's CAPTCHA by waiting up to 60s for the user to solve it.
    """
    # Check for CAPTCHA
    if el_exists(driver, "//form[@id='captcha-form'] | //div[@id='recaptcha']", timeout=2):
        log.info("  Google CAPTCHA detected — solve it in the browser (60s).")
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='search']"))
            )
        except TimeoutException:
            log.warning("  CAPTCHA not solved in time — skipping this page.")
            return []

    urls = []
    # Result links live in <a> tags inside #search
    for a in driver.find_elements(By.XPATH, "//a[@href]"):
        href = a.get_attribute("href") or ""
        # Match boards.greenhouse.io/<company>/jobs/<id>
        if re.search(r"boards\.greenhouse\.io/[^/]+/jobs/\d+", href):
            # Strip Google redirect wrapper if present
            m = re.search(r"(https://boards\.greenhouse\.io/[^&\"]+)", href)
            if m:
                clean = m.group(1).split("#")[0]  # strip URL fragments (#:~:text=...)
                if clean not in urls:
                    urls.append(clean)
    return urls

# ── Job detail ────────────────────────────────────────────────────────────────
def parse_job_page(driver) -> dict:
    """Extract title, company, location, description from a boards.greenhouse.io job page."""
    title = safe_text(driver, "//h1", timeout=5)

    # Company name: try page title, DOM elements, then fall back to URL slug
    company = ""
    try:
        t = driver.title
        # "Job Title at Company | ..." or "Job Title - Company Careers"
        if " at " in t:
            company = t.split(" at ", 1)[-1].split("|")[0].split("-")[0].strip()
        elif "|" in t:
            company = t.split("|")[-1].strip()
        elif " - " in t:
            company = t.split(" - ")[-1].replace("Careers", "").strip()
    except Exception:
        pass
    if not company:
        company = safe_text(driver,
            "//div[contains(@class,'company-name')] | "
            "//a[contains(@class,'back')] | "
            "//h2[contains(@class,'company')]", timeout=1)
    if not company:
        # Extract slug from current URL: boards.greenhouse.io/<slug>/jobs/<id>
        slug_m = re.search(r"boards\.greenhouse\.io/([^/]+)/jobs/", driver.current_url)
        if slug_m:
            company = slug_m.group(1).replace("_", " ").replace("-", " ").title()

    location = safe_text(driver, "//div[contains(@class,'location')] | //*[@id='location']", timeout=2)

    # Description
    desc = ""
    for xp in [
        "//div[@id='content']",
        "//div[contains(@class,'job-description')]",
        "//div[contains(@class,'description')]",
        "//section",
    ]:
        try:
            el = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, xp)))
            desc = el.text.strip()
            if len(desc) > 200:
                break
        except Exception:
            pass

    low = desc.lower()
    remote_type = (
        "hybrid" if "remote" in low and ("hybrid" in low or "onsite" in low or "in-office" in low) else
        "remote" if "remote" in low else "onsite"
    )
    emp_type = (
        "full-time"  if "full-time" in low or "full time" in low else
        "part-time"  if "part-time" in low else
        "internship" if "intern" in low else
        "contract"   if "contract" in low else ""
    )
    salary_raw = ""
    m = re.search(r"\$[\d,]+(?:\s*[-–—]\s*\$[\d,]+)?(?:\s*/\s*(?:yr|hr|year|hour))?", desc)
    if m:
        salary_raw = m.group(0)

    # Extract job ID from URL
    job_id = ""
    id_m = re.search(r"/jobs/(\d+)", driver.current_url)
    if id_m:
        job_id = id_m.group(1)

    return {
        "job_id": job_id, "title": title, "company": company, "location": location,
        "description_full": desc[:8000], "remote_type": remote_type,
        "employment_type": emp_type, "salary_raw": salary_raw,
        "skills_mentioned": extract_skills(desc),
    }

# ── Application form filler ───────────────────────────────────────────────────
def fill_form(driver, wait):
    """Fill standard Greenhouse public application form fields."""

    def try_fill(xpaths: list[str], value: str):
        for xp in xpaths:
            if el_exists(driver, xp, timeout=1):
                try:
                    el = driver.find_element(By.XPATH, xp)
                    if not el.get_attribute("value"):
                        el.clear()
                        el.send_keys(value)
                    return
                except Exception:
                    pass

    # Name
    try_fill(["//input[@id='first_name']", "//input[@name='first_name']",
              "//input[@autocomplete='given-name']"], FULL_NAME.split()[0])
    try_fill(["//input[@id='last_name']", "//input[@name='last_name']",
              "//input[@autocomplete='family-name']"], FULL_NAME.split()[-1])

    # Email
    try_fill(["//input[@id='email']", "//input[@type='email']",
              "//input[@name='email']"], EMAIL)

    # Phone
    if PHONE:
        try_fill(["//input[@id='phone']", "//input[@type='tel']",
                  "//input[@name='phone']"], PHONE)

    # LinkedIn
    for xp in [
        "//input[contains(@id,'linkedin') or contains(@name,'linkedin')]",
        "//input[contains(translate(@placeholder,'LINKEDIN','linkedin'),'linkedin')]",
        "//label[contains(translate(.,'LINKEDIN','linkedin'),'linkedin')]/following::input[1]",
    ]:
        if el_exists(driver, xp, timeout=1):
            try:
                el = driver.find_element(By.XPATH, xp)
                if not el.get_attribute("value"):
                    el.send_keys(LINKEDIN_URL)
                break
            except Exception:
                pass

    # Resume upload
    if RESUME_PATH and os.path.isfile(RESUME_PATH):
        for xp in ["//input[@type='file'][1]"]:
            if el_exists(driver, xp, timeout=1):
                try:
                    driver.find_element(By.XPATH, xp).send_keys(RESUME_PATH)
                    time.sleep(2.0)
                except Exception:
                    pass
                break

    # Work auth radio buttons
    for grp in driver.find_elements(By.XPATH,
            "//div[contains(@class,'field') and .//input[@type='radio']]"):
        label_text = ""
        try:
            label_text = grp.find_element(By.XPATH, ".//*[not(self::input)]").text.lower()
        except Exception:
            pass

        if "sponsor" in label_text:
            answer = "no"
        elif any(kw in label_text for kw in ("authorized", "legally", "eligible", "right to work")):
            answer = "yes"
        else:
            answer = "yes"  # default generic questions to Yes

        try:
            radio = grp.find_element(
                By.XPATH,
                f".//label[contains(translate(normalize-space(.),'YESNO','yesno'),'{answer}')]"
            )
            driver.execute_script(_JS_CLICK, radio)
        except Exception:
            try:
                first = grp.find_elements(By.XPATH, ".//input[@type='radio']")
                if first:
                    driver.execute_script(_JS_CLICK, first[0])
            except Exception:
                pass

    # Select dropdowns
    for sel_el in driver.find_elements(By.XPATH, "//select"):
        try:
            sel = Select(sel_el)
            if sel_el.get_attribute("value"):
                continue
            try:
                sel.select_by_visible_text("Yes")
            except Exception:
                if len(sel.options) > 1:
                    sel.select_by_index(1)
        except Exception:
            pass

    # Generic website / portfolio inputs
    for inp in driver.find_elements(By.XPATH,
            "//input[@type='text' and (not(@value) or @value='')]"):
        try:
            ph = (inp.get_attribute("placeholder") or "").lower()
            label_for = inp.get_attribute("id") or ""
            label_text = ""
            try:
                label_text = driver.find_element(
                    By.XPATH, f"//label[@for='{label_for}']"
                ).text.lower()
            except Exception:
                pass
            combined = ph + label_text
            if any(kw in combined for kw in ("website", "portfolio", "personal site")):
                inp.send_keys(LINKEDIN_URL)
            elif any(kw in combined for kw in ("salary", "compensation", "expected")):
                inp.send_keys("100000")
        except Exception:
            pass

# ── Apply flow ────────────────────────────────────────────────────────────────
APPLY_BTN = (
    "//button[contains(normalize-space(),'Apply for this job')] | "
    "//a[contains(normalize-space(),'Apply for this job')] | "
    "//button[contains(normalize-space(),'Apply now')] | "
    "//a[contains(normalize-space(),'Apply now')] | "
    "//button[normalize-space()='Apply'] | "
    "//a[normalize-space()='Apply']"
)
EXTERNAL_BTN = (
    "//a[contains(@href,'http') and ("
    "contains(normalize-space(),'Apply on company') or "
    "contains(normalize-space(),'Apply externally') or "
    "contains(normalize-space(),'Visit job posting'))]"
)
SUBMIT_BTN = (
    "//button[normalize-space()='Submit Application'] | "
    "//button[normalize-space()='Submit'] | "
    "//input[@type='submit' and contains(@value,'Submit')] | "
    "//button[contains(normalize-space(),'Submit Application')] | "
    "//button[contains(normalize-space(),'Submit application')] | "
    "//button[@data-qa='btn-submit'] | "
    "//button[contains(@class,'submit')]"
)
NEXT_BTN = (
    "//button[normalize-space()='Next'] | "
    "//button[normalize-space()='Continue'] | "
    "//input[@type='submit' and @value='Next'] | "
    "//button[contains(normalize-space(),'Next step')] | "
    "//button[@data-qa='btn-next'] | "
    "//button[contains(@class,'next-btn')] | "
    "//button[contains(@class,'next') and @type='button']"
)
SUCCESS_XP = (
    "//*[contains(normalize-space(),'application has been submitted')] | "
    "//*[contains(normalize-space(),'successfully applied')] | "
    "//*[contains(normalize-space(),'Thank you for applying')] | "
    "//h1[contains(normalize-space(),'Thank you')]"
)


def apply_to_job(driver, wait) -> tuple[str, str]:
    """Navigate the apply flow. Returns (status, apply_type)."""

    # External redirect — skip
    if el_exists(driver, EXTERNAL_BTN, timeout=1):
        return "skipped_external", "external"

    if not el_exists(driver, APPLY_BTN, timeout=3):
        return "skipped_no_button", "unknown"

    apply_type = "full_form"

    if args.dry_run:
        return "dry_run", apply_type

    # Click the Apply button
    safe_click(driver, wait, APPLY_BTN)
    human_wait(1.0, 2.0)

    for step in range(1, MODAL_MAX_STEPS + 1):
        try:
            fill_form(driver, wait)
            human_wait(0.5, 1.0)

            if el_exists(driver, SUBMIT_BTN, timeout=2):
                safe_click(driver, wait, SUBMIT_BTN)
                human_wait(2.0, 3.0)
                if el_exists(driver, SUCCESS_XP, timeout=5):
                    log.info(f"    Applied (step {step})")
                    return "applied", apply_type
                # Page changed — assume success
                return "applied", apply_type

            if el_exists(driver, NEXT_BTN, timeout=2):
                safe_click(driver, wait, NEXT_BTN)
                human_wait(0.8, 1.5)
                continue

            # Last resort: any visible submit-type button or input
            fallback_btns = driver.find_elements(
                By.XPATH,
                "//button[@type='submit'] | //input[@type='submit'] | "
                "//button[contains(@class,'btn-primary') or contains(@class,'btn-submit')]"
            )
            if fallback_btns:
                log.info(f"    Fallback click on {fallback_btns[0].text.strip() or 'submit btn'}")
                driver.execute_script(_JS_CLICK, fallback_btns[0])
                human_wait(2.0, 3.0)
                if el_exists(driver, SUCCESS_XP, timeout=5):
                    return "applied", apply_type
                continue

            log.warning(f"    No Next/Submit at step {step}")
            break

        except Exception as e:
            log.error(f"    Form error at step {step}: {e}")
            break

    dismiss_modal(driver)
    return "error", apply_type

# ── Main ──────────────────────────────────────────────────────────────────────
def run():
    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Greenhouse via Google site: search  |  {args.google_pages} pages  |  {mode}")
    log.info(f"  Query: {GOOGLE_QUERY[:80]}...")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    wait   = WebDriverWait(driver, WAIT_SEC)
    counts: dict[str, int] = {}

    # ── Phase 1: collect all job URLs from Google ─────────────────────────────
    log.info("\n[Phase 1] Collecting job URLs from Google...")
    job_urls: list[str] = []

    for page_num in range(args.google_pages):
        start = page_num * RESULTS_PER_GOOGLE_PAGE
        gurl  = google_search_url(GOOGLE_QUERY, start)
        log.info(f"  Google page {page_num+1}/{args.google_pages}  (start={start})")

        driver.get(gurl)
        human_wait(2.0, 4.0)

        found = collect_greenhouse_urls(driver, wait)
        new   = [u for u in found if u not in job_urls]
        job_urls.extend(new)
        log.info(f"  Found {len(found)} links ({len(new)} new) — total: {len(job_urls)}")

        if not found:
            log.info("  No results on this page — stopping search.")
            break

        # Random pause between Google pages to avoid rate limiting
        time.sleep(random.uniform(3.0, 6.0))

    log.info(f"\n  Total unique Greenhouse job URLs: {len(job_urls)}")
    # Save URL list for reference
    with open(os.path.join(RUN_DIR, "job_urls.txt"), "w") as f:
        f.write("\n".join(job_urls))

    if not job_urls:
        log.warning("No job URLs found — Google may have blocked the search. "
                    "Try running again or solve the CAPTCHA manually.")
        driver.quit()
        return

    # ── Phase 2: apply to each job ────────────────────────────────────────────
    log.info(f"\n[Phase 2] Applying to {len(job_urls)} jobs...")

    for idx, url in enumerate(job_urls, 1):
        if url in _seen_urls:
            continue
        _seen_urls.add(url)

        log.info(f"\n  [{idx}/{len(job_urls)}] {url}")

        try:
            driver.get(url)
            human_wait(1.5, 2.5)

            detail = parse_job_page(driver)

            log.info(f"  Title:   {detail['title']}")
            log.info(f"  Company: {detail['company']}")
            log.info(f"  Loc:     {detail['location']}  |  {detail['remote_type']}")

            if title_is_excluded(detail["title"]):
                log.info("  Title excluded — skip")
                counts["skipped"] = counts.get("skipped", 0) + 1
                _records.append(GHJob(
                    job_id=detail["job_id"], title=detail["title"],
                    company=detail["company"], location=detail["location"],
                    status="skipped", url=url, note="title_excluded",
                    remote_type=detail["remote_type"],
                ))
                save_all()
                continue

            status, apply_type = apply_to_job(driver, wait)
            log.info(f"  → {apply_type}  |  {status}")
            counts[status] = counts.get(status, 0) + 1

            _records.append(GHJob(
                job_id=detail["job_id"],
                title=detail["title"],
                company=detail["company"],
                location=detail["location"],
                status=status,
                url=url,
                apply_type=apply_type,
                remote_type=detail["remote_type"],
                employment_type=detail["employment_type"],
                salary_raw=detail["salary_raw"],
                skills_mentioned=detail["skills_mentioned"],
                description_full=detail["description_full"],
            ))
            save_all()
            human_wait(1.0, 2.5)

        except Exception as e:
            log.error(f"  Error on {url}: {e}")
            counts["error"] = counts.get("error", 0) + 1
            dismiss_modal(driver)

    # ── Done ──────────────────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("DONE")
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

    log.info(f"  JSON     → {JSON_FILE}")
    log.info(f"  CSV      → {CSV_FILE}")
    log.info(f"  URL list → {os.path.join(RUN_DIR, 'job_urls.txt')}")
    log.info("=" * 60)

    try:
        driver.quit()
    except Exception:
        pass


if __name__ == "__main__":
    run()
