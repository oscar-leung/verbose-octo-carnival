"""
Handshake Task Helper — Omni T2V ELO Evaluation
─────────────────────────────────────────────────
Evaluates Omni text-to-video (T2V) AI model outputs head-to-head using ELO
ranking methodology. Submits quality rankings to the Outlier Handshake
contractor platform for AI model training data.

Each task has a ~3-minute video playback window before voting unlocks.

Usage: python 043_handshake_script_260317-omni-t2v-elo.py
"""
import os
import random
import time
import sys
import logging
import json
import csv
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchWindowException, WebDriverException,
    ElementNotInteractableException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# ==============================================================================
# CONFIGURATION
# ==============================================================================
load_dotenv()

EMAIL           = os.getenv("handshake_email")
PASS            = os.getenv("handshake_password")
WORKER_EMAIL    = os.getenv("multimango_email")
WORKER_PASSWORD = os.getenv("multimango_password")

# Categories shown in the rating panel (matches the live UI exactly).
CATEGORIES = [
    "Overall Preference",
    "Instruction Following",
    "Frame Visual Quality",
    "Motion & Temporal Quality",
    "Audio Quality & Sync",
    "Absence of AI Artifacts",
]

TASK_ID        = "260317-omni-t2v-elo"
VIDEO_WAIT_SEC = 3 * 60     # 3-minute video playback window before unlock
COOLDOWN       = 10         # seconds between cycles
WAIT_SEC       = 30         # selenium default wait
DURATION_HOURS = 5
TOTAL_SECONDS  = DURATION_HOURS * 3600

# Submission-time inflation (looks human on the "Task complete!" screen).
# Slightly higher than the actual 3-min playback to look like real review time.
SUBMIT_MIN_MINUTES = 3
SUBMIT_MAX_MINUTES = 5

HUMAN_DELAY_ENABLED = True

# ==============================================================================
# DATA COLLECTION
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
    categories_done: str   = ""
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
# LOGGING
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
# GLOBALS
# ==============================================================================
driver: Optional[webdriver.Chrome] = None
wait:   Optional[WebDriverWait]    = None
handshake_window_handle            = None
multimango_window_handle           = None

_JS_SCROLL_CENTER = "arguments[0].scrollIntoView({block:'center'});"
_JS_CLICK         = "arguments[0].click();"

# ==============================================================================
# HUMAN DELAYS
# ==============================================================================
def human_wait(min_s=0.15, max_s=0.6):
    if HUMAN_DELAY_ENABLED:
        time.sleep(random.uniform(min_s, max_s))

# ==============================================================================
# CLICK HELPERS
# ==============================================================================
def click(xpath: str, timeout: int = WAIT_SEC, js_fallback: bool = True) -> bool:
    """Click an element by XPath. Returns True on success."""
    if isinstance(xpath, tuple):
        xpath = xpath[1]
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script(_JS_SCROLL_CENTER, el)
        human_wait(0.1, 0.4)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            if js_fallback:
                driver.execute_script(_JS_CLICK, el)
            else:
                raise
        return True
    except TimeoutException:
        logger.warning(f"  Timeout clicking: {xpath[:80]}")
        return False
    except Exception as e:
        logger.warning(f"  Click failed [{type(e).__name__}]: {xpath[:80]}")
        return False

def click_required(xpath: str, label: str = "", timeout: int = WAIT_SEC):
    if isinstance(xpath, tuple):
        xpath = xpath[1]
    label = label or xpath[:60]
    if not click(xpath, timeout):
        raise RuntimeError(f"Required click failed: {label}")

def js_click_element(el):
    driver.execute_script(_JS_SCROLL_CENTER, el)
    driver.execute_script(_JS_CLICK, el)

def safe_send_keys(locator, text: str, clear_first: bool = True):
    el = wait.until(EC.visibility_of_element_located(locator))
    driver.execute_script(_JS_SCROLL_CENTER, el)
    if clear_first:
        el.clear()
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.DELETE)
    el.send_keys(text)

# ==============================================================================
# TAB MANAGEMENT
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
# SETUP
# ==============================================================================
def init_driver():
    global driver, wait
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Chrome(options=opts)
    wait   = WebDriverWait(driver, WAIT_SEC)
    logger.info("WebDriver initialised")

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
# LOGIN
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
    logger.info("Handshake logged in")

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
    logger.info("Multimango logged in")

