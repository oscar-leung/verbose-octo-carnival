import logging
import os
import random
import re
import time
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote_plus

import pyautogui
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
)
from urllib.parse import quote_plus

# ============================================================
# EDIT HERE
# ============================================================
def build_search_url(keywords: str, date_posted: str = "past-week") -> str:
    """
    keywords: human string, will be url-encoded
    date_posted: "past-24h" or "past-week" (LinkedIn uses these)
    """
    return (
        "https://www.linkedin.com/search/results/content/"
        f"?keywords={quote_plus(keywords)}"
        "&origin=FACETED_SEARCH"
        f"&datePosted=%5B%22{date_posted}%22%5D"
    )


# Expandable keyword packs
BASE_HASHTAGS = "#hiring remote"

QA_KEYWORDS = [
    f"software qa {BASE_HASHTAGS}",
    f"qa engineer {BASE_HASHTAGS}",
    f"sdet {BASE_HASHTAGS}",
    f"test automation engineer {BASE_HASHTAGS}",
    f"selenium python {BASE_HASHTAGS}",
    f"cypress {BASE_HASHTAGS}",
    f"playwright {BASE_HASHTAGS}",
    f"api testing postman {BASE_HASHTAGS}",
    f"mobile qa appium {BASE_HASHTAGS}",
    f"performance testing jmeter {BASE_HASHTAGS}",
    f"security testing {BASE_HASHTAGS}",
    f"salesforce qa {BASE_HASHTAGS}",
    f"manual tester {BASE_HASHTAGS}",
]

SWE_KEYWORDS = [
    f"software engineer {BASE_HASHTAGS}",
    f"backend engineer {BASE_HASHTAGS}",
    f"frontend engineer {BASE_HASHTAGS}",
    f"full stack developer {BASE_HASHTAGS}",
    f"python developer {BASE_HASHTAGS}",
    f"django developer {BASE_HASHTAGS}",
    f"fastapi developer {BASE_HASHTAGS}",
    f"node js developer {BASE_HASHTAGS}",
    f"javascript developer react {BASE_HASHTAGS}",
    f"react developer {BASE_HASHTAGS}",
    f"typescript developer {BASE_HASHTAGS}",
    f"java developer spring boot {BASE_HASHTAGS}",
    f"dotnet developer {BASE_HASHTAGS}",
    f"golang developer {BASE_HASHTAGS}",
    f"ruby on rails {BASE_HASHTAGS}",
    f"php laravel {BASE_HASHTAGS}",
]

DEVOPS_DATA_KEYWORDS = [
    f"devops engineer {BASE_HASHTAGS}",
    f"site reliability engineer {BASE_HASHTAGS}",
    f"sre {BASE_HASHTAGS}",
    f"cloud engineer aws {BASE_HASHTAGS}",
    f"cloud engineer azure {BASE_HASHTAGS}",
    f"kubernetes engineer {BASE_HASHTAGS}",
    f"terraform {BASE_HASHTAGS}",
    f"data engineer {BASE_HASHTAGS}",
    f"data analyst {BASE_HASHTAGS}",
    f"machine learning engineer {BASE_HASHTAGS}",
]

# Build many searches automatically (both past-24h and past-week)
SEARCH_URLS = []
for kw in (QA_KEYWORDS + SWE_KEYWORDS + DEVOPS_DATA_KEYWORDS):
    SEARCH_URLS.append(build_search_url(kw, "past-24h"))
    SEARCH_URLS.append(build_search_url(kw, "past-week"))

OUT_DIR = "linkedin_runs"
# ============================================================

EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")

pyautogui.PAUSE = 0.05  # small pause between GUI actions
pyautogui.FAILSAFE = True


# ---------------------------
# Data structures
# ---------------------------
@dataclass
class SearchResult:
    search_label: str
    search_url: str
    results_path: str
    total_posts_seen: int = 0
    posts_with_emails: int = 0
    unique_emails: int = 0
    unique_job_urls: int = 0
    error: str = ""

# ---------------------------
# UI helpers (macOS)
# ---------------------------
def zoom_out(times=5):
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.25)
    for _ in range(times):
        pyautogui.hotkey("command", "-")
        time.sleep(0.06)


def move_window_to_topright():
    # Magnet shortcut (your setup)
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "option", "i")
    time.sleep(0.25)


