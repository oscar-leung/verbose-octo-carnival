import logging
import os
import random
import re
import time
import json
from collections import Counter
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote_plus, quote_plus

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

# ============================================================
# CONFIG
# ============================================================
OUT_DIR = "linkedin_runs"

MASTER_DIR = os.path.join(OUT_DIR, "_MASTER")
MASTER_EMAILS_PATH = os.path.join(MASTER_DIR, "MASTER_ALL_EMAILS.txt")
MASTER_URLS_PATH = os.path.join(MASTER_DIR, "MASTER_ALL_JOB_POST_URLS.txt")
MASTER_POSTS_PATH = os.path.join(MASTER_DIR, "MASTER_POSTS.jsonl")  # hella data ledger
MASTER_RUNS_PATH = os.path.join(MASTER_DIR, "MASTER_RUNS.jsonl")  # one record per run
MASTER_INSIGHTS_TXT = os.path.join(MASTER_DIR, "MASTER_INSIGHTS.txt")  # append insights

EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
JOB_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/jobs/view/\d+")
POST_URL_RE = re.compile(r"https?://(?:www\.)?linkedin\.com/(?:feed/update|posts)/[^?\s]+")

pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True


# ============================================================
# SEARCH URLS
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

SEARCH_URLS: list[str] = []
for kw in (QA_KEYWORDS + SWE_KEYWORDS + DEVOPS_DATA_KEYWORDS):
    SEARCH_URLS.append(build_search_url(kw, "past-24h"))
    SEARCH_URLS.append(build_search_url(kw, "past-week"))


# ============================================================
# DATA STRUCTURES
# ============================================================
@dataclass
class SearchResult:
    search_label: str
    search_url: str
    results_path: str
    total_posts_seen: int = 0
    posts_with_emails: int = 0
    unique_emails: int = 0
    unique_job_urls: int = 0
    runtime_s: float = 0.0
    new_emails_this_search: int = 0
    new_urls_this_search: int = 0
    error: str = ""


# ============================================================
# UI HELPERS (macOS)
# ============================================================
def zoom_out(times=5):
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.25)
    for _ in range(times):
        pyautogui.hotkey("command", "-")
        time.sleep(0.06)


def move_window_to_topright():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.15)
    pyautogui.hotkey("ctrl", "option", "i")
    time.sleep(0.25)


# ============================================================
# MASTER STORAGE HELPERS
# ============================================================
def ensure_master_storage():
    os.makedirs(MASTER_DIR, exist_ok=True)
    for p in [
        MASTER_EMAILS_PATH,
        MASTER_URLS_PATH,
        MASTER_POSTS_PATH,
        MASTER_RUNS_PATH,
        MASTER_INSIGHTS_TXT,
    ]:
        Path(p).touch(exist_ok=True)


def load_lines_set(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    out: set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.add(line)
    return out


def append_unique_lines(path: str, items: set[str], known: set[str]) -> set[str]:
    new_items = sorted([x for x in items if x and x not in known])
    if not new_items:
        return set()
    with open(path, "a", encoding="utf-8") as f:
        for x in new_items:
            f.write(x + "\n")
    known |= set(new_items)
    return set(new_items)


def append_jsonl(path: str, records: list[dict]):
    if not records:
        return
    with open(path, "a", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ============================================================
# GENERAL HELPERS
# ============================================================
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


def canonicalize_url(url: str) -> str:
    try:
        p = urlparse(url)
        return f"{p.scheme}://{p.netloc}{p.path}".rstrip("/")
    except Exception:
        return (url or "").strip()


def extract_relevant_links_from_post(post) -> list[str]:
    links = set()
    try:
        for a in post.find_elements(By.CSS_SELECTOR, "a[href]"):
            href = (a.get_attribute("href") or "").strip()
            if not href:
                continue
            if (
                "linkedin.com/jobs/view" in href
                or "linkedin.com/feed/update" in href
                or "linkedin.com/posts" in href
            ):
                links.add(canonicalize_url(href))
    except Exception:
        pass

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
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[data-view-name='feed-full-update']")
            )
        )
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


def get_scroll_container(driver):
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

    return driver.execute_script(
        """
        const els = Array.from(document.querySelectorAll('*'));
        function isScrollable(el) {
          const st = getComputedStyle(el);
          if (!['auto','scroll'].includes(st.overflowY)) return false;
          return el.scrollHeight > el.clientHeight + 50;
        }
        const scrollables = els.filter(isScrollable)
                               .sort((a,b) => (b.scrollHeight-b.clientHeight) - (a.scrollHeight-a.clientHeight));
        return scrollables[0] || document.scrollingElement || document.documentElement;
        """
    )