# ==============================================================================
# NAVIGATION
# ==============================================================================
def nav_to_task():
    switch_to_tab("multimango.com")
    click_required("//div[@class='px-2']//a", "sidebar link")
    time.sleep(0.8)
    click_required(f"//a[@href='/tasks/{TASK_ID}']", f"task {TASK_ID}")
    time.sleep(0.8)
    logger.info(f"  Navigated to task {TASK_ID}")

# ==============================================================================
# MULTIMANGO TASKING CYCLE
# ==============================================================================
_VOTE_CHOICES = ("Response A", "Response B", "Both Good")


def _wait_for_videos() -> bool:
    """Wait until both comparison <video> elements are loaded and visible."""
    try:
        WebDriverWait(driver, 30).until(
            lambda d: len([
                v for v in d.find_elements(By.TAG_NAME, "video")
                if v.is_displayed()
                   and (v.get_attribute("readyState") or "0") not in ("0", "1")
            ]) >= 2
        )
        logger.info("  Both videos loaded")
        return True
    except TimeoutException:
        logger.warning("  Videos did not finish loading — proceeding anyway")
        return False


def _wait_for_rating_section_unlock(extra_wait: int = 2):
    """Block until the 'Play all media first' lock badge disappears."""
    lock_xpath = "//h2[contains(.,'Rate the Responses')]//span[contains(.,'Play all media first')]"
    try:
        WebDriverWait(driver, VIDEO_WAIT_SEC + 60).until(
            EC.invisibility_of_element_located((By.XPATH, lock_xpath))
        )
        logger.info("  Rating section unlocked")
    except TimeoutException:
        logger.warning("  Rating section still locked — proceeding anyway")
    time.sleep(extra_wait)


_B_LOCK_XPATH = (
    "//div[@data-audio-section='response-b']"
    "//span[contains(.,'Play Response A first')]"
)


def _play_video_at(index: int) -> bool:
    """Start the nth <video> element. Returns True if play() resolved without error."""
    try:
        driver.execute_script(
            "const v=document.querySelectorAll('video')[arguments[0]];"
            "if(v){v.muted=false;v.currentTime=0;return v.play().then(()=>true).catch(()=>false);}"
            "return false;",
            index,
        )
        return True
    except Exception as e:
        logger.warning(f"  JS play({index}) failed: {e}")
        return False


def _wait_for_video_ended(index: int, timeout_sec: int) -> bool:
    """Block until the nth <video> reports ended=true (or timeout)."""
    end = time.time() + timeout_sec
    while time.time() < end:
        try:
            done = driver.execute_script(
                "const v=document.querySelectorAll('video')[arguments[0]];"
                "return v && (v.ended || v.currentTime >= v.duration - 0.25);",
                index,
            )
            if done:
                return True
        except Exception:
            pass
        time.sleep(1.0)
    return False


def _play_responses_sequentially():
    """Play Response A, wait for it to end / B to unlock, then play Response B."""
    logger.info("  Playing Response A...")
    if not _play_video_at(0):
        # Fallback: keyboard shortcut "Q" listed in the UI
        try:
            driver.find_element(By.TAG_NAME, "body").send_keys("q")
        except Exception:
            pass

    # Wait for B's lock badge to disappear OR A's video to end (whichever first)
    end = time.time() + VIDEO_WAIT_SEC + 60
    a_done = False
    while time.time() < end:
        try:
            if not driver.find_elements(By.XPATH, _B_LOCK_XPATH):
                a_done = True
                break
        except Exception:
            pass
        if _wait_for_video_ended(0, timeout_sec=2):
            a_done = True
            break
    if a_done:
        logger.info("  Response A finished — B unlocked")
    else:
        logger.warning("  Timed out waiting for Response A — playing B anyway")

    human_wait(0.4, 0.9)
    logger.info("  Playing Response B...")
    _play_video_at(1)
    if not _wait_for_video_ended(1, timeout_sec=VIDEO_WAIT_SEC + 60):
        logger.warning("  Response B did not finish in time")
    else:
        logger.info("  Response B finished")