# ---------------------------
# General helpers
# ---------------------------
def human_wait(min_s=0.25, max_s=0.9, long_pause_chance=0.05, long_min=1.5, long_max=3.0):
    time.sleep(random.uniform(min_s, max_s))
    if random.random() < long_pause_chance:
        time.sleep(random.uniform(long_min, long_max))


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def safe_filename(s: str, max_len=80) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", (s or "")).strip("_")
    return s[:max_len] if s else "run"


def label_from_search_url(url: str) -> str:
    """
    Builds a readable label from URL keywords + datePosted.
    """
    try:
        q = parse_qs(urlparse(url).query)
        kw = unquote_plus(q.get("keywords", ["search"])[0])
        dp = q.get("datePosted", [""])[0]
        return safe_filename(f"{kw}_{dp}".strip("_"))
    except Exception:
        return "search"


def make_run_folder(out_dir: str):
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(out_dir, f"run_{run_id}")
    os.makedirs(run_dir, exist_ok=True)
    return run_id, run_dir


def setup_master_logging(run_dir: str):
    log_path = os.path.join(run_dir, "RUN.log")

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.INFO)

    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    fh = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    fh.setFormatter(fmt)

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)

    root.addHandler(fh)
    root.addHandler(sh)

    logging.info(f"Master log: {log_path}")
    return log_path

JOB_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\d+")
POST_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:feed/update|posts)/[^?\s]+")

def canonicalize_url(url: str) -> str:
    """
    Remove query params + fragments so we can dedupe reliably.
    """
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        return (url or "").strip()

def extract_relevant_links_from_post(post) -> list[str]:
    """
    Returns a list of deduped LinkedIn job/post URLs found in a post.
    """
    links = set()
    try:
        for a in post.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue

            # Keep just LinkedIn job + post/update links (adjust if you want external apply links too)
            if "linkedin.com/jobs/view" in href or "linkedin.com/feed/update" in href or "linkedin.com/posts" in href:
                links.add(canonicalize_url(href))
    except Exception:
        pass

    # Also regex scan the visible text (sometimes URLs appear in text)
    try:
        t = post.text or ""
        for m in JOB_URL_RE.findall(t):
            links.add(canonicalize_url(m))
        for m in POST_URL_RE.findall(t):
            links.add(canonicalize_url(m))
    except Exception:
        pass

    return sorted(links)

def click_xpath(driver, wait, xpath: str):
    el = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    human_wait(0.08, 0.2)
    el.click()
    human_wait(0.15, 0.35)


def expand_see_more(driver, post):
    try:
        buttons = post.find_elements(
            By.XPATH,
            ".//button[contains(., 'See more') or contains(., 'see more') "
            "or contains(@aria-label,'see more') or contains(@aria-label,'See more')]",
        )
        for b in buttons:
            try:
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.08)
            except Exception:
                pass
    except Exception:
        pass


def post_dedupe_key(post) -> str:
    try:
        li = post.find_element(By.XPATH, "./ancestor::*[@role='listitem'][1]")
        key = (li.get_attribute("id") or "").strip()
        if key:
            return key
    except Exception:
        pass

    try:
        txt = normalize_space(post.text)
        if txt:
            return txt[:220]
    except Exception:
        pass

    return ""


def find_relevant_url(post) -> str:
    try:
        for a in post.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = a.get_attribute("href") or ""
            if (
                "linkedin.com/jobs/view" in href
                or "linkedin.com/posts" in href
                or "linkedin.com/feed/update" in href
            ):
                return href
    except Exception:
        pass
    return ""


def wait_for_feed_posts(driver, wait, timeout_s=30):
    try:
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-view-name='feed-full-update']")))
        return True
    except TimeoutException:
        return False


def click_show_more_if_present(driver):
    xpaths = [
        "//button[contains(., 'Show more results')]",
        "//button[contains(., 'See more results')]",
        "//button[contains(., 'Show more')]",
    ]
    for xp in xpaths:
        try:
            btns = driver.find_elements(By.XPATH, xp)
            for btn in btns:
                if btn.is_displayed() and btn.is_enabled():
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    time.sleep(0.15)
                    driver.execute_script("arguments[0].click();", btn)
                    logging.info("Clicked a 'Show more results' button.")
                    time.sleep(1.0)
                    return True
        except Exception:
            pass
    return False


