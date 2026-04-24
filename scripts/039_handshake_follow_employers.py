"""
Handshake Employer Follow + Profile Update
──────────────────────────────────────────
1. Logs into Handshake (cookie-based, same as 036)
2. Updates your student profile — career interests, location, skills
3. Searches the employer directory, paginating through results
4. Follows every employer that matches:
     - Industry: tech / software / IT / SaaS / AI / cloud / security / fintech / gaming
     - Location:  California OR remote-friendly (or no location listed)
   and SKIPS:
     - Non-tech industries (retail, food, construction, etc.)
     - Employers you already follow
5. Logs everything to runs/handshake_follow_<RUN_ID>/

Usage:
  python 039_handshake_follow_employers.py
  python 039_handshake_follow_employers.py --dry-run      # log only, do not follow
  python 039_handshake_follow_employers.py --max-follows 200
  python 039_handshake_follow_employers.py --pages 10
"""

import argparse
import logging
import os
import random
import re
import sys
import time
from csv import DictWriter
from dataclasses import dataclass, asdict, field
from datetime import datetime

import sys as _sys, os as _os; _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import library.uc_compat  # noqa: F401
import undetected_chromedriver as uc
from dotenv import load_dotenv
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

load_dotenv()

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--dry-run",     action="store_true", help="Log only — do not follow")
parser.add_argument("--max-follows", type=int, default=500, help="Stop after N new follows (default 500)")
parser.add_argument("--pages",       type=int, default=40,  help="Max employer-search pages (default 40)")
args = parser.parse_args()

# ── Credentials ────────────────────────────────────────────────────────────────
USERNAME = os.getenv("handshake_email")
PASSWORD = os.getenv("handshake_password")

# ── Run folder ─────────────────────────────────────────────────────────────────
RUN_ID  = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
RUN_DIR = os.path.join("runs", f"handshake_follow_{RUN_ID}")
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

COOKIE_FILE = "handshake_cookies.json"
CSV_FILE    = os.path.join(RUN_DIR, "followed_employers.csv")

# ── Relevance filters ──────────────────────────────────────────────────────────
# Industries we WANT — tech/software companies that hire QA/SWE
GOOD_INDUSTRIES = {
    "software", "technology", "tech", "saas", "cloud", "internet",
    "information technology", "it services", "computer", "data",
    "artificial intelligence", "machine learning", "ai", "cybersecurity",
    "security", "fintech", "financial technology", "healthtech", "health tech",
    "medtech", "biotech", "gaming", "video games", "ecommerce", "e-commerce",
    "telecom", "semiconductor", "hardware", "robotics", "aerospace",
    "defense", "consulting", "staffing", "recruiting", "engineering",
    "analytics", "business intelligence", "devops", "infrastructure",
    "networking", "mobile", "app", "platform", "enterprise", "startup",
    # Government / public sector
    "government", "federal", "state", "county", "municipal", "public sector",
    "department of", "agency", "bureau", "city of", "county of",
    "transportation", "utilities", "airport", "port authority",
}

# Keywords that flag a company as NON-tech — skip these
BAD_INDUSTRY_TOKENS = {
    "restaurant", "food", "hospitality", "retail", "fashion", "apparel",
    "real estate", "construction", "farming",
    "agriculture", "media", "publishing",
    "entertainment", "sports", "travel",
    "insurance", "law", "legal",
}

# California city/region keywords
CA_TOKENS = {
    "california", " ca", "san francisco", "bay area", "san jose", "santa clara",
    "sunnyvale", "cupertino", "mountain view", "palo alto", "redwood city",
    "fremont", "milpitas", "sacramento", "davis", "los angeles", "san diego",
    "irvine", "pasadena", "santa barbara", "oakland", "berkeley", "emeryville",
    "menlo park", "foster city", "burlingame", "south san francisco",
}

def industry_ok(industry: str, description: str) -> bool:
    """Return True if employer looks like a tech company."""
    combined = (industry + " " + description).lower()
    if any(bad in combined for bad in BAD_INDUSTRY_TOKENS):
        return False
    return any(good in combined for good in GOOD_INDUSTRIES)

