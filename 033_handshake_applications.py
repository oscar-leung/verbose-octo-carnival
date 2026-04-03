import logging
import random
import time
import json
import os
import re
import csv
from collections import Counter
from datetime import datetime
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

# ── Config ────────────────────────────────────────────────────────────────────
TOTAL_PAGES      = 400   # 400 pages × 25 jobs = ~10,000 jobs
JOBS_PER_PAGE    = 25
AUTO_APPLY       = True  # Set False to scrape-only without applying
APPLY_PAUSE_MIN  = 1.5
APPLY_PAUSE_MAX  = 3.5

COVER_LETTER_NAME = "HandShake Cover Letter"
TRANSCRIPT_NAME   = "0JH7198571 | SJSU Transcript | Oscar Leung"

# ── Run folder setup ──────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", RUN_ID)
os.makedirs(RUN_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(RUN_DIR, "run.log")),
        logging.StreamHandler(),
    ],
)

DATA_FILE = os.path.join(RUN_DIR, "jobs.json")
CSV_FILE  = os.path.join(RUN_DIR, "jobs.csv")
all_jobs: list[dict] = []

# CSV columns (defined once so header matches rows)
CSV_COLUMNS = [
    "page", "index", "job_id", "url",
    "title", "company", "industry",
    "location_raw", "city", "state", "country", "remote_type",
    "salary_raw", "salary_min", "salary_max", "salary_unit",
    "job_type", "employment_type",
    "deadline_raw", "deadline_date",
    "posted_raw",
    "work_auth_required", "visa_sponsorship",
    "description_full",
    "skills_mentioned",
    "qualifications_raw",
    "benefits_raw",
    "company_size", "company_location",
    "status", "timestamp",
]

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(all_jobs, f, indent=2)
    # Write / overwrite CSV
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(all_jobs)

logging.info(f"Run ID: {RUN_ID}  →  {RUN_DIR}/")

# ── Parsing helpers ───────────────────────────────────────────────────────────

def parse_salary(raw: str) -> dict:
    """Extract min/max/unit from strings like '$75–90K/yr' or '$40-120/hr'."""
    result = {"salary_min": None, "salary_max": None, "salary_unit": None}
    if not raw:
        return result
    unit_match = re.search(r"/(yr|hr|mo|month|year|hour)", raw, re.I)
    result["salary_unit"] = unit_match.group(1).lower() if unit_match else None

    nums = re.findall(r"[\d,]+\.?\d*", raw.replace(",", ""))
    multiplier = 1000 if "K" in raw or "k" in raw else 1
    if len(nums) >= 2:
        result["salary_min"] = float(nums[0]) * multiplier
        result["salary_max"] = float(nums[1]) * multiplier
    elif len(nums) == 1:
        result["salary_min"] = float(nums[0]) * multiplier
    return result


def parse_location(raw: str) -> dict:
    """Split 'Onsite, based in Redlands, CA' into components."""
    result = {"city": None, "state": None, "country": "United States", "remote_type": None}
    if not raw:
        return result
    low = raw.lower()
    if "remote" in low and "onsite" in low:
        result["remote_type"] = "hybrid"
    elif "remote" in low:
        result["remote_type"] = "remote"
    else:
        result["remote_type"] = "onsite"

    # Try to extract city/state from patterns like "based in City, ST" or "City, ST"
    m = re.search(r"(?:based in\s+)?([A-Za-z\s\.]+),\s*([A-Z]{2})", raw)
    if m:
        result["city"]  = m.group(1).strip()
        result["state"] = m.group(2).strip()
    return result


def parse_deadline(raw: str) -> str | None:
    """Extract ISO date from 'Apply by May 1, 2026 at 11:59 PM'."""
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", raw)
    if m:
        try:
            return datetime.strptime(m.group(1).replace(",", ""), "%B %d %Y").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "sql",
    "postgresql", "mysql", "mongodb", "aws", "azure", "gcp", "docker",
    "kubernetes", "git", "ci/cd", "rest", "graphql", "machine learning",
    "deep learning", "pytorch", "tensorflow", "llm", "rag", "langchain",
    "c++", "c#", "golang", "rust", "swift", "kotlin", "flutter",
    "html", "css", "django", "flask", "fastapi", "spring", "rails",
    "terraform", "linux", "bash", "agile", "scrum",
]

