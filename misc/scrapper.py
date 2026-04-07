"""
Workday Career Page Scraper
Loops through all configured companies, searches by keyword, paginates,
deduplicates, and saves results to a timestamped CSV + log.

Usage:
    python scrapper.py
"""

import os
import csv
import sys
import time
import random
import logging
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException,
    ElementClickInterceptedException, ElementNotInteractableException,
    WebDriverException,
)

# ==============================================================================
# ⚙️  CONFIG
# ==============================================================================
load_dotenv()

EMAIL    = os.getenv("handshake_email")
PASSWORD = os.getenv("handshake_password")

KEYWORDS = [
    "QA Engineer",
    "Quality Assurance",
    "SDET",
    "Automation Engineer",
    "Software Engineer",
]

WAIT_SEC = 15
RUN_ID   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR  = os.path.join(os.path.dirname(__file__), "..", "runs", f"workday_{RUN_ID}")
os.makedirs(RUN_DIR, exist_ok=True)

OUTPUT_FILE = os.path.join(RUN_DIR, "jobs.csv")
LOG_FILE    = os.path.join(RUN_DIR, "run.log")

WORKDAY_COMPANIES = {
    "Intel":              "https://intel.wd1.myworkdayjobs.com/en-US/External",
    "Maxar":              "https://maxar.wd1.myworkdayjobs.com/Maxar",
    "NVIDIA":             "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "Applied Materials":  "https://amat.wd1.myworkdayjobs.com/External",
    "Adobe":              "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/jobs",
    "Zoom":               "https://zoom.wd5.myworkdayjobs.com/Zoom/",
    "KLA":                "https://kla.wd1.myworkdayjobs.com/en-US/Search/",
    "Rakuten":            "https://rakuten.wd1.myworkdayjobs.com/en-US/RakutenRewards",
    "Dicks Sporting Goods": "https://dickssportinggoods.wd1.myworkdayjobs.com/en-US/DSG",
    "Leidos":             "https://leidos.wd5.myworkdayjobs.com/en-US/External",
    "Broadcom":           "https://broadcom.wd1.myworkdayjobs.com/en-US/External_Career/userHome",
    "Ring Central":       "https://ringcentral.wd1.myworkdayjobs.com/en-US/RingCentral_Careers/userHome",
    "eBay":               "https://ebay.wd5.myworkdayjobs.com/en-US/apply/userHome",
    "SailPoint":          "https://sailpoint.wd1.myworkdayjobs.com/en-US/SailPoint/userHome",
    "Campbell Soup":      "https://campbellsoup.wd5.myworkdayjobs.com/en-US/ExternalCareers_GlobalSite/userHome",
    "Disney":             "https://disney.wd5.myworkdayjobs.com/en-US/disneycareer/userHome",
    "Twitter/X":          "https://twitter.wd5.myworkdayjobs.com/en-US/X/userHome",
    "Snapchat":           "https://wd1.myworkdaysite.com/en-US/recruiting/snapchat/snap/userHome",
    "Abbott":             "https://abbott.wd5.myworkdayjobs.com/en-US/abbottcareers/userHome",
    "Credit Acceptance":  "https://creditacceptance.wd5.myworkdayjobs.com/en-US/Credit_Acceptance",
    "General Motors":     "https://generalmotors.wd5.myworkdayjobs.com/en-US/Careers_GM/userHome",
    "Humana":             "https://humana.wd5.myworkdayjobs.com/en-US/Humana_External_Career_Site/userHome",
    "Key Bank":           "https://keybank.wd5.myworkdayjobs.com/en-US/External_Career_Site/userHome",
    "TransUnion":         "https://transunion.wd5.myworkdayjobs.com/en-US/TransUnion/userHome",
    "Home Depot":         "https://homedepot.wd5.myworkdayjobs.com/en-US/CareerDepot/userHome",
    "Dataminr":           "https://dataminr.wd12.myworkdayjobs.com/en-US/Dataminr/userHome",
    "Tinuiti":            "https://tinuiti.wd12.myworkdayjobs.com/en-US/Tinuiti/userHome",
    "BMO":                "https://bmo.wd3.myworkdayjobs.com/en-US/External/userHome",
    "Inmar":              "https://inmar.wd1.myworkdayjobs.com/en-US/inmarcareers/userHome",
    "Transunion":         "https://transunion.wd5.myworkdayjobs.com/en-US/TransUnion/userHome",
    "Public Consulting":  "https://pcg.wd1.myworkdayjobs.com/en-US/PCG_External_Careers/",
}