def location_ok(location: str) -> bool:
    """Return True if employer is in California, remote, or has no listed location."""
    if not location:
        return True   # no location = probably remote-friendly / nationwide
    low = location.lower()
    if "remote" in low:
        return True
    return any(tok in low for tok in CA_TOKENS)

# ── Data ───────────────────────────────────────────────────────────────────────
@dataclass
class Employer:
    name:        str
    industry:    str
    location:    str
    size:        str
    url:         str
    status:      str   # followed | skipped_industry | skipped_location | already_following | error | dry_run
    note:        str   = ""
    timestamp:   str   = field(default_factory=lambda: datetime.now().isoformat())

records: list[Employer] = []

def save_csv():
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = DictWriter(f, fieldnames=list(Employer.__dataclass_fields__.keys()))
        w.writeheader()
        w.writerows(asdict(r) for r in records)

# ── Driver ─────────────────────────────────────────────────────────────────────
# Persistent profile so Cloudflare recognises the same browser fingerprint each run.
CHROME_PROFILE = os.path.expanduser("~/.chrome-handshake-profile")

def init_driver() -> uc.Chrome:
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    return uc.Chrome(options=opts, use_subprocess=True, version_main=147)

driver: uc.Chrome = None

# ── Browser helpers ─────────────────────────────────────────────────────────────
def el_exists(xpath, timeout=2) -> bool:
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))
        return True
    except Exception:
        return False

def safe_text(xpath, timeout=3) -> str:
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        ).text.strip()
    except Exception:
        return ""

def fast_click(xpath, timeout=5) -> bool:
    try:
        el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        try:
            el.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            driver.execute_script("arguments[0].click();", el)
        return True
    except Exception:
        return False

def human_pause(lo=0.8, hi=1.8):
    time.sleep(random.uniform(lo, hi))

# ── Login / session ────────────────────────────────────────────────────────────

def is_logged_in() -> bool:
    """Check for the left-nav sidebar — only visible when authenticated."""
    return el_exists("//nav | //a[contains(@href,'/jobs')] | //a[contains(@href,'/explore')]", timeout=5)

def check_session() -> bool:
    """Navigate to employer search and verify we're actually logged in."""
    driver.get("https://app.joinhandshake.com/employer-search?page=1&per_page=25")
    time.sleep(3)
    if is_logged_in() and "employer-search" in driver.current_url:
        log.info("Session active — already logged in.")
        return True
    log.info("Not logged in — doing fresh login.")
    return False

def login():
    driver.get("https://app.joinhandshake.com/login?requested_authentication_method=standard")
    time.sleep(3)
    driver.save_screenshot(os.path.join(RUN_DIR, "login_page.png"))
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "email-address-identifier"))
    ).send_keys(USERNAME)
    fast_click("//button[normalize-space()='Next']")
    time.sleep(1.5)
    fast_click("//a[normalize-space()='Log in another way']")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "password"))
    ).send_keys(PASSWORD)
    fast_click("//button[normalize-space()='Log in']")
    time.sleep(4)