def extract_skills(text: str) -> str:
    """Return comma-separated skills found in text."""
    text_low = text.lower()
    found = [s for s in COMMON_SKILLS if s in text_low]
    return ", ".join(found)


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

def clickWebElement(xpath, timeout=5):
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.click()
        logging.info(f"  ✓ Clicked: {xpath[:80]}")
    except Exception as e:
        logging.error(f"  ✗ Click failed [{xpath[:60]}]: {type(e).__name__}")

def element_exists(xpath, timeout=2):
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except Exception:
        return False

def safe_text(xpath, timeout=3) -> str:
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return el.text.strip()
    except Exception:
        return ""

def safe_texts(xpath, timeout=3) -> list[str]:
    try:
        els = WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(By.XPATH, xpath)
        )
        return [e.text.strip() for e in els if e.text.strip()]
    except Exception:
        return []

def close_modal():
    for xp in ["//button[@aria-label='Cancel application']", "//button[@aria-label='Close']"]:
        if element_exists(xp, timeout=1):
            try:
                clickWebElement(xp)
                time.sleep(0.4)
                return
            except Exception:
                pass

def get_current_job_id() -> str:
    """Extract job ID from the current URL."""
    url = driver.current_url
    m = re.search(r"/jobs/(\d+)", url)
    return m.group(1) if m else ""

def expand_description():
    """Click 'More' button if present to get full job description."""
    more_xpath = "//button[contains(@aria-label, 'Show more')]"
    if element_exists(more_xpath, timeout=2):
        try:
            clickWebElement(more_xpath)
            time.sleep(0.5)
        except Exception:
            pass

def collect_job_data(index: int, page: int) -> dict:
    expand_description()

    job_id  = get_current_job_id()
    url     = f"https://app.joinhandshake.com/jobs/{job_id}" if job_id else driver.current_url

    title       = safe_text("//h1[contains(@class,'job-title')] | //h1[contains(@class,'dmTfkw')]")
    company     = safe_text("//div[contains(@class,'gBthqB')] | //*[contains(@data-hook,'employer-name')]")
    industry    = safe_text("//div[contains(@class,'hrTUzH')] | //*[contains(@data-hook,'employer-industry')]")
    posted_raw  = safe_text("//*[contains(@class,'fsLGJY')] | //*[contains(@data-hook,'posted-date')]")

    # At a glance fields
    salary_raw  = safe_text("//*[contains(@class,'dVnqLS')][1]")
    location_raw= safe_text("//*[contains(@class,'dVnqLS')][2]")
    job_type    = safe_text("//*[contains(@class,'dVnqLS')][3]")

    # Work auth / visa
    work_auth_raw = safe_text("//*[@data-hook='work-auth-title']")
    work_auth_required = "yes" if "required" in work_auth_raw.lower() else "no" if work_auth_raw else ""
    visa_sponsorship   = "yes" if "sponsor" in (safe_text("//*[contains(normalize-space(),'visa sponsor')]") or "").lower() else "no"

    # Full description
    desc_full = safe_text("//*[contains(@data-hook,'job-description')] | //div[contains(@style,'overflow-wrap')]", timeout=4)
    if len(desc_full) < 200:
        desc_full = safe_text("//div[contains(@class,'hkJwbQ')][2]//div", timeout=3)

    # Deadline from posted line
    deadline_raw = ""
    if "Apply by" in posted_raw:
        deadline_raw = posted_raw
    else:
        deadline_raw = safe_text("//*[contains(normalize-space(),'Apply by')]", timeout=2)

    # Benefits / what this job offers
    benefits_list = safe_texts("//ul[contains(@class,'dpqcEU')]//li")
    benefits_raw  = " | ".join(benefits_list)

    # Qualifications
    qual_list = safe_texts("//*[contains(@class,'dsAqlh')]")
    qualifications_raw = " | ".join(qual_list)

    # Company info
    company_size     = safe_text("//*[contains(@class,'jCQffL')][1]", timeout=2)
    company_location = safe_text("//*[contains(@class,'jCQffL')][2]//p", timeout=2)

    # Parse structured fields
    sal   = parse_salary(salary_raw)
    loc   = parse_location(location_raw)
    dl    = parse_deadline(deadline_raw)
    skills = extract_skills(desc_full)

    return {
        "page": page, "index": index,
        "job_id": job_id, "url": url,
        "title": title, "company": company, "industry": industry,
        "location_raw": location_raw,
        **loc,
        "salary_raw": salary_raw,
        **sal,
        "job_type": job_type,
        "employment_type": "full-time" if "full" in job_type.lower() else
                           "internship" if "intern" in job_type.lower() else
                           "part-time"  if "part"  in job_type.lower() else job_type.lower(),
        "deadline_raw": deadline_raw, "deadline_date": dl,
        "posted_raw": posted_raw,
        "work_auth_required": work_auth_required,
        "visa_sponsorship": visa_sponsorship,
        "description_full": desc_full[:5000],   # cap at 5k chars
        "skills_mentioned": skills,
        "qualifications_raw": qualifications_raw,
        "benefits_raw": benefits_raw,
        "company_size": company_size,
        "company_location": company_location,
        "status": "pending",
        "timestamp": datetime.now().isoformat(),
    }


