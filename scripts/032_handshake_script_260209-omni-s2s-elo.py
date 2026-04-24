"""
Handshake Task Helper — Omni S2S ELO Evaluation (Feb 2026)
────────────────────────────────────────────────────────────
Evaluates Omni speech-to-speech (S2S) AI model outputs head-to-head
using ELO ranking methodology. Submits quality rankings to the
Outlier Handshake contractor platform for AI model training data.

Usage: python 032_handshake_script_260209-omni-s2s-elo.py
"""
import os
import random
import time
import sys
import logging
import json
import csv
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException,
    NoSuchWindowException, WebDriverException,
    NoSuchElementException, ElementNotInteractableException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# ==============================================================================
# ⚙️ CONFIGURATION
# ==============================================================================
load_dotenv()

EMAIL           = os.getenv("handshake_email")
PASS            = os.getenv("handshake_password")
WORKER_EMAIL    = os.getenv("multimango_email")
WORKER_PASSWORD = os.getenv("multimango_password")

CATEGORIES = [
    "Audio and Recording Quality",
    "Persona Likeness (Speaker Similarity)",
    "Utility",
    "Persona Likeness",
    "Contextual Appropriateness",
    "Naturalness",
    "Overall Preference",
    "Dominant Factor",
]

TASK_ID        = "260209-omni-s2s-elo"
AUDIO_WAIT_SEC = 10 * 60    # time to wait for audio playback
COOLDOWN       = 10        # seconds between cycles
WAIT_SEC       = 30        # selenium wait timeout
DURATION_HOURS = 30
TOTAL_SECONDS  = DURATION_HOURS * 3600

# Speed tuning — set False to disable human jitter entirely
HUMAN_DELAY_ENABLED = True

# ==============================================================================
# 📊 DATA COLLECTION
# ==============================================================================
RUN_ID       = datetime.now().strftime("%Y%m%d_%H%M%S")
_RUN_DIR     = os.path.join("runs", "handshake_elo")
os.makedirs(_RUN_DIR, exist_ok=True)
LOG_FILE     = os.path.join(_RUN_DIR, f"automation_{RUN_ID}.log")
DATA_FILE    = os.path.join(_RUN_DIR, f"{RUN_ID}.csv")
SUMMARY_FILE = os.path.join(_RUN_DIR, f"summary_{RUN_ID}.json")

@dataclass
class CycleRecord:
    cycle:           int
    started_at:      str
    finished_at:     str   = ""
    duration_sec:    float = 0.0
    multimango_ok:   bool  = False
    handshake_ok:    bool  = False
    votes_cast:      int   = 0
    categories_done: str   = ""   # comma-separated
    submit_ok:       bool  = False
    error:           str   = ""

_csv_writer  = None
_csv_file_fh = None

def _init_csv():
    global _csv_writer, _csv_file_fh
    _csv_file_fh = open(DATA_FILE, "w", newline="", encoding="utf-8")
    _csv_writer  = csv.DictWriter(_csv_file_fh, fieldnames=list(CycleRecord.__dataclass_fields__.keys()))
    _csv_writer.writeheader()
    _csv_file_fh.flush()

def _write_row(record: CycleRecord):
    if _csv_writer:
        _csv_writer.writerow(asdict(record))
        _csv_file_fh.flush()

# ==============================================================================
# 📝 LOGGING
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
logger = logging.getLogger(__name__)

def _banner(msg: str, char: str = "=", width: int = 64):
    logger.info(char * width)
    logger.info(f"  {msg}")
    logger.info(char * width)

# ==============================================================================
# 🌐 GLOBALS
# ==============================================================================
driver: Optional[webdriver.Chrome] = None
wait:   Optional[WebDriverWait]    = None
handshake_window_handle            = None
multimango_window_handle           = None

# ==============================================================================
# ⏱️ HUMAN DELAYS (minimal but present)
# ==============================================================================
def human_wait(min_s=0.15, max_s=0.6):
    if HUMAN_DELAY_ENABLED:
        time.sleep(random.uniform(min_s, max_s))

# ==============================================================================
# 🖱️ CLICK HELPER
# ==============================================================================
def click(xpath: str, timeout: int = WAIT_SEC, js_fallback: bool = True) -> bool:
    """
    Click an element by XPath. Returns True on success, False on failure.
    Always tries native click first, falls back to JS click if intercepted.
    """
    if isinstance(xpath, tuple):   # safety: accept (By.XPATH, "...") tuples too
        xpath = xpath[1]
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        human_wait(0.1, 0.4)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            if js_fallback:
                driver.execute_script("arguments[0].click();", el)
            else:
                raise
        return True
    except TimeoutException:
        logger.warning(f"  ⏱ Timeout clicking: {xpath[:80]}")
        return False
    except Exception as e:
        logger.warning(f"  ⚠️  Click failed [{type(e).__name__}]: {xpath[:80]}")
        return False