def scroll_more(driver, steps=6, step_px=900, after_step_sleep=0.25):
    """
    More realistic scrolling:
    - scrolls down in multiple increments to trigger lazy-loading
    - tries to click 'Show more results' if it appears
    """
    # try to ensure the page has focus (helps some setups)
    try:
        driver.find_element(By.TAG_NAME, "body").click()
    except Exception:
        pass

    for _ in range(steps):
        driver.execute_script("window.scrollBy(0, arguments[0]);", step_px)
        time.sleep(after_step_sleep)
        click_show_more_if_present(driver)

def extract_emails_from_feed(driver, results_path: str, pause=1.2, max_no_change=6):
    """
    Returns: (total_posts_seen, posts_with_emails, all_emails_set, all_job_urls_set)
    """
    seen_post_keys = set()
    total_posts_seen = 0
    posts_with_emails = 0
    all_emails = set()
    all_job_urls = set()

    no_change = 0
    scroll_container = get_scroll_container(driver)
    logging.info("Detected scroll container for lazy-load scrolling.")

    with open(results_path, "w", encoding="utf-8") as f:
        f.write("LinkedIn Email + Job Link Extraction\n")
        f.write(f"Timestamp : {datetime.now().isoformat(timespec='seconds')}\n")
        f.write(f"URL       : {driver.current_url}\n")
        f.write("=" * 90 + "\n\n")

        while True:
            posts = driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']")

            for post in posts:
                try:
                    key = post_dedupe_key(post)
                except StaleElementReferenceException:
                    continue

                if not key or key in seen_post_keys:
                    continue

                seen_post_keys.add(key)
                total_posts_seen += 1

                expand_see_more(driver, post)

                try:
                    text = post.text or ""
                except StaleElementReferenceException:
                    continue

                emails = sorted(set(EMAIL_RE.findall(text)))
                for e in emails:
                    all_emails.add(e.lower())

                links = extract_relevant_links_from_post(post)
                for u in links:
                    all_job_urls.add(u)

                snippet = normalize_space(text)[:260]

                if emails:
                    posts_with_emails += 1
                    logging.info(f"[POST {total_posts_seen}] emails={len(emails)} links={len(links)}")
                else:
                    logging.info(f"[POST {total_posts_seen}] emails=0 links={len(links)}")

                f.write(f"[POST #{total_posts_seen}]\n")
                f.write(f"Key    : {key}\n")
                f.write(f"Emails : {', '.join(emails) if emails else '(none)'}\n")
                if links:
                    f.write("Links  :\n")
                    for u in links:
                        f.write(f"  - {u}\n")
                else:
                    f.write("Links  : (none)\n")
                f.write(f"Snippet: {snippet}\n")
                f.write("-" * 90 + "\n\n")

            prev_posts_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']"))
            scroll_container_more(driver, scroll_container, steps=12, step_px=950, after_step_sleep=0.12)
            loaded = wait_for_new_posts(driver, prev_posts_count, timeout_s=10)

            new_posts_count = len(driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']"))
            logging.info(f"Scroll check: posts_before={prev_posts_count} posts_after={new_posts_count} loaded={loaded}")

            if new_posts_count <= prev_posts_count:
                no_change += 1
            else:
                no_change = 0

            if no_change >= max_no_change:
                logging.info("No new posts after repeated container scrolling; stopping this search.")
                break

        # Summary block (per search file)
        f.write("\n" + "=" * 90 + "\n")
        f.write("SUMMARY\n")
        f.write(f"Total NEW posts seen      : {total_posts_seen}\n")
        f.write(f"Posts containing email(s) : {posts_with_emails}\n")
        f.write(f"Unique emails found       : {len(all_emails)}\n")
        f.write(f"Unique job/post URLs      : {len(all_job_urls)}\n")

        f.write("\nEmails:\n")
        for e in sorted(all_emails):
            f.write(f" - {e}\n")

        f.write("\nJob/Post URLs:\n")
        for u in sorted(all_job_urls):
            f.write(f" - {u}\n")

        f.write("=" * 90 + "\n")

    return total_posts_seen, posts_with_emails, all_emails, all_job_urls


def ai_style_summary(run_id: str, results: list[SearchResult], all_emails_overall: set[str], all_job_urls_overall: set[str]):
    ok = [r for r in results if not r.error]
    bad = [r for r in results if r.error]

    total_posts = sum(r.total_posts_seen for r in ok)
    total_posts_with_emails = sum(r.posts_with_emails for r in ok)

    # best search (by emails found)
    best = None
    if ok:
        best = max(ok, key=lambda r: (r.unique_emails, r.posts_with_emails, r.total_posts_seen))

    # domain analysis
    domains = []
    for e in all_emails_overall:
        parts = e.split("@", 1)
        if len(parts) == 2:
            domains.append(parts[1].lower())
    domain_counts = Counter(domains).most_common(10)

    lines = []
    lines.append(f"RUN {run_id} — Automated Summary")
    lines.append("-" * 70)
    lines.append(f"Searches attempted : {len(results)}")
    lines.append(f"Searches succeeded : {len(ok)}")
    lines.append(f"Searches failed    : {len(bad)}")
    lines.append("")
    lines.append("What I observed / gathered:")
    lines.append(f"- Total new posts scanned        : {total_posts}")
    lines.append(f"- Posts containing email(s)      : {total_posts_with_emails}")
    lines.append(f"- Unique emails (overall)        : {len(all_emails_overall)}")
    lines.append(f"- Unique job/post URLs (overall) : {len(all_job_urls_overall)}")

    lines.append("")
    lines.append("ALL UNIQUE EMAIL LEADS:")
    for e in sorted(all_emails_overall):
        lines.append(f"- {e}")

    lines.append("")
    lines.append("ALL UNIQUE JOB/POST URL LEADS:")
    for u in sorted(all_job_urls_overall):
        lines.append(f"- {u}")
    

    if best:
        lines.append("")
        lines.append("Best-performing search (most unique emails):")
        lines.append(f"- Label       : {best.search_label}")
        lines.append(f"- Unique emails: {best.unique_emails}")
        lines.append(f"- Posts w/email: {best.posts_with_emails}")
        lines.append(f"- Results file : {best.results_path}")

    if domain_counts:
        lines.append("")
        lines.append("Most common email domains found:")
        for dom, cnt in domain_counts:
            lines.append(f"- {dom}: {cnt}")

    if bad:
        lines.append("")
        lines.append("Failures (continued anyway):")
        for r in bad:
            lines.append(f"- {r.search_label}: {r.error}")

    lines.append("")
    lines.append("Per-search breakdown:")
    for r in results:
        status = "OK" if not r.error else "ERROR"
        lines.append(
            f"- [{status}] {r.search_label} | posts={r.total_posts_seen} | "
            f"posts_with_email={r.posts_with_emails} | unique_emails={r.unique_emails}"
        )
        lines.append(f"  results: {r.results_path}")
        lines.append(f"  url    : {r.search_url}")

    return "\n".join(lines)


def get_scroll_container(driver):
    """
    LinkedIn often uses a scrollable container instead of window scrolling.
    Try known containers first, then fall back to "largest scrollable element".
    Returns a WebElement.
    """
    candidates = [
        "div.scaffold-layout__main",
        "main.scaffold-layout__main",
        "div.scaffold-finite-scroll__content",
        "div.scaffold-finite-scroll",
        "div.scaffold-layout__content",
    ]

    for css in candidates:
        try:
            el = driver.find_element(By.CSS_SELECTOR, css)
            is_scrollable = driver.execute_script(
                "return arguments[0].scrollHeight > arguments[0].clientHeight + 50;", el
            )
            if is_scrollable:
                return el
        except Exception:
            pass

    # Fallback: pick the largest scrollable element on the page
    return driver.execute_script("""
        const els = Array.from(document.querySelectorAll('*'));
        function isScrollable(el) {
          const st = getComputedStyle(el);
          if (!['auto','scroll'].includes(st.overflowY)) return false;
          return el.scrollHeight > el.clientHeight + 50;
        }
        const scrollables = els.filter(isScrollable)
                               .sort((a,b) => (b.scrollHeight-b.clientHeight) - (a.scrollHeight-a.clientHeight));
        return scrollables[0] || document.scrollingElement || document.documentElement;
    """)


def scroll_container_more(driver, container, steps=10, step_px=900, after_step_sleep=0.15):
    """
    Scrolls the *container* (not the window) in increments, triggering lazy-load.
    """
    for _ in range(steps):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];",
            container, step_px
        )
        time.sleep(after_step_sleep)
        click_show_more_if_present(driver)  # your existing helper