# ── Document attachment ───────────────────────────────────────────────────────

def attach_document(placeholder_text: str, doc_name: str):
    already_xpath = f"//input[@placeholder='{placeholder_text}']/ancestor::div[3]//h2"
    if element_exists(already_xpath, timeout=1):
        return

    search_xpath = f"//input[@placeholder='{placeholder_text}']"
    if not element_exists(search_xpath, timeout=1):
        return

    try:
        box = driver.find_element(By.XPATH, search_xpath)
        box.click()
        box.send_keys(doc_name[:12])
        time.sleep(1.0)
        opt = f"//*[@role='option'][contains(normalize-space(), '{doc_name[:20]}')]"
        if element_exists(opt, timeout=2):
            clickWebElement(opt)
            logging.info(f"    📎 Attached: {doc_name[:40]}")
        else:
            logging.warning(f"    ⚠ No dropdown match for: {doc_name[:40]}")
    except Exception as e:
        logging.warning(f"    ⚠ Attach error [{placeholder_text}]: {e}")


# ── Login ─────────────────────────────────────────────────────────────────────

load_dotenv()
username = os.getenv('handshake_email')
password = os.getenv('handshake_password')

driver = webdriver.Chrome()
wait   = WebDriverWait(driver, 5)

driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
zoom_out()
move_window_to_topright()

driver.find_element(By.ID, "email-address-identifier").send_keys(username)
clickWebElement("//button[normalize-space()='Next']")
clickWebElement("//a[normalize-space()='Log in another way']")
driver.find_element(By.ID, "password").send_keys(password)
clickWebElement("//button[normalize-space()='Log in']")
time.sleep(3)

# Navigate to job listings
driver.get("https://app.joinhandshake.com/job-search/")
time.sleep(2)

# ── Main pagination loop ──────────────────────────────────────────────────────

