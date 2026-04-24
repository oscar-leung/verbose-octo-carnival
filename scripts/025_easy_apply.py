"""
LinkedIn Easy Apply — Automated Job Application Bot
Searches across keywords + pages, deduplicates jobs, and applies via Easy Apply.

Output per run:
  runs/linkedin_easy_apply_<ts>/
    run.log          — timestamped full log
    applied_jobs.csv — structured job records
    applied_jobs.json — same data, JSON format

Usage:
  python 025_easy_apply.py
"""

import csv
import json
import logging
import os
import random
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import date, datetime
from typing import Optional

import pyautogui
from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    InvalidSessionIdException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

# =============================================================================
# CONFIG
# =============================================================================
load_dotenv()
USERNAME     = os.getenv("LINKIN_USERNAME")
PASSWORD     = os.getenv("LINKIN_PASSWORD")
FULL_NAME    = "Oscar Leung"
LINKEDIN_URL = "https://www.linkedin.com/in/oscar-leung/"

# Single consolidated LinkedIn boolean search query (covers all target roles in one pass)
SEARCH_QUERY = "(software engineer OR qa OR AI OR Salesforce OR web)"

# Titles containing any of these words (case-insensitive) will be skipped before applying
TITLE_EXCLUDE = {
    "founding", "sr.", "sr ", " sr", "sales", "senior", "product", "robotics",
    "campus", "customer", "manager", "digital", "filmware", "lead", "field",
}

PAGES_PER_KEYWORD = 40   # 40 pages × 25 = ~1,000 jobs per run
JOBS_PER_PAGE     = 25
MODAL_MAX_STEPS   = 20   # bail if modal doesn't resolve after N steps
WAIT_SEC          = 10

# Run folder
RUN_ID   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR  = os.path.join("runs", f"linkedin_easy_apply_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)
LOG_FILE  = os.path.join(RUN_DIR, "run.log")
CSV_FILE  = os.path.join(RUN_DIR, "applied_jobs.csv")
JSON_FILE = os.path.join(RUN_DIR, "applied_jobs.json")

# Shared XPath selectors
EASY_BTN    = "//button[@id='jobs-apply-button-id']"
NEXT_BTN    = "//button[@aria-label='Continue to next step']"
REVIEW_BTN  = "//button[@aria-label='Review your application']"
SUBMIT_BTN  = "//button[@aria-label='Submit application']"
DISMISS_BTN = "//button[@aria-label='Dismiss']"

# =============================================================================
# LOGGING
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# =============================================================================
# DATA MODEL
# =============================================================================
@dataclass
class JobRecord:
    job_id:     str
    title:      str
    company:    str
    location:   str
    keyword:    str
    status:     str    # "applied" | "skipped" | "error"
    url:        str = ""
    note:       str = ""
    applied_at: str = field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# PERSISTENCE
# =============================================================================
_records: list[JobRecord] = []


def save_all():
    if not _records:
        return
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(JobRecord.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(asdict(r) for r in _records)
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in _records], f, indent=2, ensure_ascii=False)
    log.info(f"Saved {len(_records)} records → {RUN_DIR}")


# =============================================================================
# DRIVER
# =============================================================================
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
    driver.implicitly_wait(2)
    return driver


# =============================================================================
# HELPERS
# =============================================================================
HUMAN_DELAY_ENABLED = True


def human_wait(min_s=0.4, max_s=2.3, long_pause_chance=0.08, long_min=2.0, long_max=4.5):
    if not HUMAN_DELAY_ENABLED:
        return
    time.sleep(random.uniform(min_s, max_s))
    if random.random() < long_pause_chance:
        time.sleep(random.uniform(long_min, long_max))


def el_exists(driver, xpath: str) -> bool:
    return bool(driver.find_elements(By.XPATH, xpath))


def safe_click(driver, wait, xpath: str, pre=(0.2, 0.9), post=(0.2, 2.1)) -> bool:
    """Click element; returns True on success, False if not found/clickable."""
    human_wait(*pre)
    try:
        el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_wait(0.1, 0.4)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", el)
        human_wait(*post)
        return True
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
        return False


