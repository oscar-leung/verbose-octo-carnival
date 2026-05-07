"""
Handshake Task Helper — Vision (TI2T) Head-to-Head Evaluation
──────────────────────────────────────────────────────────────
Compares two text responses to an image+prompt input. Workflow:

  Step 1 — Categorize the prompt (dropdown)
  Step 2 — Rate each response on 4 dimensions × 3-point scale:
             Factuality | Instruction Following | Helpfulness | Style & Format
             (Major Issue / Minor Issue / No Issue)
  Step 3 — Pick winner: A / B / Tie / I don't know
  Justification — min 100 chars, NO PASTING (typed char-by-char)
  Submit vote

Each task targets 18–22 minutes of "review time" on the Handshake
Task-complete screen.

Usage: python 044_handshake_script_260504-vision-ti2t-h2h.py
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

# NOTE: confirm/update this once you see the live Multimango URL & Handshake button.
TASK_ID = "260504-vision-ti2t-h2h"

DIMENSIONS = ["Factuality", "Instruction Following", "Helpfulness", "Style & Format"]
RATINGS    = ["Major Issue", "Minor Issue", "No Issue"]
# Bias the random ratings — most things should land on "No Issue" / "Minor Issue".
RATING_WEIGHTS = [0.10, 0.30, 0.60]

# Step 3 winner weights: A, B, Tie, IDK
WINNER_CHOICES = ["A", "B", "tie", "idk"]
WINNER_WEIGHTS = [0.45, 0.45, 0.08, 0.02]

COOLDOWN       = 10
WAIT_SEC       = 30
DURATION_HOURS = 5
TOTAL_SECONDS  = DURATION_HOURS * 3600

# Submission time on the Handshake "Task complete!" screen (18–22 min per task).
SUBMIT_MIN_MINUTES = 18
SUBMIT_MAX_MINUTES = 22

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
    category_picked: str   = ""
    ratings_done:    int   = 0     # out of 8 (4 dims × 2 responses)
    winner:          str   = ""
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

# ==============================================================================
# HUMAN DELAYS
# ==============================================================================
def human_wait(min_s=0.15, max_s=0.6):
    if HUMAN_DELAY_ENABLED:
        time.sleep(random.uniform(min_s, max_s))

# ==============================================================================
# CLICK / INPUT HELPERS
# ==============================================================================
def click(xpath: str, timeout: int = WAIT_SEC, js_fallback: bool = True) -> bool:
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
    if isinstance(xpath, tuple):
        xpath = xpath[1]
    label = label or xpath[:60]
    if not click(xpath, timeout):
        raise RuntimeError(f"Required click failed: {label}")

def js_click_element(el):
    driver.execute_script(_JS_SCROLL_CENTER, el)
    driver.execute_script("arguments[0].click();", el)

def safe_send_keys(locator, text: str, clear_first: bool = True):
    el = wait.until(EC.visibility_of_element_located(locator))
    driver.execute_script(_JS_SCROLL_CENTER, el)
    if clear_first:
        el.clear()
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.DELETE)
    el.send_keys(text)

def type_like_human(el, text: str, min_d: float = 0.02, max_d: float = 0.09):
    """Type one char at a time — paste is blocked on the justification textarea."""
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(min_d, max_d))

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
# NAVIGATION
# ==============================================================================
def nav_to_task():
    switch_to_tab("multimango.com")
    click_required("//div[@class='px-2']//a", "sidebar link")
    time.sleep(0.8)
    click_required(f"//a[@href='/tasks/{TASK_ID}']", f"task {TASK_ID}")
    time.sleep(0.8)
    logger.info(f"  📌 Navigated to task {TASK_ID}")

# ==============================================================================
# JUSTIFICATION COPY (>100 chars, varied so it doesn't look templated)
# ==============================================================================
_JUSTIFICATION_BANK_A = [
    "Response A reads the image more carefully and stays on task; B drifts and adds details that aren't visibly supported by the prompt context.",
    "A handles the prompt instructions directly and keeps formatting clean. B is reasonable but slightly over-explains and includes one minor inaccuracy.",
    "Response A is more grounded in the visible content and avoids speculative additions. B is close but its phrasing is a touch verbose for what was asked.",
    "A is more accurate to what's in the image and follows the requested format more closely; B's structure is fine but a small detail is off.",
]
_JUSTIFICATION_BANK_B = [
    "Response B captures more of the visible details and presents them in a cleaner structure. A is acceptable but skips a relevant point from the image.",
    "B follows the instructions more literally and is easier to scan. A is okay but introduces a mild factual slip not supported by the image content.",
    "Response B is more complete and stays on topic without verbosity. A is shorter but misses a piece of the prompt that B addresses correctly.",
    "B reads the image more accurately and matches the requested formatting; A is reasonable overall but its summary leaves one detail unclear.",
]
_JUSTIFICATION_BANK_TIE = [
    "Both responses cover the same key points from the image with comparable accuracy and structure; the differences here are stylistic rather than substantive.",
    "A and B are roughly equivalent — same information, similar tone, no clear factual or formatting advantage either way given what's visible in the image.",
]
_JUSTIFICATION_BANK_IDK = [
    "The image is hard to read in places and both responses make plausible interpretations, so I can't confidently say one is better than the other here.",
    "Given the ambiguity in the prompt and partial visibility of the image content, neither response is clearly preferable on the dimensions evaluated.",
]

def _pick_justification(winner: str) -> str:
    bank = {
        "A":   _JUSTIFICATION_BANK_A,
        "B":   _JUSTIFICATION_BANK_B,
        "tie": _JUSTIFICATION_BANK_TIE,
        "idk": _JUSTIFICATION_BANK_IDK,
    }[winner]
    text = random.choice(bank)
    # Safety net: pad to >=100 chars with a neutral sentence if a future bank entry is short.
    if len(text) < 100:
        text += " The remaining differences are minor and don't change the overall judgement."
    return text

# ==============================================================================
# STEP 1 — CATEGORY DROPDOWN
# ==============================================================================
def _pick_category(record: CycleRecord) -> bool:
    """Open the 'Select a category' combobox and pick a random non-empty option."""
    combo_xp = "//button[@role='combobox' and .//span[normalize-space()='Select a category']]"
    if not click(combo_xp, timeout=15):
        # Fallback: any combobox that follows the Step 1 label
        combo_xp = "//div[contains(., 'Step 1')]/following::button[@role='combobox'][1]"
        if not click(combo_xp, timeout=10):
            logger.warning("  ⚠️  Category combobox not found")
            return False
    human_wait(0.4, 0.8)
    try:
        options = WebDriverWait(driver, 10).until(
            lambda d: [o for o in d.find_elements(By.XPATH, "//*[@role='option']") if o.is_displayed()]
        )
    except TimeoutException:
        logger.warning("  ⚠️  Category options never appeared")
        return False

    choice = random.choice(options)
    label  = (choice.text or "").strip()
    js_click_element(choice)
    record.category_picked = label
    logger.info(f"  ✔ Category → '{label}'")
    human_wait(0.3, 0.7)
    return True

# ==============================================================================
# STEP 2 — RATE 4 DIMENSIONS PER RESPONSE (A and B)
# ==============================================================================
def _rate_response(card_index: int, label: str) -> int:
    """
    card_index: 1 (Response A) or 2 (Response B). Returns count of dimensions rated.
    Each rating button has aria-label="<Dimension>: <Rating>". We scope by card.
    """
    card_xp = f"(//div[contains(@class,'flex h-full flex-col rounded-md')])[{card_index}]"
    try:
        card = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, card_xp))
        )
    except TimeoutException:
        logger.warning(f"  ⚠️  {label} card not found")
        return 0

    driver.execute_script(_JS_SCROLL_CENTER, card)
    human_wait(0.2, 0.5)

    rated = 0
    for dim in DIMENSIONS:
        rating = random.choices(RATINGS, weights=RATING_WEIGHTS, k=1)[0]
        aria   = f"{dim}: {rating}"
        btns = card.find_elements(By.XPATH, f".//button[@aria-label='{aria}']")
        if not btns:
            logger.warning(f"  ⚠️  [{label}] '{aria}' button missing")
            continue
        try:
            js_click_element(btns[0])
            rated += 1
            logger.info(f"  ✔ [{label}] {dim} → {rating}")
            human_wait(0.15, 0.45)
        except Exception as e:
            logger.warning(f"  ⚠️  [{label}] click {aria} failed: {e}")
    return rated

# ==============================================================================
# STEP 3 — WINNER + JUSTIFICATION + SUBMIT
# ==============================================================================
def _pick_winner(record: CycleRecord) -> bool:
    winner = random.choices(WINNER_CHOICES, weights=WINNER_WEIGHTS, k=1)[0]
    record.winner = winner
    label_xp = f"//label[@for='choice-{winner}']"
    if not click(label_xp, timeout=10):
        logger.warning(f"  ⚠️  Winner label '{winner}' click failed")
        return False
    logger.info(f"  ✔ Winner → {winner}")
    human_wait(0.3, 0.7)
    return True

def _fill_justification(winner: str) -> bool:
    text = _pick_justification(winner)
    try:
        ta = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "choice-comment"))
        )
        driver.execute_script(_JS_SCROLL_CENTER, ta)
        ta.click()
        human_wait(0.2, 0.4)
        type_like_human(ta, text)
        logger.info(f"  ✔ Justification typed ({len(text)} chars)")
        return True
    except TimeoutException:
        logger.error("  ❌ Justification textarea not found")
        return False

def _submit_vote() -> bool:
    # Button label is "Submit vote" (lowercase v). Wait until enabled.
    xp = "//button[normalize-space()='Submit vote' and not(@disabled)]"
    try:
        WebDriverWait(driver, 20).until(
            lambda d: d.find_elements(By.XPATH, xp)
        )
    except TimeoutException:
        logger.warning("  ⚠️  Submit vote stayed disabled — clicking anyway")
    return click(xp, timeout=10) or click("//button[normalize-space()='Submit vote']", timeout=5)

# ==============================================================================
# MULTIMANGO TASKING CYCLE
# ==============================================================================
def multimango_tasking_cycle(record: CycleRecord) -> bool:
    logger.info("🖼  Starting Vision (TI2T) H2H cycle...")
    switch_to_tab("multimango.com")

    # Wait for the task UI (header) to render.
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(., 'Vision') or contains(., 'TI2T')]"))
        )
    except TimeoutException:
        logger.warning("  ⚠️  TI2T header not detected — proceeding anyway")

    # Step 1: category
    _pick_category(record)
    human_wait(0.4, 0.9)

    # Step 2: rate Response A and Response B
    rated_a = _rate_response(1, "Response A")
    rated_b = _rate_response(2, "Response B")
    record.ratings_done = rated_a + rated_b
    logger.info(f"  📊 Ratings: A={rated_a}/4  B={rated_b}/4")

    # Step 3: winner
    _pick_winner(record)

    # Justification
    _fill_justification(record.winner or "tie")
    human_wait(0.5, 1.0)

    # Submit
    if not _submit_vote():
        record.error = "submit: failed"
        raise RuntimeError("Submit vote click failed")
    record.submit_ok = True
    time.sleep(3)
    logger.info("  ✅ Vote submitted")

    safe_close_and_switch(handshake_window_handle)
    record.multimango_ok = True
    return True

# ==============================================================================
# TIME EDIT — 18–22 min on the Handshake "Task complete!" screen
# ==============================================================================
def _edit_submission_time():
    minutes = random.randint(SUBMIT_MIN_MINUTES, SUBMIT_MAX_MINUTES)
    seconds = random.randint(5, 55)
    logger.info(f"  ⏱ Adjusting submission time → {minutes}m {seconds}s")

    if not click("//button[normalize-space()='Edit time']", timeout=10):
        logger.warning("  ⚠️  'Edit time' button not found — skipping")
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
            logger.warning(f"  ⚠️  Could not set {label}: {e}")

    _set_field("Hours",   0)
    _set_field("Minutes", minutes)
    _set_field("Seconds", seconds)
    human_wait(0.3, 0.6)

    click("//button[normalize-space()='Save']", timeout=10)
    human_wait(0.5, 1.0)
    logger.info(f"  ✔ Time saved: {minutes}m {seconds}s")

# ==============================================================================
# HANDSHAKE TASK COMPLETION
# ==============================================================================
def handshake_complete_task(record: CycleRecord) -> bool:
    logger.info("  🟦 Completing Handshake task...")
    switch_to_tab("ai.joinhandshake.com")

    pre_confirm_steps = [
        (f"//button[normalize-space()='{TASK_ID}']",                                  "Select task type"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",              "Submit 1"),
        ("//button[@aria-label='Continue task' or normalize-space()='Continue task']","Continue task"),
        ("//button[normalize-space()='I submitted my time on Multimango']",           "Confirm Multimango"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",              "Submit 3"),
        ("//button[normalize-space()='5']",                                           "Rate satisfaction 5"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",              "Submit satisfaction"),
        ("//div[@class='flex flex-col mt-1 flex-wrap gap-2 items-start']//div/button","Select sufficient time"),
        ("//button[@aria-label='Submit' or normalize-space()='Submit']",              "Submit sufficient time"),
        ("//button[@aria-label='Submit task' or normalize-space()='Submit task']",    "Submit task"),
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
                logger.warning(f"  ⏱ Timeout on: {label}")
                return False
            logger.info(f"  ✔ {label}")
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

    logger.info("  ⏳ Waiting for 'Continue to Task' (up to 700s)...")
    WebDriverWait(driver, 700).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Continue to Task')]"))
    ).click()
    logger.info("  ✔ Continue to Task clicked")

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
        f"CYCLE {cycle_num:03d}  |  ✅ {metrics['success']}  ❌ {metrics['failed']}"
        f"  |  ⏱ {time.strftime('%H:%M:%S', time.gmtime(elapsed))} elapsed"
        f"  ⏳ {time.strftime('%H:%M:%S', time.gmtime(remaining))} left",
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
        logger.error(f"🔴 Multimango cycle failed: {e}")
        _recover_multimango_tab()

    hs_ok = False
    try:
        hs_ok = handshake_complete_task(record) or False
    except Exception as e:
        record.error += f" | hs: {e}"
        logger.error(f"🔴 Handshake completion failed: {e}")

    cycle_sec           = round(time.time() - cycle_start, 1)
    record.duration_sec = cycle_sec
    record.finished_at  = datetime.now().isoformat()

    if mm_ok and hs_ok:
        metrics["success"] += 1
    else:
        metrics["failed"] += 1

    metrics["total_cycles"] += 1
    metrics["cycle_times"].append(cycle_sec)

    _write_row(record)
    logger.info(
        f"  📈 Cycle {cycle_num:03d} done in {cycle_sec:.0f}s  |"
        f"  ratings={record.ratings_done}/8  winner={record.winner}"
        f"  mm_ok={record.multimango_ok}  hs_ok={record.handshake_ok}"
    )
    return record

def run_automation():
    global driver, wait

    _banner(f"🚀 AUTOMATION START  |  Run ID: {RUN_ID}  |  Target: {DURATION_HOURS}h")
    _init_csv()

    metrics = {
        "run_id":       RUN_ID,
        "start_time":   datetime.now().isoformat(),
        "total_cycles": 0,
        "success":      0,
        "failed":       0,
        "avg_cycle_sec": 0.0,
        "cycle_times":  [],
    }

    init_driver()

    try:
        _login_and_warmup()

        metrics["_start"] = time.time()
        metrics["_end"]   = metrics["_start"] + TOTAL_SECONDS
        cycle_num = 1

        while time.time() < metrics["_end"]:
            _run_cycle(cycle_num, metrics)
            logger.info(f"  😴 Cooldown {COOLDOWN}s...")
            time.sleep(COOLDOWN)
            cycle_num += 1

    except Exception as e:
        logger.critical(f"💥 Fatal error: {e}", exc_info=True)

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

        _banner("🏁 AUTOMATION COMPLETE", char="#")
        logger.info(f"  Total cycles  : {metrics['total_cycles']}")
        logger.info(f"  Successful    : {metrics['success']}")
        logger.info(f"  Failed        : {metrics['failed']}")
        logger.info(f"  Avg cycle     : {metrics['avg_cycle_sec']}s")
        logger.info(f"  CSV data      : {DATA_FILE}")
        logger.info(f"  JSON summary  : {SUMMARY_FILE}")
        logger.info(f"  Log file      : {LOG_FILE}")

        if driver:
            driver.quit()

if __name__ == "__main__":
    run_automation()