for page in range(1, TOTAL_PAGES + 1):
    logging.info(f"\n{'='*60}")
    logging.info(f"  PAGE {page}/{TOTAL_PAGES}  |  Jobs collected so far: {len(all_jobs)}")
    logging.info(f"{'='*60}")

    if page > 1:
        next_btn = f"//button[@value='{page}' and not(@aria-current='page')]"
        if not element_exists(next_btn, timeout=4):
            logging.info(f"No page {page} button — stopping.")
            break
        clickWebElement(next_btn)
        time.sleep(random.uniform(1.5, 2.5))

    cards = driver.find_elements(
        By.XPATH,
        "//div[@aria-label='Jobs List']/div[3]/div[contains(@data-hook,'job-result-card')]"
    )
    n = len(cards)
    logging.info(f"Found {n} cards on page {page}")

    for idx in range(n):
        job_data = {
            "page": page, "index": idx + 1,
            "status": "pending", "timestamp": datetime.now().isoformat()
        }
        try:
            all_cards = driver.find_elements(
                By.XPATH,
                "//div[@aria-label='Jobs List']/div[3]/div[contains(@data-hook,'job-result-card')]"
            )
            if idx >= len(all_cards):
                logging.warning(f"Card {idx+1} disappeared — skipping")
                continue

            link = all_cards[idx].find_element(By.XPATH, ".//a[@role='button']")
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            link.click()
            time.sleep(random.uniform(0.8, 1.6))

            # ── Collect rich metadata ──
            job_data = collect_job_data(idx + 1, page)
            logging.info(
                f"  [{idx+1}/{n}] {job_data['title'][:45]} @ {job_data['company'][:25]}"
                f"  |  {job_data['salary_raw']}  |  {job_data['location_raw'][:30]}"
            )

            # ── Already applied / withdrawn ──
            already_xpath = (
                "//button[contains(normalize-space(),'Withdraw application')] | "
                "//*[contains(normalize-space(),'Application withdrawn')] | "
                "//*[contains(normalize-space(),'You already applied')]"
            )
            if element_exists(already_xpath, timeout=1):
                logging.info("    ↩ Already applied/withdrawn — skipping")
                job_data["status"] = "skipped_already_applied"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── External apply ──
            ext_xpath = (
                "//button[contains(@aria-label,'Apply externally')] | "
                "//button[.//span[normalize-space()='Apply externally']]"
            )
            if element_exists(ext_xpath, timeout=1):
                logging.info("    🌐 External apply — skipping")
                job_data["status"] = "skipped_external"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── No apply button ──
            apply_xpath = (
                "//button[@aria-label='Apply'] | "
                "//button[.//span[normalize-space()='Apply']]"
            )
            if not element_exists(apply_xpath, timeout=2):
                logging.info("    ✗ No Apply button — skipping")
                job_data["status"] = "skipped_no_button"
                all_jobs.append(job_data)
                save_data()
                continue

            if not AUTO_APPLY:
                job_data["status"] = "scraped_only"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── Open modal ──
            clickWebElement(apply_xpath)
            time.sleep(random.uniform(0.8, 1.4))

            # ── Attach docs ──
            if element_exists("//input[@placeholder='Search your cover letters']", timeout=2):
                attach_document("Search your cover letters", COVER_LETTER_NAME)
                time.sleep(0.4)

            if element_exists("//input[@placeholder='Search your transcripts']", timeout=2):
                attach_document("Search your transcripts", TRANSCRIPT_NAME)
                time.sleep(0.4)

            # ── Submit ──
            submit_xpath = "//button[normalize-space()='Submit Application']"
            if not element_exists(submit_xpath, timeout=3):
                logging.warning("    ✗ Submit button missing — closing modal")
                close_modal()
                job_data["status"] = "skipped_no_submit_button"
                all_jobs.append(job_data)
                save_data()
                continue

            clickWebElement(submit_xpath)
            logging.info("    ✅ Application submitted!")
            job_data["status"] = "applied"
            time.sleep(random.uniform(APPLY_PAUSE_MIN, APPLY_PAUSE_MAX))

        except Exception as e:
            logging.error(f"  Job #{idx+1} error: {type(e).__name__}: {e}")
            try:
                close_modal()
            except Exception:
                pass
            job_data["status"] = "error"

        all_jobs.append(job_data)
        save_data()

    # Checkpoint summary every page
    counts = Counter(j["status"] for j in all_jobs)
    logging.info(f"  Checkpoint after page {page}: {dict(counts)}")
    time.sleep(random.uniform(2.0, 3.5))

# ── Final summary ─────────────────────────────────────────────────────────────
logging.info("\n" + "="*60)
logging.info("DONE")
logging.info(f"Total jobs processed: {len(all_jobs)}")
counts = Counter(j["status"] for j in all_jobs)
for status, n in sorted(counts.items()):
    logging.info(f"  {status:<35} {n:>5}")
logging.info(f"\nJSON  → {DATA_FILE}")
logging.info(f"CSV   → {CSV_FILE}")
logging.info(f"Log   → {os.path.join(RUN_DIR, 'run.log')}")

driver.quit()