# ==============================================================================
# 📝  LOGGING
# ==============================================================================
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


# ==============================================================================
# 📊  DATA MODEL
# ==============================================================================
@dataclass
class JobRecord:
    company:    str
    title:      str
    location:   str = ""
    url:        str = ""
    keyword:    str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ==============================================================================
# 🔧  DRIVER
# ==============================================================================
def init_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=opts)
    driver.implicitly_wait(2)
    return driver


# ==============================================================================
# 🖱️  HELPERS
# ==============================================================================
def _wait_for(driver, by, locator, timeout=WAIT_SEC):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, locator))
    )


def automation_click(driver, automation_id: str, timeout: int = WAIT_SEC) -> bool:
    """Click by data-automation-id. Falls back to JS click. Returns True on success."""
    xpath = f"//*[@data-automation-id='{automation_id}']"
    try:
        el = _wait_for(driver, By.XPATH, xpath, timeout)
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        time.sleep(random.uniform(0.15, 0.4))
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", el)
        return True
    except TimeoutException:
        log.debug(f"    timeout: {automation_id}")
        return False


def automation_type(driver, automation_id: str, text: str, timeout: int = WAIT_SEC) -> bool:
    """Send keys to input by data-automation-id."""
    xpath = f"//input[@data-automation-id='{automation_id}']"
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )
        el.clear()
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.DELETE)
        el.send_keys(text)
        return True
    except TimeoutException:
        log.debug(f"    timeout typing: {automation_id}")
        return False


# ==============================================================================
# 🔑  LOGIN
# ==============================================================================
def try_login(driver) -> bool:
    """Attempt Workday sign-in if the button exists. Silently skips if not."""
    if not EMAIL or not PASSWORD:
        return False
    if not automation_click(driver, "utilityButtonSignIn", timeout=5):
        return False
    time.sleep(0.8)
    automation_type(driver, "email", EMAIL, timeout=8)
    automation_type(driver, "password", PASSWORD, timeout=8)
    # different Workday instances use different submit IDs
    if not automation_click(driver, "signInSubmitButton", timeout=6):
        automation_click(driver, "login", timeout=4)
    time.sleep(1.5)
    log.info("  Signed in")
    return True


# ==============================================================================
# 📋  COLLECT LISTINGS (with pagination)
# ==============================================================================
def collect_jobs(driver, company: str, keyword: str) -> list[JobRecord]:
    """Scrape all job cards on the current results page(s), following pagination."""
    jobs: list[JobRecord] = []
    page = 1

    while True:
        try:
            WebDriverWait(driver, WAIT_SEC).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[@data-automation-id='jobTitle']")
                )
            )
        except TimeoutException:
            log.info(f"    page {page}: no listings")
            break

        titles    = driver.find_elements(By.XPATH, "//a[@data-automation-id='jobTitle']")
        locations = driver.find_elements(By.XPATH, "//dd[@data-automation-id='locations']")

        for i, el in enumerate(titles):
            try:
                title = el.text.strip()
                url   = el.get_attribute("href") or ""
                loc   = locations[i].text.strip() if i < len(locations) else ""
                if title:
                    jobs.append(JobRecord(
                        company=company, title=title,
                        location=loc, url=url, keyword=keyword
                    ))
            except Exception:
                continue

        log.info(f"    page {page}: {len(titles)} jobs")

        # next page
        try:
            next_btn = driver.find_element(
                By.XPATH, "//button[@aria-label='next' or @data-automation-id='next']"
            )
            if next_btn.is_enabled() and next_btn.is_displayed():
                driver.execute_script("arguments[0].click();", next_btn)
                time.sleep(1.5)
                page += 1
            else:
                break
        except NoSuchElementException:
            break

    return jobs