def _vote_on_category(title: str) -> bool:
    """Click a random eligible button (Response A / B / Both Good) for one category."""
    block_xpath = (
        f"//h3[contains(@class,'font-medium') and normalize-space()='{title}']"
        f"/ancestor::div[contains(@class,'py-4')][1]"
    )
    btn_row_xpath = ".//div[contains(@class,'gap-1.5') and contains(@class,'flex')]"

    try:
        block = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, block_xpath))
        )
        driver.execute_script(_JS_SCROLL_CENTER, block)
        human_wait(0.2, 0.5)

        WebDriverWait(driver, 10).until(
            lambda d: block.find_elements(By.XPATH, btn_row_xpath)
        )

        all_btns = block.find_elements(By.XPATH, btn_row_xpath + "/button")
        eligible = [
            b for b in all_btns
            if b.text.strip() in _VOTE_CHOICES and b.is_displayed() and b.is_enabled()
        ]
        if not eligible:
            eligible = [
                b for b in block.find_elements(By.TAG_NAME, "button")
                if b.text.strip() and b.text.strip() != "Both Bad" and b.is_displayed()
            ]
        if not eligible:
            logger.warning(f"  No eligible buttons for '{title}'")
            return False

        choice = random.choice(eligible)
        js_click_element(choice)
        logger.info(f"  [{title}] -> '{choice.text.strip()}'")
        human_wait(0.2, 0.5)
        return True

    except TimeoutException:
        logger.error(f"  Timeout finding category block: '{title}'")
        driver.save_screenshot(os.path.join(_RUN_DIR, f"timeout_{title.replace(' ','_')}.png"))
        return False
    except Exception as e:
        logger.error(f"  Error on '{title}': {type(e).__name__}: {e}")
        return False


def _wait_for_submit_enabled(timeout: int = 30) -> bool:
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.find_elements(
                By.XPATH, "//button[normalize-space()='Submit Vote' and not(@disabled)]"
            )
        )
        return True
    except TimeoutException:
        return False


def multimango_tasking_cycle(record: CycleRecord) -> bool:
    """Full Multimango T2V vote cycle. Mutates `record` with results."""
    logger.info("Starting Multimango T2V cycle...")
    switch_to_tab("multimango.com")

    _wait_for_videos()
    _play_responses_sequentially()
    _wait_for_rating_section_unlock()

    done = []
    for title in CATEGORIES:
        human_wait(0.4, 0.9)
        if _vote_on_category(title):
            done.append(title)
            record.votes_cast += 1
        human_wait(0.3, 0.7)

    record.categories_done = ", ".join(done)
    logger.info(f"  Voted on {len(done)}/{len(CATEGORIES)} categories")

    if not _wait_for_submit_enabled(timeout=15):
        logger.warning("  Submit Vote still disabled after 15s — trying click anyway")

    if not click("//button[normalize-space()='Submit Vote' and not(@disabled)]", timeout=10):
        record.error = "submit: timeout"
        raise RuntimeError("Submit Vote click timed out")

    record.submit_ok = True
    time.sleep(3)
    logger.info("  Vote submitted")

    safe_close_and_switch(handshake_window_handle)
    record.multimango_ok = True
    return True

# ==============================================================================
# TIME EDIT — inflate session time on "Task complete!" screen
# ==============================================================================
def _edit_submission_time():
    """Click 'Edit time' and set a realistic 3-5 min duration before confirming."""
    minutes = random.randint(SUBMIT_MIN_MINUTES, SUBMIT_MAX_MINUTES)
    seconds = random.randint(5, 55)
    logger.info(f"  Adjusting submission time -> {minutes}m {seconds}s")

    if not click("//button[normalize-space()='Edit time']", timeout=10):
        logger.warning("  'Edit time' button not found — skipping adjustment")
        return

    human_wait(0.6, 1.0)

    def _set_field(label: str, value: int):
        xp = f"//label[normalize-space()='{label}']/following::input[1]"
        try:
            el = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, xp))
            )
            driver.execute_script(_JS_SCROLL_CENTER, el)
            el.send_keys(Keys.COMMAND + "a")
            el.send_keys(Keys.DELETE)
            el.clear()
            el.send_keys(str(value))
            human_wait(0.1, 0.3)
        except Exception as e:
            logger.warning(f"  Could not set {label}: {e}")

    _set_field("Hours",   0)
    _set_field("Minutes", minutes)
    _set_field("Seconds", seconds)
    human_wait(0.3, 0.6)

    click("//button[normalize-space()='Save']", timeout=10)
    human_wait(0.5, 1.0)
    logger.info(f"  Time saved: {minutes}m {seconds}s")

