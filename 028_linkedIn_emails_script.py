import logging
import random
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import pyautogui
from dotenv import load_dotenv
import os
from datetime import datetime

# helper fn
def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)

    # zoom out (Cmd + -)
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')

def move_window_to_topright():
    """Moves the current window to the top-right corner of the screen (macOS specific)."""
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i') # Move window top right shortcut using magnet app 
    time.sleep(0.2)

def clickWebElement(xpath, pre_wait=(0.2, 0.9), post_wait=(0.2, 2.1)):
    try:
        # small "aim" delay before clicking
        human_wait(*pre_wait)

        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

        # micro delay after scroll (feels more human)
        human_wait(0.15, 0.6)

        element.click()
        logging.info(f"Clicked element with xpath {xpath}")

        # small delay after clicking
        human_wait(*post_wait)

    except (TimeoutException, ElementClickInterceptedException, StaleElementReferenceException,
            NoSuchElementException, ElementNotInteractableException) as e:
        logging.error(f"Error clicking element with xpath {xpath}: {e}")

def element_exists(xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def scroll_by_last_item(pause=0.8, max_no_change=3):
    """
    Keeps scrolling the last listitem into view until no new items load.
    Stops after `max_no_change` consecutive times where the last item doesn't change.
    """
    last_key = None
    no_change = 0

    while True:
        items = driver.find_elements(By.CSS_SELECTOR, '[data-testid="lazy-column"] [role="listitem"]')
        if not items:
            return False

        last = items[-1]

        # build a "signature" for the last element so we know if it changed
        key = (last.get_attribute("id") or "") + "|" + (last.text[:80] or "")

        if key == last_key:
            no_change += 1
        else:
            no_change = 0
            last_key = key

        driver.execute_script("arguments[0].scrollIntoView({block:'end'});", last)
        time.sleep(pause)

        if no_change >= max_no_change:
            break

    return True

# --- Human-like delays ---
HUMAN_DELAY_ENABLED = True

def human_wait(min_s=0.4, max_s=2.3, long_pause_chance=0.08, long_min=2.0, long_max=4.5):
    """
    Randomized delay to reduce bot-like timing.
    - min_s/max_s: normal jitter range
    - long_pause_chance: occasionally add a longer "thinking" pause
    """
    if not HUMAN_DELAY_ENABLED:
        return

    t = random.uniform(min_s, max_s)
    time.sleep(t)

    # occasional longer pause
    if random.random() < long_pause_chance:
        time.sleep(random.uniform(long_min, long_max))

# Load variables from .env
load_dotenv()
username = os.getenv("LINKIN_USERNAME")
password = os.getenv("LINKIN_PASSWORD")

# Initialize variables
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)

# XPath selectors
EASY_BUTTON = "//button[@id='jobs-apply-button-id']"

# Email regex
EMAIL_RE = re.compile(r'(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b')


driver.get("https://www.linkedin.com/login")
zoom_out()
move_window_to_topright()

# login to linkedin
driver.find_element(By.ID,"username").send_keys(username)
driver.find_element(By.ID,"password").send_keys(password)
clickWebElement("//button[@type='submit']")

# nav to search page
# driver.get("https://www.linkedin.com/search/results/content/?keywords=software%20qa%20%23hiring&origin=GLOBAL_SEARCH_HEADER&datePosted=%5B%22past-week%22%5D")
driver.get("https://www.linkedin.com/search/results/content/?keywords=software%20qa%20%23hiring&origin=FACETED_SEARCH&datePosted=%5B%22past-24h%22%5D")

# ---------- output + logging setup ----------
RUN_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUT_DIR = "linkedin_runs"
os.makedirs(OUT_DIR, exist_ok=True)

LOG_PATH = os.path.join(OUT_DIR, f"linkedin_email_extract_{RUN_TS}.log")
RESULTS_PATH = os.path.join(OUT_DIR, f"linkedin_email_extract_{RUN_TS}.txt")

logging.getLogger().handlers.clear()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ],
)

logging.info(f"Run started: {RUN_TS}")
logging.info(f"Log file: {LOG_PATH}")
logging.info(f"Results file: {RESULTS_PATH}")


# ---------- scroll + extract emails as NEW posts appear ----------
time.sleep(2)

seen_post_keys = set()
all_emails = set()
posts_with_emails = 0
total_posts_seen = 0