def xpath_literal(s: str) -> str:
    """Safely escape a string for use in XPath (handles apostrophes)."""
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    parts = s.split("'")
    return "concat(" + ",\"'\",".join(f"'{p}'" for p in parts) + ")"


# =============================================================================
# WINDOW SETUP (macOS)
# =============================================================================
def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)
    for _ in range(5):
        pyautogui.hotkey("command", "-")


def move_window_to_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey("ctrl", "option", "i")
    time.sleep(0.2)


# =============================================================================
# FORM FILLERS
# =============================================================================
WORK_AUTH_QUESTIONS = [
    {"text": "Are you willing to take a drug test, in accordance with local law/regulations?", "answer": "Yes"},
    {"text": "Will you now, or in the future, require sponsorship for employment visa status", "answer": "No"},
    {"text": "Do you have unrestricted right to work in the country in which this position is based?", "answer": "No"},
    {"text": "Excluding the transfer or extension of a currently valid H1B visa, will you now or in the future require sponsorship for employment authorization in the country in which this position is based?", "answer": "No"},
    {"text": "I am allowing Quantcast to contact me about future job opportunities for up to 1 year.", "answer": "Yes"},
    {"text": "Security Clearance", "answer": "None"},
    {"text": "What is your target salary range?", "answer": "100k-110k"},
    {"text": "Are you legally authorized to work in the United States WITHOUT employer sponsorship (i.e., C2C, H1B, EAD, OPT, F1 or TN) now or in the future?", "answer": "Yes"},
    {"text": "Are you comfortable commuting to this job's location?", "answer": "Yes"},
    {"text": "Are you comfortable working in a remote setting?", "answer": "Yes"},
    {"text": "Will you now or in the future require sponsorship for employment visa status?", "answer": "No"},
    {"text": "How did you hear about this job?", "answer": "LinkedIn"},
    {"text": "Part of the interview process will be in-person in our San Francisco office. If you are not currently based in the SF/Bay Area, you will not be considered for this position. Are you currently residing in the SF/Bay Area?", "answer": "Yes"},
]