def wait_for_new_posts(driver, prev_count, timeout_s=8):
    """
    Poll until LinkedIn loads more posts (count increases) or timeout.
    """
    end = time.time() + timeout_s
    while time.time() < end:
        cur = len(driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']"))
        if cur > prev_count:
            return True
        time.sleep(0.35)
    return False

# ---------------------------
# Main
# ---------------------------
def main():
    load_dotenv()
    all_emails_overall: set[str] = set()
    all_job_urls_overall: set[str] = set()
    username = os.getenv("LINKIN_USERNAME")
    password = os.getenv("LINKIN_PASSWORD")

    if not username or not password:
        raise RuntimeError("Missing LINKIN_USERNAME or LINKIN_PASSWORD in environment/.env")

    run_id, run_dir = make_run_folder(OUT_DIR)
    setup_master_logging(run_dir)

    logging.info("=" * 70)
    logging.info(f"Run ID   : {run_id}")
    logging.info(f"Run dir  : {run_dir}")
    logging.info(f"Searches : {len(SEARCH_URLS)}")
    logging.info("=" * 70)

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    results: list[SearchResult] = []
    all_emails_overall: set[str] = set()

    try:
        # Login once
        logging.info("Opening LinkedIn login...")
        driver.get("https://www.linkedin.com/login")
        time.sleep(2.0)
        zoom_out(times=5)
        move_window_to_topright()

        logging.info("Typing credentials...")
        
        driver.find_element(By.ID, "username").clear()
        driver.find_element(By.ID, "username").send_keys(username)

        driver.find_element(By.ID, "password").clear()
        driver.find_element(By.ID, "password").send_keys(password)

        try:
            click_xpath(driver, wait, "//button[@type='submit']")
        except (TimeoutException, ElementClickInterceptedException):
            logging.warning("Could not click submit button (it may have already submitted).")

        time.sleep(4.0)

        # Mix order
        urls = SEARCH_URLS[:]

        for idx, search_url in enumerate(urls, start=1):
            label = label_from_search_url(search_url)
            results_path = os.path.join(run_dir, f"{idx:02d}_{label}_results.txt")

            logging.info("-" * 70)
            logging.info(f"[{idx}/{len(urls)}] Search: {label}")
            logging.info(f"URL: {search_url}")
            logging.info(f"Results file: {results_path}")

            sr = SearchResult(search_label=label, search_url=search_url, results_path=results_path)

            try:
                driver.get(search_url)
                human_wait(1.0, 2.0)

                if wait_for_feed_posts(driver, wait, timeout_s=35):

                    total_posts_seen, posts_with_emails, emails, job_urls = extract_emails_from_feed(
                        driver,
                        results_path=results_path,
                        pause=1.2,
                        max_no_change=6,
                    )

                    sr.total_posts_seen = total_posts_seen
                    sr.posts_with_emails = posts_with_emails
                    sr.unique_emails = len(emails)
                    sr.unique_job_urls = len(job_urls)

                    all_emails_overall |= set(emails)
                    all_job_urls_overall |= set(job_urls)

                logging.info(
                    f"Done: posts={sr.total_posts_seen} | posts_with_email={sr.posts_with_emails} | unique_emails={sr.unique_emails}"
                )

            except Exception as e:
                sr.error = str(e)
                logging.exception(f"Search crashed but continuing: {label}")

            results.append(sr)
            human_wait(1.5, 3.0)

        # Final run summary
        emails_path = os.path.join(run_dir, "ALL_EMAIL_LEADS.txt")
        with open(emails_path, "w", encoding="utf-8") as f:
            for e in sorted(all_emails_overall):
                f.write(e + "\n")

        jobs_path = os.path.join(run_dir, "ALL_JOB_URL_LEADS.txt")
        with open(jobs_path, "w", encoding="utf-8") as f:
            for u in sorted(all_job_urls_overall):
                f.write(u + "\n")
                
        summary_text = ai_style_summary(run_id, results, all_emails_overall, all_job_urls_overall)
        summary_path = os.path.join(run_dir, "RUN_SUMMARY.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(summary_text + "\n")

        logging.info("=" * 70)
        logging.info("ALL SEARCHES COMPLETE")
        logging.info(f"Summary file: {summary_path}")
        logging.info("=" * 70)
        print("\n" + summary_text + "\n")

    finally:
        # comment out if you want to keep browser open
        # driver.quit()
        pass


if __name__ == "__main__":
    main()