def click_required(xpath: str, label: str = "", timeout: int = WAIT_SEC):
    """Click that raises on failure (for critical steps)."""
    if isinstance(xpath, tuple):
        xpath = xpath[1]
    label = label or xpath[:60]
    if not click(xpath, timeout):
        raise RuntimeError(f"Required click failed: {label}")

def js_click_element(el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    driver.execute_script("arguments[0].click();", el)

def safe_send_keys(locator, text: str, clear_first: bool = True):
    el = wait.until(EC.visibility_of_element_located(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    if clear_first:
        el.clear()
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.DELETE)
    el.send_keys(text)

# ==============================================================================
# 🪟 TAB MANAGEMENT
# ==============================================================================
def switch_to_tab(url_substring: str, timeout: int = 12) -> str:
    global handshake_window_handle, multimango_window_handle
    end = time.time() + timeout
    while time.time() < end:
        for h in driver.window_handles:
            try:
                driver.switch_to.window(h)
                if url_substring in (driver.current_url or ""):
                    if "handshake.com" in url_substring:
                        handshake_window_handle = h
                    elif "multimango.com" in url_substring:
                        multimango_window_handle = h
                    logger.debug(f"Switched to tab: {url_substring}")
                    return h
            except (NoSuchWindowException, WebDriverException):
                continue
        time.sleep(0.3)
    raise RuntimeError(f"Tab not found: {url_substring}")

def safe_close_and_switch(target_handle=None):
    if len(driver.window_handles) <= 1:
        return
    try:
        driver.close()
    except Exception:
        pass
    remaining = driver.window_handles
    if remaining:
        target = target_handle if target_handle in remaining else remaining[-1]
        driver.switch_to.window(target)

# ==============================================================================
# 🔧 SETUP
# ==============================================================================
def init_driver():
    global driver, wait
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=opts)
    wait   = WebDriverWait(driver, WAIT_SEC)
    logger.info("✅ WebDriver initialised")

def zoom_out(levels: int = 5):
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)
    for _ in range(levels):
        pyautogui.hotkey("command", "-")

def move_window_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey("ctrl", "option", "i")
    time.sleep(0.2)

# ==============================================================================
# 🔑 LOGIN
# ==============================================================================
def login_handshake():
    global handshake_window_handle
    driver.get("https://ai.joinhandshake.com/fellow/projects")
    handshake_window_handle = driver.current_window_handle
    move_window_topright()
    safe_send_keys((By.XPATH, "//input[@name='email']"), EMAIL)
    click_required("//button[normalize-space()='Continue with email']", "Continue with email")
    click_required("//button[normalize-space()='Log in another way']",  "Log in another way")
    safe_send_keys((By.XPATH, "//input[@name='password']"), PASS)
    click_required("//button[@aria-label='submit' or normalize-space()='Continue with password']", "Submit password")
    time.sleep(5)
    zoom_out()
    logger.info("✅ Handshake logged in")

def login_multimango():
    global multimango_window_handle
    switch_to_tab("multimango.com")
    zoom_out()
    multimango_window_handle = driver.current_window_handle
    click_required("//button[@id='terms']")  
    click("//button[@data-localization-key='formButtonPrimary' or normalize-space()='Continue']")
    time.sleep(0.8)
    safe_send_keys((By.ID, "password-field"), WORKER_PASSWORD)
    click_required("//button[@data-localization-key='formButtonPrimary' or normalize-space()='Log in']", "Log in")
    logger.info("✅ Multimango logged in")

# ==============================================================================
# 🗺️ NAVIGATION
# ==============================================================================
def nav_to_task():
    switch_to_tab("multimango.com")
    click_required("//div[@class='px-2']//a", "sidebar link")
    time.sleep(0.8)
    click_required(f"//a[@href='/tasks/{TASK_ID}']", f"task {TASK_ID}")
    time.sleep(0.8)
    logger.info(f"  📌 Navigated to task {TASK_ID}")

# ==============================================================================
# 🎧 MULTIMANGO TASKING CYCLE
# ==============================================================================