def scroll_container_more(driver, container, steps=10, step_px=900, after_step_sleep=0.15):
    for _ in range(steps):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollTop + arguments[1];",
            container,
            step_px,
        )
        time.sleep(after_step_sleep)
        click_show_more_if_present(driver)


def wait_for_new_posts(driver, prev_count, timeout_s=8):
    end = time.time() + timeout_s
    while time.time() < end:
        cur = len(driver.find_elements(By.CSS_SELECTOR, "div[data-view-name='feed-full-update']"))
        if cur > prev_count:
            return True
        time.sleep(0.35)
    return False


# ============================================================
# EXTRACTION
# ============================================================
def extract_emails_from_feed(driver, results_path: str, pause=1.2, max_no_change=6):
    """
    Returns: (total_posts_seen, posts_with_emails, all_emails_set, all_job_urls_set, post_records)
    """
    seen_post_keys = set()
    total_posts_seen = 0
    posts_with_emails = 0
    all_emails: set[str] = set()
    all_job_urls: set[str] = set()
    post_records: list[dict] = []

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

                post_url = find_relevant_url(post)
                post_records.append(
                    {
                        "ts": datetime.now().isoformat(timespec="seconds"),
                        "page_url": driver.current_url,
                        "post_key": key,
                        "post_url": canonicalize_url(post_url) if post_url else "",
                        "emails": emails,
                        "links": links,
                        "snippet": snippet,
                    }
                )

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

        # Summary block
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

    return total_posts_seen, posts_with_emails, all_emails, all_job_urls, post_records


# ============================================================
# SUMMARIES
# ============================================================
def ai_style_summary(run_id: str, results: list[SearchResult], all_emails_overall: set[str], all_job_urls_overall: set[str]):
    ok = [r for r in results if not r.error]
    bad = [r for r in results if r.error]

    total_posts = sum(r.total_posts_seen for r in ok)
    total_posts_with_emails = sum(r.posts_with_emails for r in ok)

    best = max(ok, key=lambda r: (r.unique_emails, r.posts_with_emails, r.total_posts_seen), default=None)

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
        lines.append(f"- Label        : {best.search_label}")
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
            f"- [{status}] {r.search_label} | runtime_s={r.runtime_s:.2f} | posts={r.total_posts_seen} | "
            f"posts_with_email={r.posts_with_emails} | unique_emails={r.unique_emails} | unique_urls={r.unique_job_urls} | "
            f"new_emails={r.new_emails_this_search} | new_urls={r.new_urls_this_search}"
        )
        lines.append(f"  results: {r.results_path}")
        lines.append(f"  url    : {r.search_url}")

    return "\n".join(lines)