def fill_work_authorization_questions(driver, wait):
    for q in WORK_AUTH_QUESTIONS:
        # Try radio button first
        try:
            radio_xpath = (
                f"//fieldset[.//legend[contains(normalize-space(.), {xpath_literal(q['text'])})]]"
                f"//label[@data-test-text-selectable-option__label={xpath_literal(q['answer'])}]"
            )
            el = driver.find_element(By.XPATH, radio_xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            continue
        except Exception:
            pass

        # Try <select> dropdown
        try:
            label_el = driver.find_element(
                By.XPATH, f"//label[contains(normalize-space(.), {xpath_literal(q['text'])})]"
            )
            sel_id = label_el.get_attribute("for")
            sel_el = driver.find_element(By.ID, sel_id)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", sel_el)
            Select(sel_el).select_by_visible_text(q["answer"])
        except Exception:
            pass

    # "I agree" checkbox
    try:
        el = driver.find_element(
            By.XPATH, "//label[@data-test-text-selectable-option__label='I agree']"
        )
        driver.execute_script("arguments[0].click();", el)
    except Exception:
        pass


def fill_voluntary_self_id(driver, wait):
    try:
        Select(wait.until(EC.element_to_be_clickable((
            By.XPATH, "//label[.//strong[normalize-space()='Gender']]/following::select[1]"
        )))).select_by_visible_text("Male")
    except Exception:
        pass

    try:
        Select(wait.until(EC.element_to_be_clickable((
            By.XPATH, "//label[.//strong[normalize-space()='Race/Ethnicity']]/following::select[1]"
        )))).select_by_visible_text("Asian (Not Hispanic or Latino)")
    except Exception:
        pass

    for opt_text, sel_xpath in [
        ("I am not a protected veteran",
         "(//select[.//option[normalize-space()='I am not a protected veteran']])[1]"),
        ("No, I do not have a disability and have not had one in the past",
         "(//select[.//option[normalize-space()='No, I do not have a disability and have not had one in the past']])[1]"),
    ]:
        try:
            Select(driver.find_element(By.XPATH, sel_xpath)).select_by_visible_text(opt_text)
        except Exception:
            pass

    try:
        inp = driver.find_element(By.XPATH, "//label[normalize-space()='Your Name']/following::input[1]")
        inp.clear(); inp.send_keys(FULL_NAME)
    except Exception:
        pass

    try:
        inp = driver.find_element(By.XPATH, "//label[normalize-space()=\"Today's Date\"]/following::input[1]")
        inp.clear(); inp.send_keys(date.today().strftime("%m/%d/%Y"))
    except Exception:
        pass

    try:
        boxes = driver.find_elements(
            By.XPATH,
            "//input[@data-test-text-selectable-option__input='Confirmed' and @type='checkbox']",
        )
        for cb in boxes[:2]:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
            if not cb.is_selected():
                driver.execute_script("arguments[0].click();", cb)
    except Exception:
        pass


def fill_additional_questions(driver, wait):
    """Fill numeric inputs with '1', selects with 'Yes', then work auth questions."""
    containers = driver.find_elements(By.XPATH, "//div[@class='ph5']/div[1]/div")
    for box in containers:
        try:
            inp = box.find_element(By.XPATH, ".//input")
            inp.clear(); inp.send_keys("1")
        except Exception:
            pass
        try:
            Select(box.find_element(By.XPATH, ".//select")).select_by_visible_text("Yes")
        except Exception:
            pass
    fill_work_authorization_questions(driver, wait)


# =============================================================================
# MODAL DISPATCH LOOP
# =============================================================================

# Map heading text → optional filler function (driver, wait) -> None
_STEP_HANDLERS = {
    "Contact info":                   None,
    "Resume":                         None,
    "Work experience":                None,
    "Education":                      None,
    "Screening questions":            None,
    "Privacy policy":                 lambda d, w: safe_click(
        d, w, "//label[@data-test-text-selectable-option__label='I Agree Terms & Conditions']",
        pre=(0.1, 0.3), post=(0.2, 0.5)
    ),
    "Additional Questions":           fill_additional_questions,
    "Work authorization":             fill_work_authorization_questions,
    "Voluntary self identification":  fill_voluntary_self_id,
}


def _fill_resume_linkedin(driver, wait):
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


def _current_modal_heading(driver) -> str:
    try:
        els = driver.find_elements(By.XPATH, "//div[@data-test-modal]//h3")
        return els[0].text.strip() if els else ""
    except Exception:
        return ""


def _fill_home_city(driver):
    if el_exists(driver, "//input[contains(@id,'city-HOME-CITY')]"):
        try:
            inp = driver.find_element(By.XPATH, "//input[contains(@id,'city-HOME-CITY')]")
            inp.send_keys("Santa Clara")
            os.system("osascript -e 'tell application \"Google Chrome\" to activate'")
            time.sleep(0.8)
            pyautogui.press("down")
            pyautogui.press("enter")
            time.sleep(0.5)
        except Exception:
            pass


def advance_modal(driver, wait) -> bool:
    """
    Detect current modal step, fill it, then click Next/Review/Submit.
    Returns True if the application was submitted.
    Raises RuntimeError if no advance button is found.
    """
    heading = _current_modal_heading(driver)
    log.debug(f"    modal heading: {heading!r}")

    # Run the step-specific filler
    for h_text, handler in _STEP_HANDLERS.items():
        if h_text.lower() in heading.lower():
            if h_text == "Resume":
                _fill_resume_linkedin(driver, wait)
            elif handler:
                try:
                    handler(driver, wait)
                except Exception as e:
                    log.warning(f"    handler '{h_text}' raised: {e}")
            break

    # Always check for home-city autocomplete
    _fill_home_city(driver)

    # Advance: Review → Submit → Dismiss | Submit | Next
    if el_exists(driver, REVIEW_BTN):
        safe_click(driver, wait, REVIEW_BTN)
        human_wait(0.5, 1.2)
        if el_exists(driver, SUBMIT_BTN):
            safe_click(driver, wait, SUBMIT_BTN, pre=(0.4, 1.2), post=(1.5, 2.5))
            _dismiss_post_apply(driver, wait)
            return True
        return False

    if el_exists(driver, SUBMIT_BTN):
        safe_click(driver, wait, SUBMIT_BTN, pre=(0.4, 1.2), post=(1.5, 2.5))
        _dismiss_post_apply(driver, wait)
        return True

    if el_exists(driver, NEXT_BTN):
        safe_click(driver, wait, NEXT_BTN)
        return False

    raise RuntimeError("No advance button found (Review / Submit / Next)")


def _dismiss_post_apply(driver, wait):
    """Close whatever confirmation dialog appears after submitting."""
    for xpath in [
        DISMISS_BTN,
        "//button[@aria-label='Done']",
        "//div[@role='alertdialog']//button[@data-control-name='discard_application_confirm_btn']",
    ]:
        try:
            el = WebDriverWait(driver, 4).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            driver.execute_script("arguments[0].click();", el)
            time.sleep(0.5)
            return
        except Exception:
            pass


def _emergency_close(driver, wait):
    """Abandon current application and close the modal."""
    safe_click(driver, wait, DISMISS_BTN, pre=(0.1, 0.3), post=(0.3, 0.8))
    time.sleep(0.4)
    safe_click(
        driver, wait,
        "//div[@role='alertdialog']//button[@data-control-name='discard_application_confirm_btn']",
        pre=(0.1, 0.3), post=(0.3, 0.8),
    )


def run_easy_apply(driver, wait) -> str:
    """
    Drive the full Easy Apply modal for the currently selected job.
    Returns "applied" | "skipped" | "error".
    """
    if not safe_click(driver, wait, EASY_BTN, pre=(0.3, 0.8), post=(0.8, 1.5)):
        return "skipped"

    for step in range(1, MODAL_MAX_STEPS + 1):
        try:
            submitted = advance_modal(driver, wait)
            if submitted:
                log.info(f"    Applied (step {step})")
                return "applied"
            human_wait(0.5, 1.5)
        except RuntimeError as e:
            log.warning(f"    Stuck at step {step}: {e}")
            _emergency_close(driver, wait)
            return "error"
        except Exception as e:
            log.error(f"    Unexpected modal error step {step}: {e}")
            _emergency_close(driver, wait)
            return "error"

    log.warning(f"    Modal exceeded {MODAL_MAX_STEPS} steps, aborting.")
    _emergency_close(driver, wait)
    return "error"


# =============================================================================
# JOB METADATA
# =============================================================================
def get_job_metadata(driver, job_el) -> dict:
    job_id = job_el.get_attribute("data-occludable-job-id") or ""
    try:
        title = job_el.find_element(
            By.XPATH, ".//a[contains(@class,'job-card-container__link')]"
        ).text.strip()
    except Exception:
        title = ""
    try:
        company = job_el.find_element(
            By.XPATH, ".//span[contains(@class,'job-card-container__primary-description')]"
        ).text.strip()
    except Exception:
        company = ""
    try:
        location = job_el.find_element(
            By.XPATH, ".//li[contains(@class,'job-card-container__metadata-item')]"
        ).text.strip()
    except Exception:
        location = ""
    url = f"https://www.linkedin.com/jobs/view/{job_id}/" if job_id else ""
    return {"job_id": job_id, "title": title, "company": company, "location": location, "url": url}


# =============================================================================
# SEARCH URL + PAGE COLLECTION
# =============================================================================
def search_url(query: str, start: int) -> str:
    from urllib.parse import quote_plus
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(query)}&f_LF=f_AL&start={start}"