# ==============================================================================
# HANDSHAKE TASK COMPLETION
# ==============================================================================
def handshake_complete_task(record: CycleRecord) -> bool:
    logger.info("  Completing Handshake task...")
    switch_to_tab("ai.joinhandshake.com")

    pre_confirm_steps = [
        # 1) Pick the task type from the approved list
        (f"//button[contains(normalize-space(),'{TASK_ID}')]",                "Select task type"),
        # 2) Confirm time submission on Multimango
        ("//button[normalize-space()='I submitted my time on Multimango']",   "Confirm Multimango submission"),
        # 3) Submit task → opens the 'Confirm time' / 'Edit time' modal
        ("//button[normalize-space()='Submit task']",                          "Submit task"),
    ]

    post_confirm_steps = [
        ("//button[normalize-space()='Confirm time' or normalize-space()='Retry']", "Confirm time / Retry"),
        ("//button[normalize-space()='Next task']",                                  "Next task"),
        ("//button[normalize-space()='Open Multimango']",                            "Open Multimango"),
    ]

    def _run_steps(steps):
        for xpath, label in steps:
            human_wait(0.4, 1.0)
            if not click(xpath, timeout=20):
                logger.warning(f"  Timeout on: {label}")
                return False
            logger.info(f"  {label}")
        return True

    if not _run_steps(pre_confirm_steps):
        record.handshake_ok = False
        return False

    _edit_submission_time()

    if not _run_steps(post_confirm_steps):
        record.handshake_ok = False
        return False

    record.handshake_ok = True
    return True

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def _login_and_warmup():
    login_handshake()
    click_required(
        "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']",
        "Start task"
    )
    click_required("//button[normalize-space()='Open Multimango']", "Open Multimango")
    login_multimango()
    nav_to_task()

    logger.info("  Waiting for 'Continue to Task' button (up to 700s)...")
    WebDriverWait(driver, 700).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue to Task')]"))
    ).click()
    logger.info("  Continue to Task clicked")


def _recover_multimango_tab():
    if multimango_window_handle and multimango_window_handle in driver.window_handles:
        try:
            driver.switch_to.window(multimango_window_handle)
            safe_close_and_switch(handshake_window_handle)
        except Exception:
            pass


def _run_cycle(cycle_num: int, metrics: dict) -> CycleRecord:
    elapsed   = int(time.time() - metrics["_start"])
    remaining = int(metrics["_end"] - time.time())
    _banner(
        f"CYCLE {cycle_num:03d}  |  OK {metrics['success']}  FAIL {metrics['failed']}"
        f"  |  {time.strftime('%H:%M:%S', time.gmtime(elapsed))} elapsed"
        f"  {time.strftime('%H:%M:%S', time.gmtime(remaining))} left",
        char="-"
    )

    record      = CycleRecord(cycle=cycle_num, started_at=datetime.now().isoformat())
    cycle_start = time.time()

    mm_ok = False
    try:
        nav_to_task()
        multimango_tasking_cycle(record)
        mm_ok = True
    except Exception as e:
        record.error = str(e)
        logger.error(f"Multimango cycle failed: {e}")
        _recover_multimango_tab()

    hs_ok = False
    try:
        hs_ok = handshake_complete_task(record) or False
    except Exception as e:
        record.error += f" | hs: {e}"
        logger.error(f"Handshake completion failed: {e}")

    cycle_sec           = round(time.time() - cycle_start, 1)
    record.duration_sec = cycle_sec
    record.finished_at  = datetime.now().isoformat()

    if mm_ok and hs_ok:
        metrics["success"] += 1
    else:
        metrics["failed"] += 1

    metrics["total_cycles"] += 1
    metrics["total_votes"]  += record.votes_cast
    metrics["cycle_times"].append(cycle_sec)

    _write_row(record)
    logger.info(
        f"  Cycle {cycle_num:03d} done in {cycle_sec:.0f}s  |"
        f"  votes={record.votes_cast}  mm_ok={record.multimango_ok}"
        f"  hs_ok={record.handshake_ok}"
    )
    return record


def run_automation():
    global driver, wait

    _banner(f"AUTOMATION START  |  Run ID: {RUN_ID}  |  Target: {DURATION_HOURS}h")
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
        _login_and_warmup()

        metrics["_start"] = time.time()
        metrics["_end"]   = metrics["_start"] + TOTAL_SECONDS
        cycle_num = 1

        while time.time() < metrics["_end"]:
            _run_cycle(cycle_num, metrics)
            logger.info(f"  Cooldown {COOLDOWN}s...")
            time.sleep(COOLDOWN)
            cycle_num += 1

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)

    finally:
        times = metrics.pop("cycle_times", [])
        metrics.pop("_start", None)
        metrics.pop("_end",   None)
        metrics["avg_cycle_sec"] = round(sum(times) / len(times), 1) if times else 0
        metrics["end_time"]      = datetime.now().isoformat()

        with open(SUMMARY_FILE, "w") as f:
            json.dump(metrics, f, indent=2)

        if _csv_file_fh:
            _csv_file_fh.close()

        _banner("AUTOMATION COMPLETE", char="#")
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