# ============================================================
# MAIN
# ============================================================
def main():
    load_dotenv()

    username = os.getenv("LINKIN_USERNAME")
    password = os.getenv("LINKIN_PASSWORD")
    if not username or not password:
        raise RuntimeError("Missing LINKIN_USERNAME or LINKIN_PASSWORD in environment/.env")

    run_id, run_dir = make_run_folder(OUT_DIR)
    setup_master_logging(run_dir)

    ensure_master_storage()
    master_emails_known = load_lines_set(MASTER_EMAILS_PATH)
    master_urls_known = load_lines_set(MASTER_URLS_PATH)

    run_started_at = datetime.now()
    run_t0 = time.perf_counter()

    logging.info("=" * 70)
    logging.info(f"Run ID   : {run_id}")
    logging.info(f"Run dir  : {run_dir}")
    logging.info(f"Searches : {len(SEARCH_URLS)}")
    logging.info("=" * 70)

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 20)

    results: list[SearchResult] = []
    all_emails_overall: set[str] = set()
    all_job_urls_overall: set[str] = set()

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

        urls = SEARCH_URLS[:]

        for idx, search_url in enumerate(urls, start=1):
            label = label_from_search_url(search_url)
            results_path = os.path.join(run_dir, f"{idx:02d}_{label}_results.txt")

            logging.info("-" * 70)
            logging.info(f"[{idx}/{len(urls)}] Search: {label}")
            logging.info(f"URL: {search_url}")
            logging.info(f"Results file: {results_path}")

            sr = SearchResult(search_label=label, search_url=search_url, results_path=results_path)
            search_t0 = time.perf_counter()

            try:
                driver.get(search_url)
                human_wait(1.0, 2.0)

                if wait_for_feed_posts(driver, wait, timeout_s=35):
                    total_posts_seen, posts_with_emails, emails, job_urls, post_records = extract_emails_from_feed(
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

                    # MASTER append (deduped)
                    new_emails = append_unique_lines(MASTER_EMAILS_PATH, set(emails), master_emails_known)
                    new_urls = append_unique_lines(MASTER_URLS_PATH, set(job_urls), master_urls_known)
                    sr.new_emails_this_search = len(new_emails)
                    sr.new_urls_this_search = len(new_urls)

                    # MASTER post ledger (event style)
                    for r in post_records:
                        r["run_id"] = run_id
                        r["search_label"] = label
                        r["search_url"] = search_url
                    append_jsonl(MASTER_POSTS_PATH, post_records)

                sr.runtime_s = time.perf_counter() - search_t0

                logging.info(
                    f"Done: runtime_s={sr.runtime_s:.2f} | posts={sr.total_posts_seen} | "
                    f"posts_with_email={sr.posts_with_emails} | unique_emails={sr.unique_emails} | new_emails={sr.new_emails_this_search}"
                )

            except Exception as e:
                sr.error = str(e)
                sr.runtime_s = time.perf_counter() - search_t0
                logging.exception(f"Search crashed but continuing: {label}")

            results.append(sr)
            human_wait(1.5, 3.0)

        # Per-run output (existing behavior)
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

        # MASTER run + insights append
        run_runtime_s = time.perf_counter() - run_t0
        run_ended_at = datetime.now()

        domains = [e.split("@", 1)[1].lower() for e in all_emails_overall if "@" in e]
        top_domains = Counter(domains).most_common(15)

        insight_lines = []
        insight_lines.append("=" * 100)
        insight_lines.append(f"RUN {run_id}")
        insight_lines.append(f"Start: {run_started_at.isoformat(timespec='seconds')}")
        insight_lines.append(f"End  : {run_ended_at.isoformat(timespec='seconds')}")
        insight_lines.append(f"Total runtime (s): {run_runtime_s:.2f}")
        insight_lines.append("")
        insight_lines.append(f"Run unique emails: {len(all_emails_overall)}")
        insight_lines.append(f"Run unique urls  : {len(all_job_urls_overall)}")
        insight_lines.append("")
        insight_lines.append("Top email domains (this run):")
        for dom, cnt in top_domains:
            insight_lines.append(f"- {dom}: {cnt}")
        insight_lines.append("")
        insight_lines.append("Per-search runtime + deltas:")
        for r in results:
            status = "OK" if not r.error else "ERROR"
            insight_lines.append(
                f"- [{status}] {r.search_label} | runtime_s={r.runtime_s:.2f} | "
                f"posts={r.total_posts_seen} | emails={r.unique_emails} (+{r.new_emails_this_search} new) | "
                f"urls={r.unique_job_urls} (+{r.new_urls_this_search} new)"
            )

        with open(MASTER_INSIGHTS_TXT, "a", encoding="utf-8") as f:
            f.write("\n".join(insight_lines) + "\n")

        append_jsonl(
            MASTER_RUNS_PATH,
            [
                {
                    "run_id": run_id,
                    "start": run_started_at.isoformat(timespec="seconds"),
                    "end": run_ended_at.isoformat(timespec="seconds"),
                    "runtime_s": run_runtime_s,
                    "searches": [asdict(r) for r in results],
                    "run_unique_emails": len(all_emails_overall),
                    "run_unique_urls": len(all_job_urls_overall),
                }
            ],
        )

        logging.info("=" * 70)
        logging.info("ALL SEARCHES COMPLETE")
        logging.info(f"Summary file: {summary_path}")
        logging.info(f"MASTER emails:   {MASTER_EMAILS_PATH}")
        logging.info(f"MASTER urls:     {MASTER_URLS_PATH}")
        logging.info(f"MASTER posts:    {MASTER_POSTS_PATH}")
        logging.info(f"MASTER runs:     {MASTER_RUNS_PATH}")
        logging.info(f"MASTER insights: {MASTER_INSIGHTS_TXT}")
        logging.info("=" * 70)

        print("\n" + summary_text + "\n")

    finally:
        # driver.quit()
        pass


if __name__ == "__main__":
    main()