def title_is_excluded(title: str) -> bool:
    low = title.lower()
    return any(tok in low for tok in TITLE_EXCLUDE)


def collect_jobs_on_page(driver) -> list:
    try:
        WebDriverWait(driver, WAIT_SEC).until(
            EC.presence_of_element_located((By.XPATH, "//li[@data-occludable-job-id]"))
        )
    except TimeoutException:
        return []
    return driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")


# =============================================================================
# LOGIN
# =============================================================================
def login(driver, wait):
    driver.get("https://www.linkedin.com/login")
    zoom_out()
    move_window_to_topright()
    time.sleep(2)
    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    safe_click(driver, wait, "//button[@type='submit']")
    time.sleep(3)
    log.info("Logged in to LinkedIn")


# =============================================================================
# MAIN
# =============================================================================
def run():
    log.info("=" * 60)
    log.info(f"  LinkedIn Easy Apply  |  query: {SEARCH_QUERY[:60]}  |  {PAGES_PER_KEYWORD} pages")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()
    wait   = WebDriverWait(driver, WAIT_SEC)

    counts   = {"applied": 0, "skipped": 0, "error": 0}
    seen_ids: set[str] = set()

    try:
        login(driver, wait)

        for page in range(PAGES_PER_KEYWORD):
            start = page * JOBS_PER_PAGE
            url   = search_url(SEARCH_QUERY, start)
            log.info(f"  Page {page+1} (start={start})")

            try:
                driver.get(url)
                human_wait(1.5, 3.0)
            except InvalidSessionIdException:
                log.error("Chrome session lost — saving and exiting.")
                raise

            job_els = collect_jobs_on_page(driver)
            if not job_els:
                log.info(f"  Page {page+1}: no jobs — stopping.")
                break

            log.info(f"  Page {page+1}: {len(job_els)} jobs")

            for idx, job_el in enumerate(job_els):
                try:
                    meta   = get_job_metadata(driver, job_el)
                    job_id = meta["job_id"]

                    if not job_id or job_id in seen_ids:
                        log.debug(f"  [{idx+1}] Duplicate/no ID — skip")
                        continue
                    seen_ids.add(job_id)

                    # Title exclusion filter
                    if title_is_excluded(meta.get("title", "")):
                        log.info(f"  [{idx+1}] Title excluded: {meta['title']}")
                        counts["skipped"] += 1
                        _records.append(JobRecord(
                            job_id=job_id,
                            title=meta.get("title", ""),
                            company=meta.get("company", ""),
                            location=meta.get("location", ""),
                            keyword=SEARCH_QUERY,
                            status="skipped",
                            note="title_excluded",
                            url=meta.get("url", ""),
                        ))
                        continue

                    log.info(f"  [{idx+1}/{len(job_els)}] {meta['title']} @ {meta['company']}")

                    driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});", job_el
                    )
                    try:
                        job_el.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", job_el)
                    human_wait(1.0, 2.5)

                    if not el_exists(driver, EASY_BTN):
                        log.info("    No Easy Apply button — skipping")
                        status = "skipped"
                    else:
                        status = run_easy_apply(driver, wait)

                    counts[status] += 1
                    _records.append(JobRecord(
                        job_id=job_id,
                        title=meta.get("title", ""),
                        company=meta.get("company", ""),
                        location=meta.get("location", ""),
                        keyword=SEARCH_QUERY,
                        status=status,
                        url=meta.get("url", ""),
                    ))
                    human_wait(0.8, 2.0)

                except InvalidSessionIdException:
                    log.error("Chrome session lost mid-job — saving and exiting.")
                    raise
                except StaleElementReferenceException:
                    log.warning(f"  [{idx+1}] Stale element — skip")
                    counts["error"] += 1
                except Exception as e:
                    log.error(f"  [{idx+1}] Error: {e}")
                    counts["error"] += 1
                    _emergency_close(driver, wait)

    except (InvalidSessionIdException, WebDriverException):
        pass
    finally:
        save_all()
        try:
            driver.quit()
        except Exception:
            pass

    log.info("=" * 60)
    log.info(
        f"  DONE  |  applied={counts['applied']}"
        f"  skipped={counts['skipped']}"
        f"  error={counts['error']}"
    )
    log.info(f"  Total unique jobs seen: {len(seen_ids)}")
    log.info(f"  Run folder: {RUN_DIR}")

    # ── Sync to Google Sheets ──────────────────────────────────────────────────
    try:
        import sys as _sys, os as _os
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from library.gsheets import sync_jobs
        sync_jobs([asdict(r) for r in _records], platform="LinkedIn")
        log.info("  Synced to Google Sheets.")
    except Exception as _gs_err:
        log.warning(f"  Google Sheets sync skipped: {_gs_err}")

    log.info("=" * 60)


if __name__ == "__main__":
    run()