# ── Profile update ─────────────────────────────────────────────────────────────
def update_profile():
    """
    Navigate to the student profile and update career interests / location prefs.
    Handshake's profile page: https://app.joinhandshake.com/students/<id>/edit
    We use the nav shortcut → Profile → Edit.
    """
    log.info("\n── Updating profile ──────────────────────────────────────────")
    try:
        driver.get("https://app.joinhandshake.com/users/me")
        time.sleep(3)
        driver.save_screenshot(os.path.join(RUN_DIR, "profile_page.png"))

        # Click "Edit profile" button
        edit_xpaths = [
            "//a[contains(normalize-space(),'Edit profile')]",
            "//button[contains(normalize-space(),'Edit profile')]",
            "//a[contains(@href,'/edit')]",
        ]
        clicked = False
        for xp in edit_xpaths:
            if el_exists(xp, timeout=3):
                fast_click(xp)
                time.sleep(2)
                clicked = True
                break
        if not clicked:
            log.warning("  Could not find Edit profile button — skipping profile update.")
            return

        driver.save_screenshot(os.path.join(RUN_DIR, "profile_edit.png"))

        # ── Job type / career interests ────────────────────────────────────
        # Look for "Job type" or "Employment type" checkboxes: Full-time
        for xp in [
            "//label[contains(normalize-space(),'Full-Time')]",
            "//label[contains(normalize-space(),'Full Time')]",
        ]:
            if el_exists(xp, timeout=2):
                cb = driver.find_element(By.XPATH, xp)
                if "checked" not in (cb.get_attribute("class") or ""):
                    driver.execute_script("arguments[0].click();", cb)
                    human_pause(0.3, 0.6)
                break

        # ── Location preferences ───────────────────────────────────────────
        # Try to find a location preference field and set California / Remote
        for loc_value in ["California", "Remote"]:
            for xp in [
                f"//input[contains(@placeholder,'location') or contains(@placeholder,'Location')]",
                "//input[@name='location']",
            ]:
                if el_exists(xp, timeout=2):
                    try:
                        box = driver.find_element(By.XPATH, xp)
                        box.clear()
                        box.send_keys(loc_value)
                        time.sleep(1.0)
                        # pick first dropdown suggestion
                        opt_xp = "//*[@role='option'][1]"
                        if el_exists(opt_xp, timeout=2):
                            fast_click(opt_xp)
                            human_pause()
                    except Exception:
                        pass
                    break

        # ── Save ───────────────────────────────────────────────────────────
        for save_xp in [
            "//button[normalize-space()='Save']",
            "//button[normalize-space()='Save Changes']",
            "//button[@type='submit']",
        ]:
            if el_exists(save_xp, timeout=3):
                fast_click(save_xp)
                time.sleep(2)
                log.info("  Profile saved.")
                driver.save_screenshot(os.path.join(RUN_DIR, "profile_saved.png"))
                break

    except Exception as e:
        log.warning(f"  Profile update error: {e}")

# ── Employer search + follow ───────────────────────────────────────────────────
def find_follow_buttons():
    """Return all follow-employer buttons on the current page."""
    return driver.find_elements(By.XPATH, "//button[@data-testid='follow-employer-button']")

def process_follow_button(btn, idx: int, total: int) -> str:
    """
    Given a follow button element, scrape surrounding card text for name/industry/location,
    apply relevance filters, then click Follow if eligible.
    Returns status string.
    """
    name = industry = location = size = url = ""
    try:
        # Walk up to the nearest ancestor that contains the company name
        card = driver.execute_script("""
            let el = arguments[0];
            for (let i = 0; i < 8; i++) {
                el = el.parentElement;
                if (!el) break;
                // Stop when we have a block with multiple lines of text
                if (el.innerText && el.innerText.split('\\n').filter(s=>s.trim()).length >= 3) return el;
            }
            return arguments[0].parentElement;
        """, btn)

        card_text = (card.text if card else "") or ""
        lines = [l.strip() for l in card_text.splitlines() if l.strip()]

        name     = lines[0] if lines else ""
        industry = lines[1] if len(lines) > 1 else ""

        for line in lines[2:]:
            low = line.lower()
            if any(tok in low for tok in CA_TOKENS) or "remote" in low:
                location = line
            elif any(c.isdigit() for c in line) and not location:
                size = line

        # Try to grab the href from an ancestor <a>
        try:
            a = driver.execute_script("""
                let el = arguments[0];
                for (let i = 0; i < 10; i++) {
                    el = el.parentElement;
                    if (!el) break;
                    if (el.tagName === 'A' && el.href) return el;
                }
                return null;
            """, btn)
            if a:
                url = a.get_attribute("href") or ""
        except Exception:
            pass

        already = btn.get_attribute("aria-pressed") == "true" or btn.text.strip() == "Following"

        log.info(f"  [{idx:03}/{total}] {name[:38]:<38} | {industry[:22]:<22} | {location[:18]}")

        if already:
            records.append(Employer(name=name, industry=industry, location=location,
                                    size=size, url=url, status="already_following"))
            return "already_following"

        if not industry_ok(industry, card_text):
            records.append(Employer(name=name, industry=industry, location=location,
                                    size=size, url=url, status="skipped_industry"))
            return "skipped_industry"

        if not location_ok(location):
            records.append(Employer(name=name, industry=industry, location=location,
                                    size=size, url=url, status="skipped_location"))
            return "skipped_location"

        if args.dry_run:
            records.append(Employer(name=name, industry=industry, location=location,
                                    size=size, url=url, status="dry_run"))
            return "dry_run"

        # Click Follow
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
        try:
            btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", btn)
        human_pause(0.5, 1.2)

        log.info(f"    ✓ Followed {name}")
        records.append(Employer(name=name, industry=industry, location=location,
                                size=size, url=url, status="followed"))
        return "followed"

    except Exception as e:
        log.error(f"  Button {idx} error: {type(e).__name__}: {e}")
        records.append(Employer(name=name, industry=industry, location=location,
                                size=size, url=url, status="error", note=str(e)))
        return "error"