# ==============================================================================
# 🔍  SEARCH + COLLECT
# ==============================================================================
def search_keyword(driver, company: str, base_url: str, keyword: str) -> list[JobRecord]:
    driver.get(base_url)
    time.sleep(1.5)

    # Try the most common Workday search box IDs
    search_ids = ["searchBox", "keyword-search-input", "Search", "search"]
    typed = False
    for sid in search_ids:
        if automation_type(driver, sid, keyword, timeout=5):
            typed = True
            break

    if not typed:
        log.debug(f"  [{keyword}] no search box — collecting all visible jobs")
        return collect_jobs(driver, company, keyword)

    # submit search
    submit_ids = ["searchButton", "keywordSearchButton", "Search_Button"]
    for sid in submit_ids:
        if automation_click(driver, sid, timeout=5):
            break
    else:
        # fallback: press Enter
        try:
            driver.switch_to.active_element.send_keys(Keys.RETURN)
        except Exception:
            pass

    time.sleep(1.5)
    found = collect_jobs(driver, company, keyword)
    log.info(f"  [{keyword}] → {len(found)}")
    return found


# ==============================================================================
# 🏢  PER-COMPANY SCRAPE
# ==============================================================================
def scrape_company(driver, company: str, url: str) -> list[JobRecord]:
    log.info(f"{'─' * 56}")
    log.info(f"  {company}")
    log.info(f"{'─' * 56}")

    try:
        driver.get(url)
        time.sleep(2)
        try_login(driver)

        all_jobs: list[JobRecord] = []
        seen: set[str] = set()           # deduplicate by (title, company)

        for keyword in KEYWORDS:
            jobs = search_keyword(driver, company, url, keyword)
            for j in jobs:
                key = (j.title.lower(), j.company)
                if key not in seen:
                    seen.add(key)
                    all_jobs.append(j)

        log.info(f"  {company} total unique: {len(all_jobs)}")
        return all_jobs

    except WebDriverException as e:
        log.error(f"  WebDriver error on {company}: {type(e).__name__}")
        return []
    except Exception as e:
        log.error(f"  Error on {company}: {e}")
        return []


# ==============================================================================
# 💾  SAVE
# ==============================================================================
def save_csv(records: list[JobRecord], path: str):
    if not records:
        log.warning("No records to save.")
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(JobRecord.__dataclass_fields__.keys()))
        writer.writeheader()
        writer.writerows(asdict(r) for r in records)
    log.info(f"Saved {len(records)} jobs → {path}")


# ==============================================================================
# 🚀  MAIN
# ==============================================================================
def run():
    log.info("=" * 56)
    log.info(
        f"  WORKDAY SCRAPER  |  {len(WORKDAY_COMPANIES)} companies"
        f"  |  {len(KEYWORDS)} keywords"
    )
    log.info("=" * 56)

    driver = init_driver()
    all_jobs: list[JobRecord] = []

    try:
        for company, url in WORKDAY_COMPANIES.items():
            jobs = scrape_company(driver, company, url)
            all_jobs.extend(jobs)
            time.sleep(random.uniform(1.5, 3.0))
    finally:
        save_csv(all_jobs, OUTPUT_FILE)
        driver.quit()

    log.info("=" * 56)
    log.info(f"  DONE  |  {len(all_jobs)} total jobs")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 56)


if __name__ == "__main__":
    run()
