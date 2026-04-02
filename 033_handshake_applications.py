import logging
import random
import time
import json
import os
from collections import Counter
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, ElementNotInteractableException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import pyautogui
from dotenv import load_dotenv

# ── Logging & run folder setup ───────────────────────────────────────────────
RUN_ID   = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR  = os.path.join("runs", RUN_ID)
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
all_jobs: list[dict] = []

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(all_jobs, f, indent=2)

logging.info(f"Run ID: {RUN_ID}  ->  {RUN_DIR}/")

# ── Helper functions (unchanged from your original) ──────────────────────────
def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')

def move_window_to_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i')
    time.sleep(0.2)

def clickWebElement(xpath, pre_wait=(0.2, 0.9), post_wait=(0.2, 2.1)):
    try:
        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        element.click()
        logging.info(f"Clicked element with xpath {xpath}")
    except (TimeoutException, ElementClickInterceptedException, StaleElementReferenceException,
            NoSuchElementException, ElementNotInteractableException) as e:
        logging.error(f"Error clicking element with xpath {xpath}: {e}")

def element_exists(xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

# ── Credentials ──────────────────────────────────────────────────────────────
load_dotenv()
username = os.getenv('handshake_email')
password = os.getenv('handshake_password')

# ── Document names (must match exactly as saved on Handshake) ────────────────
COVER_LETTER_NAME = "HandShake Cover Letter"
TRANSCRIPT_NAME   = "0JH7198571 | SJSU Transcript | Oscar Leung"

# ── Browser init ─────────────────────────────────────────────────────────────
driver = webdriver.Chrome()
wait   = WebDriverWait(driver, 5)

# ── New helpers ───────────────────────────────────────────────────────────────
def safe_text(xpath, timeout=3):
    """Return text of first matching element, or empty string."""
    try:
        el = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return el.text.strip()
    except Exception:
        return ""

def close_modal():
    """Close any open application modal."""
    for close_xpath in [
        "//button[@aria-label='Cancel application']",
        "//button[@aria-label='Close']",
    ]:
        if element_exists(close_xpath):
            try:
                clickWebElement(close_xpath)
                time.sleep(0.5)
                return
            except Exception:
                pass

def attach_document(placeholder_text, doc_name):
    """
    Find a search box by its placeholder (e.g. 'Search your cover letters'),
    type the doc name, and click the matching dropdown option.
    Skips if a green card (already attached) is already present.
    """
    # If there's already a green attached card in that section, skip
    already_xpath = f"//input[@placeholder='{placeholder_text}']/ancestor::div[3]//h2"
    if element_exists(already_xpath):
        logging.info(f"  '{placeholder_text}': already attached -- skipping")
        return

    search_xpath = f"//input[@placeholder='{placeholder_text}']"
    if not element_exists(search_xpath):
        logging.info(f"  '{placeholder_text}': field not present -- skipping")
        return

    try:
        search_box = driver.find_element(By.XPATH, search_xpath)
        search_box.click()
        search_box.send_keys(doc_name[:12])   # type enough chars to filter dropdown
        time.sleep(1.0)

        option_xpath = f"//*[@role='option'][contains(normalize-space(), '{doc_name[:20]}')]"
        if element_exists(option_xpath):
            clickWebElement(option_xpath)
            logging.info(f"  Attached '{doc_name}'")
        else:
            logging.warning(f"  No dropdown match found for '{doc_name}'")
    except Exception as e:
        logging.warning(f"  Error attaching '{placeholder_text}': {e}")

def collect_job_data(index, page):
    return {
        "page":        page,
        "index":       index,
        "title":       safe_text("//h1[contains(@class,'job-title')] | //h2[contains(@aria-label,'View ')]"),
        "company":     safe_text("//*[contains(@data-hook,'employer-name')] | //span[contains(@class,'employer')]"),
        "location":    safe_text("//*[contains(@data-hook,'job-location')] | //*[contains(@class,'location')]"),
        "salary":      safe_text("//*[contains(@data-hook,'compensation')]"),
        "job_type":    safe_text("//*[contains(@data-hook,'employment-type')]"),
        "description": safe_text("//*[contains(@data-hook,'job-description')]")[:800],
        "deadline":    safe_text("//*[contains(normalize-space(),'Apply by')]"),
        "status":      "pending",
        "timestamp":   datetime.now().isoformat(),
    }

# ── Login (same flow as your original) ───────────────────────────────────────
driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
zoom_out()
move_window_to_topright()

driver.find_element(By.ID, "email-address-identifier").send_keys(username)
clickWebElement("//button[normalize-space()='Next']")
clickWebElement("//a[normalize-space()='Log in another way']")
driver.find_element(By.ID, "password").send_keys(password)
clickWebElement("//button[normalize-space()='Log in']")

# ── Navigate to job postings ──────────────────────────────────────────────────
clickWebElement("//a[contains(@aria-label, 'View more')]")
time.sleep(2)

# ── Pagination loop ───────────────────────────────────────────────────────────
TOTAL_PAGES = 6   # update if total changes

for page in range(1, TOTAL_PAGES + 1):
    logging.info(f"====== Page {page}/{TOTAL_PAGES} ======")

    if page > 1:
        next_page_xpath = f"//button[@value='{page}' and not(@aria-current='page')]"
        if not element_exists(next_page_xpath):
            logging.info(f"  No page {page} button found -- stopping.")
            break
        clickWebElement(next_page_xpath)
        time.sleep(2)

    job_cards = driver.find_elements(
        By.XPATH,
        "//div[@aria-label='Jobs List']/div[3]/div[contains(@data-hook, 'job-result-card')]"
    )
    logging.info(f"Found {len(job_cards)} job cards on page {page}")

    for index in range(len(job_cards)):
        job_data = {"page": page, "index": index + 1, "status": "pending", "timestamp": datetime.now().isoformat()}
        try:
            all_cards = driver.find_elements(
                By.XPATH,
                "//div[@aria-label='Jobs List']/div[3]/div[contains(@data-hook, 'job-result-card')]"
            )
            card = all_cards[index]
            link = card.find_element(By.XPATH, ".//a[@role='button']")

            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
            link.click()
            logging.info(f"Clicked job #{index + 1} of {len(job_cards)}")
            time.sleep(random.uniform(1.0, 2.0))

            # ── Collect metadata ──
            job_data = collect_job_data(index + 1, page)
            logging.info(f"  {job_data['title']} @ {job_data['company']} | {job_data['location']} | {job_data['salary']}")

            # ── Skip: already applied or withdrawn ──
            already_xpath = (
                "//button[contains(normalize-space(),'Withdraw application')] | "
                "//*[contains(normalize-space(),'Application withdrawn')] | "
                "//*[contains(normalize-space(),'You already applied')]"
            )
            if element_exists(already_xpath):
                logging.info(f"  Already applied / withdrawn -- skipping")
                job_data["status"] = "skipped_already_applied"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── Skip: external apply ──
            apply_externally_xpath = (
                "//button[contains(@aria-label, 'Apply externally')] | "
                "//button[.//span[normalize-space()='Apply externally']]"
            )
            if element_exists(apply_externally_xpath):
                logging.info(f"  External apply -- skipping")
                job_data["status"] = "skipped_external"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── Check for Apply button ──
            apply_button_xpath = (
                "//button[@aria-label='Apply'] | "
                "//button[.//span[normalize-space()='Apply']]"
            )
            if not element_exists(apply_button_xpath):
                logging.info(f"  No apply button found -- skipping")
                job_data["status"] = "skipped_no_button"
                all_jobs.append(job_data)
                save_data()
                continue

            # ── Open the apply modal ──
            clickWebElement(apply_button_xpath)
            time.sleep(random.uniform(0.8, 1.5))

            # ── Fill cover letter if section is present and empty ──
            if element_exists("//input[@placeholder='Search your cover letters']"):
                attach_document("Search your cover letters", COVER_LETTER_NAME)
                time.sleep(0.5)

            # ── Fill transcript if section is present and empty ──
            if element_exists("//input[@placeholder='Search your transcripts']"):
                attach_document("Search your transcripts", TRANSCRIPT_NAME)
                time.sleep(0.5)

            # ── Submit ──
            submit_button_xpath = "//button[normalize-space()='Submit Application']"
            if not element_exists(submit_button_xpath):
                logging.warning(f"  Submit button not found -- closing modal")
                close_modal()
                job_data["status"] = "skipped_no_submit_button"
                all_jobs.append(job_data)
                save_data()
                continue

            clickWebElement(submit_button_xpath)
            logging.info(f"  Application submitted!")
            job_data["status"] = "applied"
            time.sleep(random.uniform(1.5, 3.0))

            all_jobs.append(job_data)
            save_data()

        except Exception as e:
            logging.error(f"Job #{index + 1} failed: {type(e).__name__}: {e}")
            try:
                close_modal()
            except Exception:
                pass
            job_data["status"] = "error"
            all_jobs.append(job_data)
            save_data()
            continue

    time.sleep(random.uniform(2.0, 3.5))   # breathe between pages

# ── Summary ───────────────────────────────────────────────────────────────────
logging.info("=== Done ===")
logging.info(f"Total jobs processed: {len(all_jobs)}")
counts = Counter(j["status"] for j in all_jobs)
for status, n in counts.items():
    logging.info(f"  {status}: {n}")
logging.info(f"Data saved -> {DATA_FILE}")

driver.quit()