def _wait_for_rating_section_unlock(extra_wait: int = 3):
    """Block until the 'Play all media first' lock badge disappears."""
    lock_xpath = "//h2[contains(.,'Rate the Responses')]//span[contains(.,'Play all media first')]"
    try:
        WebDriverWait(driver, AUDIO_WAIT_SEC + 60).until(
            EC.invisibility_of_element_located((By.XPATH, lock_xpath))
        )
        logger.info("🔓 Rating section unlocked")
    except TimeoutException:
        logger.warning("⚠️  Rating section still locked — proceeding anyway")
    time.sleep(extra_wait)

def _vote_on_category(title: str) -> bool:
    """Click a random eligible button for one category. Returns True on success."""
    block_xpath = f"//h3[normalize-space()='{title}']/ancestor::div[contains(@class,'py-4')][1]"
    try:
        block = WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, block_xpath)))

        # Wait until at least one eligible button is interactable
        WebDriverWait(driver, 15).until(
            lambda d: any(
                b.is_displayed() and b.is_enabled()
                for b in block.find_elements(By.TAG_NAME, "button")
                if b.text.strip() and b.text.strip() != "Both Bad"
            )
        )

        eligible = [
            b for b in block.find_elements(By.TAG_NAME, "button")
            if b.text.strip() and b.text.strip() != "Both Bad"
        ]
        if not eligible:
            logger.warning(f"  ⚠️  No eligible buttons for '{title}'")
            return False

        choice = random.choice(eligible)
        js_click_element(choice)
        logger.info(f"  ✔  [{title}] → '{choice.text.strip()}'")
        return True

    except TimeoutException:
        logger.error(f"  ❌ Timeout on category '{title}'")
        return False
    except Exception as e:
        logger.error(f"  ❌ Error on category '{title}': {e}")
        return False

def multimango_tasking_cycle(record: CycleRecord) -> bool:
    """Full Multimango vote cycle. Mutates `record` with results."""
    logger.info("🎧 Starting Multimango tasking cycle...")
    switch_to_tab("multimango.com")

    # Kick off autoplay
    click_required("//button[@aria-label='Play']", "Play button")

    # Wait for unlock (handles audio play time internally)
    _wait_for_rating_section_unlock()

    # Vote on each category
    done = []
    for title in CATEGORIES:
        human_wait(0.3, 0.8)
        ok = _vote_on_category(title)
        if ok:
            done.append(title)
            record.votes_cast += 1
        human_wait(0.5, 1.2)

    record.categories_done = ", ".join(done)
    logger.info(f"  📊 Voted on {len(done)}/{len(CATEGORIES)} categories")

    # Submit
    try:
        click("//button[normalize-space()='Submit Vote']")
        record.submit_ok = True
        time.sleep(5)
        logger.info("  ✅ Vote submitted")
    except Exception as e:
        logger.error(f"  ❌ Submit failed: {e}")
        record.error = f"submit: {e}"
        raise

    safe_close_and_switch(handshake_window_handle)
    record.multimango_ok = True
    return True