last_key = None
no_change = 0
max_no_change = 3
pause = 0.9

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    f.write(f"LinkedIn Email Extraction Run\nTimestamp: {RUN_TS}\n")
    f.write(f"Search URL: {driver.current_url}\n")
    f.write("=" * 70 + "\n\n")

    while True:
        # re-find each loop to reduce stale references
        posts = driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']")

        for post in posts:
            # build a dedupe key (prefer listitem id; fallback to text prefix)
            try:
                li = post.find_element(By.XPATH, "./ancestor::*[@role='listitem'][1]")
                key = (li.get_attribute("id") or "").strip()
            except Exception:
                key = ""

            if not key:
                txt_for_key = normalize_space(post.text)
                key = txt_for_key[:200] if txt_for_key else f"fallback_{total_posts_seen}"

            if key in seen_post_keys:
                continue

            seen_post_keys.add(key)
            total_posts_seen += 1

            # best-effort: expand "See more" inside the post (won't always exist)
            try:
                see_more_buttons = post.find_elements(
                    By.XPATH,
                    ".//button[contains(., 'See more') or contains(., 'see more') "
                    "or contains(@aria-label,'see more') or contains(@aria-label,'See more')]"
                )
                for b in see_more_buttons:
                    try:
                        driver.execute_script("arguments[0].click();", b)
                        time.sleep(0.15)
                    except Exception:
                        pass
            except Exception:
                pass

            text = post.text or ""
            snippet = normalize_space(text)[:220]
            emails = sorted(set(EMAIL_RE.findall(text)))

            # optional "details": try to capture a relevant link from the post
            post_url = ""
            try:
                links = post.find_elements(By.CSS_SELECTOR, "a[href]")
                for a in links:
                    href = a.get_attribute("href") or ""
                    if "linkedin.com/jobs/view" in href or "linkedin.com/posts" in href or "linkedin.com/feed/update" in href:
                        post_url = href
                        break
            except Exception:
                pass

            if emails:
                posts_with_emails += 1
                for e in emails:
                    all_emails.add(e.lower())

                msg = f"[NEW POST #{total_posts_seen}] Emails: {', '.join(emails)}"
                logging.info(msg)

                f.write(f"[POST #{total_posts_seen}]\n")
                f.write(f"Key: {key}\n")
                if post_url:
                    f.write(f"URL: {post_url}\n")
                f.write(f"Emails: {', '.join(emails)}\n")
                f.write(f"Snippet: {snippet}\n")
                f.write("-" * 70 + "\n\n")
            else:
                logging.info(f"[NEW POST #{total_posts_seen}] No email found")

                f.write(f"[POST #{total_posts_seen}]\n")
                f.write(f"Key: {key}\n")
                if post_url:
                    f.write(f"URL: {post_url}\n")
                f.write("Emails: (none)\n")
                f.write(f"Snippet: {snippet}\n")
                f.write("-" * 70 + "\n\n")

        # scroll to load more items
        items = driver.find_elements(By.CSS_SELECTOR, "[data-testid='lazy-column'] [role='listitem']")
        if not items:
            logging.info("No listitems found; stopping.")
            break

        last = items[-1]
        current_last_key = (last.get_attribute("id") or "") + "|" + normalize_space(last.text)[:80]

        if current_last_key == last_key:
            no_change += 1
        else:
            no_change = 0
            last_key = current_last_key

        driver.execute_script("arguments[0].scrollIntoView({block:'end'});", last)
        time.sleep(pause)

        if no_change >= max_no_change:
            logging.info("No new items detected after scrolling; stopping.")
            break

    # ---------- final summary (also written to file) ----------
    summary_lines = [
        "",
        "=" * 70,
        "SUMMARY",
        f"Total NEW posts seen: {total_posts_seen}",
        f"Posts containing email(s): {posts_with_emails}",
        f"Unique emails found: {len(all_emails)}",
        "Emails:" if all_emails else "Emails: (none)",
    ]

    logging.info("========== SUMMARY ==========")
    for line in summary_lines[2:]:
        logging.info(line)

    f.write("\n" + "\n".join(summary_lines) + "\n")
    for e in sorted(all_emails):
        f.write(f" - {e}\n")
    f.write("=" * 70 + "\n")

logging.info("Run complete.")