def run_employer_search(max_follows: int, max_pages: int):
    follows = 0
    base_url = "https://app.joinhandshake.com/employer-search?per_page=25"

    for page in range(1, max_pages + 1):
        if follows >= max_follows:
            log.info(f"  Max follows ({max_follows}) reached — stopping.")
            break

        url = f"{base_url}&page={page}"
        log.info(f"\n{'='*60}")
        log.info(f"  Employer search page {page}/{max_pages}  |  followed so far: {follows}")
        log.info(f"{'='*60}")
        driver.get(url)
        time.sleep(random.uniform(2.5, 4.0))

        driver.save_screenshot(os.path.join(RUN_DIR, f"page_{page:03}.png"))

        btns = find_follow_buttons()
        if not btns:
            log.info("  No follow buttons found — trying scroll for lazy load.")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            btns = find_follow_buttons()
            if not btns:
                log.info("  Still no buttons — end of results.")
                break

        log.info(f"  Found {len(btns)} employer cards")

        for idx, btn in enumerate(btns, start=1):
            if follows >= max_follows:
                break
            status = process_follow_button(btn, idx, len(btns))
            if status in ("followed", "dry_run"):
                follows += 1
            human_pause(0.3, 0.7)

        save_csv()
        log.info(f"  Page {page} done — total followed: {follows}")
        time.sleep(random.uniform(1.5, 3.0))

    return follows

# ── Main ───────────────────────────────────────────────────────────────────────
def run():
    global driver

    mode = "DRY-RUN" if args.dry_run else "LIVE"
    log.info("=" * 60)
    log.info(f"  Handshake Employer Follow  |  {mode}")
    log.info(f"  Max follows: {args.max_follows}  |  Max pages: {args.pages}")
    log.info(f"  Run folder: {RUN_DIR}")
    log.info("=" * 60)

    driver = init_driver()

    if not check_session():
        login()
        # After login, navigate to employer search to confirm session
        driver.get("https://app.joinhandshake.com/employer-search?page=1&per_page=25")
        time.sleep(3)

    driver.save_screenshot(os.path.join(RUN_DIR, "post_login.png"))

    # 1. Update profile first
    update_profile()

    # 2. Follow relevant employers
    total_followed = run_employer_search(args.max_follows, args.pages)

    save_csv()

    from collections import Counter
    counts = Counter(r.status for r in records)
    log.info("\n" + "=" * 60)
    log.info("DONE")
    for status, cnt in sorted(counts.items()):
        log.info(f"  {status:<30} {cnt:>5}")
    log.info(f"  Total followed: {total_followed}")
    log.info(f"  CSV → {CSV_FILE}")

    try:
        driver.quit()
    except Exception:
        pass


if __name__ == "__main__":
    run()