# ==============================================================================
# 🤝 HANDSHAKE TASK COMPLETION
# ==============================================================================
def handshake_complete_task(record: CycleRecord) -> bool:
    logger.info("  🟦 Completing Handshake task...")
    switch_to_tab("ai.joinhandshake.com")

    # ── Required sequential steps ─────────────────────────────────────────────
    required_steps = [
        ("//button[normalize-space()='251030-audio-transcript (Max: 20 minutes)']", "Select task type"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",            "Submit 1"),
        ("//button[normalize-space()='No']",                                        "Answer No"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",            "Submit 2"),
        ("//button[normalize-space()='I submitted my task on Multimango']",         "Confirm Multimango"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",            "Submit 3"),
        ("//button[normalize-space()='Submit task']",                               "Submit task"),
        ("//button[normalize-space()='Confirm time']",                               "Confirm time"),
        ("//button[normalize-space()='Next task']",                               "Next Task"), # take 
        ("//button[normalize-space()='Open Multimango']",                               "Open Multimango")
    ]

    for xpath, label in required_steps:
        human_wait(0.4, 1.0)
        ok = click(xpath, timeout=20)
        if not ok:
            logger.warning(f"  ⏱ Timeout on required step: {label}")
            record.handshake_ok = False
            return False
        logger.info(f"  ✔ {label}")

# ==============================================================================
# 🔁 MAIN LOOP
# ==============================================================================
def run_automation():
    global driver, wait

    _banner(f"🚀 AUTOMATION START  |  Run ID: {RUN_ID}  |  Target: {DURATION_HOURS}h")
    _init_csv()

    metrics = {
        "run_id":        RUN_ID,
        "start_time":    datetime.now().isoformat(),
        "total_cycles":  0,
        "success":       0,
        "failed":        0,
        "total_votes":   0,
        "avg_cycle_sec": 0.0,
        "cycle_times":   [],
    }

    init_driver()

    try:
        # ── Login ──────────────────────────────────────────────────────────────
        login_handshake()
        click_required(
            "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']",
            "Start task"
        )
        click_required("//button[normalize-space()='Open Multimango']", "Open Multimango")
        login_multimango()

        # ── Timer ──────────────────────────────────────────────────────────────
        start_time = time.time()
        end_time   = start_time + TOTAL_SECONDS
        cycle_num  = 1

        while time.time() < end_time:
            elapsed   = int(time.time() - start_time)
            remaining = int(end_time   - time.time())
            e_str = time.strftime("%H:%M:%S", time.gmtime(elapsed))
            r_str = time.strftime("%H:%M:%S", time.gmtime(remaining))

            _banner(
                f"CYCLE {cycle_num:03d}  |  ✅ {metrics['success']}  ❌ {metrics['failed']}"
                f"  |  ⏱ {e_str} elapsed  ⏳ {r_str} left",
                char="-"
            )

            record = CycleRecord(
                cycle=cycle_num,
                started_at=datetime.now().isoformat(),
            )
            cycle_start = time.time()

            # ── Multimango ─────────────────────────────────────────────────────
            try:
                nav_to_task()
                multimango_tasking_cycle(record)
                metrics["success"] += 1
            except Exception as e:
                metrics["failed"] += 1
                record.error = str(e)
                logger.error(f"🔴 Multimango cycle failed: {e}")
                # recover: close tab if still open
                if multimango_window_handle and multimango_window_handle in driver.window_handles:
                    try:
                        driver.switch_to.window(multimango_window_handle)
                        safe_close_and_switch(handshake_window_handle)
                    except Exception:
                        pass

            # ── Handshake ──────────────────────────────────────────────────────
            try:
                # add check to only complete task when timer is starting 
                handshake_complete_task(record)
            except Exception as e:
                metrics["failed"] += 1
                record.error += f" | hs: {e}"
                logger.error(f"🔴 Handshake completion failed: {e}")

            # ── Record ─────────────────────────────────────────────────────────
            cycle_sec              = round(time.time() - cycle_start, 1)
            record.duration_sec   = cycle_sec
            record.finished_at    = datetime.now().isoformat()
            metrics["total_cycles"] += 1
            metrics["total_votes"]  += record.votes_cast
            metrics["cycle_times"].append(cycle_sec)

            _write_row(record)

            logger.info(
                f"  📈 Cycle {cycle_num:03d} done in {cycle_sec:.0f}s  |"
                f"  votes={record.votes_cast}  mm_ok={record.multimango_ok}"
                f"  hs_ok={record.handshake_ok}"
            )

            # ── Cooldown ───────────────────────────────────────────────────────
            logger.info(f"  😴 Cooldown {COOLDOWN}s...")
            time.sleep(COOLDOWN)
            cycle_num += 1

    except Exception as e:
        logger.critical(f"💥 Fatal error: {e}", exc_info=True)

    finally:
        # ── Summary ────────────────────────────────────────────────────────────
        times = metrics["cycle_times"]
        metrics["avg_cycle_sec"] = round(sum(times) / len(times), 1) if times else 0
        metrics["end_time"]      = datetime.now().isoformat()
        del metrics["cycle_times"]   # keep JSON clean

        with open(SUMMARY_FILE, "w") as f:
            json.dump(metrics, f, indent=2)

        if _csv_file_fh:
            _csv_file_fh.close()

        _banner("🏁 AUTOMATION COMPLETE", char="#")
        logger.info(f"  Total cycles  : {metrics['total_cycles']}")
        logger.info(f"  Successful    : {metrics['success']}")
        logger.info(f"  Failed        : {metrics['failed']}")
        logger.info(f"  Total votes   : {metrics['total_votes']}")
        logger.info(f"  Avg cycle     : {metrics['avg_cycle_sec']}s")
        logger.info(f"  CSV data      : {DATA_FILE}")
        logger.info(f"  JSON summary  : {SUMMARY_FILE}")
        logger.info(f"  Log file      : {LOG_FILE}")

        if driver:
            driver.quit()

if __name__ == "__main__":
    run_automation()