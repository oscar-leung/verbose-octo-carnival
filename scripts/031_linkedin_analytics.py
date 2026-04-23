"""
linkedin_analytics.py
─────────────────────
Reads EVERYTHING in your linkedin_runs folder:
  • MASTER_RUNS.jsonl     — per-run stats
  • MASTER_ALL_EMAILS.txt — all emails ever collected
  • MASTER_ALL_JOB_POST_URLS.txt
  • MASTER_INSIGHTS.txt
  • Every RUN.log         — parses post counts, scroll events, timing
  • Every RUN_SUMMARY.txt — parses search-level stats

Outputs:
  • Printed report to terminal
  • ANALYTICS_REPORT.txt saved to _MASTER folder

Usage:
  python3 linkedin_analytics.py
  python3 linkedin_analytics.py --dir /path/to/linkedin_runs
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
DEFAULT_OUT_DIR  = "linkedin_runs"
MASTER_SUBDIR    = "_MASTER"

# ─────────────────────────────────────────────
# REGEX
# ─────────────────────────────────────────────
EMAIL_RE         = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
LOG_POST_RE      = re.compile(r"\[POST\s+\d+\]\s+emails=(\d+)")
LOG_SCROLL_RE    = re.compile(r"Scroll check: posts_before=(\d+) posts_after=(\d+) loaded=(True|False)")
LOG_DONE_RE      = re.compile(r"Done: posts=(\d+) \| posts_with_email=(\d+) \| unique_emails=(\d+)")
LOG_SEARCH_RE    = re.compile(r"\[(\d+)/(\d+)\] Search: (.+)")
LOG_START_RE     = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})")
LOG_EMAIL_HIT_RE = re.compile(r"emails=(\d+) \| (.+@.+\..+)$")
LOG_RUNTIME_RE   = re.compile(r"Total runtime \(s\): ([\d.]+)")
SUMMARY_POSTS_RE = re.compile(r"Total new posts scanned\s*:\s*(\d+)", re.IGNORECASE)
SUMMARY_EMAIL_RE = re.compile(r"Unique emails.*?:\s*(\d+)", re.IGNORECASE)
SUMMARY_URLS_RE  = re.compile(r"Unique job.*?urls.*?:\s*(\d+)", re.IGNORECASE)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def safe_read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def read_lines_set(path: str) -> set:
    lines = set()
    txt = safe_read(path)
    for line in txt.splitlines():
        line = line.strip()
        if line:
            lines.add(line)
    return lines


def read_jsonl(path: str) -> list:
    records = []
    txt = safe_read(path)
    for line in txt.splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    return records


def bar(value: int, max_value: int, width: int = 30, char: str = "█") -> str:
    if max_value == 0:
        return ""
    filled = int(round(value / max_value * width))
    return char * filled + "░" * (width - filled)


# ─────────────────────────────────────────────
# LOG PARSER
# ─────────────────────────────────────────────
def parse_run_log(log_path: str) -> dict:
    """Parse a RUN.log file into structured stats."""
    txt = safe_read(log_path)
    lines = txt.splitlines()
    if not lines:
        return {}

    stats = {
        "log_path":         log_path,
        "searches":         [],
        "total_posts":      0,
        "total_with_email": 0,
        "total_scrolls":    0,
        "failed_scrolls":   0,
        "start_time":       None,
        "end_time":         None,
        "runtime_s":        None,
        "emails_found":     [],
    }

    current_search = None

    for line in lines:
        # Timestamps
        ts_match = LOG_START_RE.match(line)
        ts = None
        if ts_match:
            try:
                ts = datetime.strptime(ts_match.group(1), "%Y-%m-%d %H:%M:%S")
                if stats["start_time"] is None:
                    stats["start_time"] = ts
                stats["end_time"] = ts
            except Exception:
                pass

        # Search label
        s_match = LOG_SEARCH_RE.search(line)
        if s_match:
            current_search = {
                "idx":         int(s_match.group(1)),
                "total":       int(s_match.group(2)),
                "label":       s_match.group(3).strip(),
                "posts":       0,
                "with_email":  0,
                "unique_emails": 0,
                "scrolls":     0,
                "failed_scrolls": 0,
            }
            stats["searches"].append(current_search)

        # Scroll events
        sc_match = LOG_SCROLL_RE.search(line)
        if sc_match:
            stats["total_scrolls"] += 1
            if current_search:
                current_search["scrolls"] += 1
            if sc_match.group(3) == "False":
                stats["failed_scrolls"] += 1
                if current_search:
                    current_search["failed_scrolls"] += 1

        # Done line
        done_match = LOG_DONE_RE.search(line)
        if done_match and current_search:
            current_search["posts"]         = int(done_match.group(1))
            current_search["with_email"]    = int(done_match.group(2))
            current_search["unique_emails"] = int(done_match.group(3))
            stats["total_posts"]      += current_search["posts"]
            stats["total_with_email"] += current_search["with_email"]

        # Inline email hits
        eh_match = LOG_EMAIL_HIT_RE.search(line)
        if eh_match and int(eh_match.group(1)) > 0:
            found_emails = EMAIL_RE.findall(line)
            for e in found_emails:
                stats["emails_found"].append(e.lower())

        # Runtime
        rt_match = LOG_RUNTIME_RE.search(line)
        if rt_match:
            stats["runtime_s"] = float(rt_match.group(1))

    # Compute runtime from timestamps if not explicit
    if stats["runtime_s"] is None and stats["start_time"] and stats["end_time"]:
        stats["runtime_s"] = (stats["end_time"] - stats["start_time"]).total_seconds()

    return stats


# ─────────────────────────────────────────────
# MASTER JSONL PARSER
# ─────────────────────────────────────────────
def parse_master_runs(path: str) -> list:
    return read_jsonl(path)


# ─────────────────────────────────────────────
# FOLDER SCANNER
# ─────────────────────────────────────────────
def scan_run_folders(out_dir: str) -> list:
    """Return sorted list of run folder paths."""
    folders = []
    if not os.path.isdir(out_dir):
        return folders
    for name in sorted(os.listdir(out_dir)):
        path = os.path.join(out_dir, name)
        if os.path.isdir(path) and name.startswith("run_") and name != MASTER_SUBDIR:
            folders.append(path)
    return folders


def find_result_txts(run_dir: str) -> list:
    """Find all *_results.txt files in a run folder."""
    files = []
    for name in sorted(os.listdir(run_dir)):
        if name.endswith("_results.txt"):
            files.append(os.path.join(run_dir, name))
    return files


def count_posts_in_result_txt(path: str) -> dict:
    txt = safe_read(path)
    post_count  = len(re.findall(r"^\[POST #\d+\]", txt, re.MULTILINE))
    emails      = EMAIL_RE.findall(txt)
    urls        = re.findall(r"https?://www\.linkedin\.com/jobs/view/\d+", txt)
    return {
        "posts":  post_count,
        "emails": [e.lower() for e in emails],
        "urls":   list(set(urls)),
    }


# ─────────────────────────────────────────────
# MAIN ANALYTICS ENGINE
# ─────────────────────────────────────────────
def run_analytics(out_dir: str) -> str:
    master_dir          = os.path.join(out_dir, MASTER_SUBDIR)
    master_emails_path  = os.path.join(master_dir, "MASTER_ALL_EMAILS.txt")
    master_urls_path    = os.path.join(master_dir, "MASTER_ALL_JOB_POST_URLS.txt")
    master_runs_path    = os.path.join(master_dir, "MASTER_RUNS.jsonl")
    master_insights_path= os.path.join(master_dir, "MASTER_INSIGHTS.txt")

    # ── Load master data ──────────────────────────────────────
    all_emails      = read_lines_set(master_emails_path)
    all_urls        = read_lines_set(master_urls_path)
    master_runs     = parse_master_runs(master_runs_path)
    insights_text   = safe_read(master_insights_path)
    run_folders     = scan_run_folders(out_dir)

    # ── Parse every run log ───────────────────────────────────
    log_stats_per_run = {}
    for rf in run_folders:
        log_path = os.path.join(rf, "RUN.log")
        if os.path.exists(log_path):
            log_stats_per_run[rf] = parse_run_log(log_path)

    # ── Aggregate from MASTER_RUNS.jsonl ──────────────────────
    total_runtime_s     = 0.0
    total_searches_ok   = 0
    total_searches_err  = 0
    total_new_emails    = 0
    total_new_urls      = 0
    runs_by_id          = {}

    for r in master_runs:
        total_runtime_s    += r.get("runtime_s", 0)
        total_searches_ok  += r.get("ok_searches", r.get("run_unique_emails", 0) and 0)
        total_searches_err += r.get("error_searches", 0)
        total_new_emails   += r.get("new_emails", 0)
        total_new_urls     += r.get("new_urls", 0)
        runs_by_id[r.get("run_id", "")] = r

    # If ok_searches not in older records, count from searches list
    for r in master_runs:
        if "ok_searches" not in r:
            searches = r.get("searches", [])
            ok  = sum(1 for s in searches if not s.get("error"))
            err = sum(1 for s in searches if s.get("error"))
            total_searches_ok  += ok
            total_searches_err += err

    # ── Aggregate from log files (fallback / supplement) ──────
    log_total_posts      = 0
    log_total_with_email = 0
    log_total_scrolls    = 0
    log_failed_scrolls   = 0
    log_all_emails       = []

    for rf, ls in log_stats_per_run.items():
        log_total_posts      += ls.get("total_posts", 0)
        log_total_with_email += ls.get("total_with_email", 0)
        log_total_scrolls    += ls.get("total_scrolls", 0)
        log_failed_scrolls   += ls.get("failed_scrolls", 0)
        log_all_emails       += ls.get("emails_found", [])

    # ── Email domain analysis ─────────────────────────────────
    domains = []
    for e in all_emails:
        if "@" in e:
            domains.append(e.split("@", 1)[1].lower())
    domain_counts = Counter(domains).most_common(20)

    # ── Email frequency (who shows up most) ───────────────────
    email_freq = Counter(log_all_emails).most_common(15)

    # ── Per-run timeline ──────────────────────────────────────
    run_timeline = []
    for r in sorted(master_runs, key=lambda x: x.get("start", "")):
        run_id   = r.get("run_id", "?")
        start    = r.get("start", "?")
        end      = r.get("end", "?")
        rt       = r.get("runtime_s", 0)
        emails   = r.get("new_emails", r.get("run_unique_emails", 0))
        urls     = r.get("new_urls", r.get("run_unique_urls", 0))
        m_e      = r.get("master_emails_after", "?")
        m_u      = r.get("master_urls_after", "?")
        searches = r.get("searches", [])
        ok_s     = r.get("ok_searches", sum(1 for s in searches if not s.get("error")))
        err_s    = r.get("error_searches", sum(1 for s in searches if s.get("error")))
        run_timeline.append({
            "run_id":  run_id,
            "start":   start,
            "runtime": rt,
            "emails":  emails,
            "urls":    urls,
            "master_emails": m_e,
            "master_urls":   m_u,
            "ok":   ok_s,
            "err":  err_s,
        })

    # ── Best performing searches ──────────────────────────────
    search_perf = defaultdict(lambda: {"emails": 0, "posts": 0, "count": 0})
    for r in master_runs:
        for s in r.get("searches", []):
            label = s.get("search_label", "?")
            search_perf[label]["emails"] += s.get("unique_emails", 0)
            search_perf[label]["posts"]  += s.get("total_posts_seen", 0)
            search_perf[label]["count"]  += 1

    top_searches = sorted(
        search_perf.items(), key=lambda x: x[1]["emails"], reverse=True
    )[:15]

    # ── Error analysis ────────────────────────────────────────
    error_counts = Counter()
    for r in master_runs:
        for s in r.get("searches", []):
            if s.get("error"):
                err_short = s["error"][:60]
                error_counts[err_short] += 1

    # ── Scroll efficiency ─────────────────────────────────────
    scroll_success_rate = 0.0
    if log_total_scrolls > 0:
        scroll_success_rate = (log_total_scrolls - log_failed_scrolls) / log_total_scrolls * 100

    # ── Email hit rate ────────────────────────────────────────
    email_hit_rate = 0.0
    if log_total_posts > 0:
        email_hit_rate = log_total_with_email / log_total_posts * 100

    # ── Searches per run ─────────────────────────────────────
    avg_searches = 0
    if master_runs:
        avg_searches = sum(
            len(r.get("searches", [])) for r in master_runs
        ) / len(master_runs)

    # ══════════════════════════════════════════════════════════
    # BUILD REPORT
    # ══════════════════════════════════════════════════════════
    lines = []
    W = 80

    def section(title):
        lines.append("\n" + "═" * W)
        lines.append(f"  {title}")
        lines.append("═" * W)

    def row(label, value, note=""):
        note_str = f"  ({note})" if note else ""
        lines.append(f"  {label:<38} {str(value):>15}{note_str}")

    def divider():
        lines.append("  " + "─" * (W - 2))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("═" * W)
    lines.append(f"  LINKEDIN SCRAPER — MASTER ANALYTICS REPORT")
    lines.append(f"  Generated : {now}")
    lines.append(f"  Data dir  : {os.path.abspath(out_dir)}")
    lines.append("═" * W)

    # ── OVERVIEW ──────────────────────────────────────────────
    section("📊 ALL-TIME OVERVIEW")
    row("Total runs completed",         len(master_runs))
    row("Total runtime (all runs)",     fmt_duration(total_runtime_s))
    row("Avg runtime per run",          fmt_duration(total_runtime_s / max(len(master_runs), 1)))
    divider()
    row("Master unique emails",         len(all_emails))
    row("Master unique URLs",           len(all_urls))
    divider()
    row("Total posts read (from logs)", f"{log_total_posts:,}")
    row("Posts containing emails",      f"{log_total_with_email:,}")
    row("Email hit rate",               f"{email_hit_rate:.2f}%", "posts with at least 1 email")
    divider()
    row("Total scroll events",          f"{log_total_scrolls:,}")
    row("Successful scrolls",           f"{log_total_scrolls - log_failed_scrolls:,}")
    row("Failed scrolls (no new posts)",f"{log_failed_scrolls:,}")
    row("Scroll success rate",          f"{scroll_success_rate:.1f}%")
    divider()
    row("Total searches OK",            total_searches_ok)
    row("Total searches errored",       total_searches_err)
    row("Avg searches per run",         f"{avg_searches:.1f}")

    # ── RUN TIMELINE ──────────────────────────────────────────
    section("📅 RUN TIMELINE  (oldest → newest)")
    lines.append(f"  {'Run ID':<20} {'Start':<20} {'Runtime':>10} {'+Emails':>8} {'+URLs':>7} {'Total✉':>8} {'OK':>5} {'ERR':>5}")
    lines.append("  " + "─" * (W - 2))
    max_emails = max((r["emails"] for r in run_timeline), default=1)
    for r in run_timeline:
        bar_str = bar(r["emails"], max_emails, width=12)
        lines.append(
            f"  {r['run_id']:<20} "
            f"{str(r['start'])[:19]:<20} "
            f"{fmt_duration(r['runtime']):>10} "
            f"{r['emails']:>+8} "
            f"{r['urls']:>+7} "
            f"{str(r['master_emails']):>8} "
            f"{r['ok']:>5} "
            f"{r['err']:>5}  "
            f"{bar_str}"
        )

    # ── EMAIL GROWTH ──────────────────────────────────────────
    section("📈 EMAIL COLLECTION GROWTH")
    running = 0
    for r in run_timeline:
        running += r["emails"]
        pct = running / max(len(all_emails), 1) * 100
        bar_str = bar(running, len(all_emails), width=25)
        lines.append(f"  {r['run_id']:<20} cumulative={running:>5}  {bar_str}  {pct:.0f}%")

    # ── TOP EMAIL DOMAINS ─────────────────────────────────────
    section("🏢 TOP EMAIL DOMAINS  (all-time)")
    max_dom = domain_counts[0][1] if domain_counts else 1
    for dom, cnt in domain_counts:
        bar_str = bar(cnt, max_dom, width=25)
        lines.append(f"  {dom:<35} {cnt:>4}  {bar_str}")

    # ── TOP RECRUITERS ────────────────────────────────────────
    section("🔁 MOST RECURRING EMAILS  (seen across multiple searches)")
    if email_freq:
        for email, cnt in email_freq:
            lines.append(f"  {email:<45} seen {cnt}x")
    else:
        lines.append("  (log-level email tracking not available — run newer v4 scraper)")

    # ── ALL EMAILS ────────────────────────────────────────────
    section(f"📧 ALL UNIQUE EMAILS  ({len(all_emails)} total)")
    for e in sorted(all_emails):
        lines.append(f"  {e}")

    # ── ALL URLS ──────────────────────────────────────────────
    section(f"🔗 ALL UNIQUE JOB / POST URLS  ({len(all_urls)} total)")
    for u in sorted(all_urls):
        lines.append(f"  {u}")

    # ── BEST SEARCHES ─────────────────────────────────────────
    section("🏆 TOP 15 SEARCH KEYWORDS  (by emails collected)")
    lines.append(f"  {'Search label':<55} {'Emails':>7} {'Posts':>8} {'Runs':>5}")
    lines.append("  " + "─" * (W - 2))
    max_se = top_searches[0][1]["emails"] if top_searches else 1
    for label, stats in top_searches:
        bar_str = bar(stats["emails"], max_se, width=12)
        lines.append(
            f"  {label[:55]:<55} "
            f"{stats['emails']:>7} "
            f"{stats['posts']:>8} "
            f"{stats['count']:>5}  "
            f"{bar_str}"
        )

    # ── ERROR ANALYSIS ────────────────────────────────────────
    if error_counts:
        section("⚠️  TOP ERRORS")
        for err, cnt in error_counts.most_common(10):
            lines.append(f"  {cnt:>4}x  {err}")

    # ── PER-RUN DETAILS ───────────────────────────────────────
    section("🔍 PER-RUN DETAIL  (from MASTER_RUNS.jsonl)")
    for r in sorted(master_runs, key=lambda x: x.get("start", ""), reverse=True):
        run_id   = r.get("run_id", "?")
        start    = r.get("start", "?")
        end      = r.get("end", "?")
        rt       = r.get("runtime_s", 0)
        searches = r.get("searches", [])
        ok_s     = r.get("ok_searches", sum(1 for s in searches if not s.get("error")))
        err_s    = r.get("error_searches", sum(1 for s in searches if s.get("error")))
        new_e    = r.get("new_emails", r.get("run_unique_emails", "?"))
        new_u    = r.get("new_urls", r.get("run_unique_urls", "?"))

        lines.append(f"\n  ── {run_id} ──────────────────────────────────────────")
        lines.append(f"     Start    : {start}")
        lines.append(f"     End      : {end}")
        lines.append(f"     Runtime  : {fmt_duration(rt)}")
        lines.append(f"     Searches : {len(searches)} total  ({ok_s} OK, {err_s} errors)")
        lines.append(f"     New emails this run : {new_e}")
        lines.append(f"     New URLs this run   : {new_u}")

        # Show searches that found emails
        email_searches = [s for s in searches if s.get("unique_emails", 0) > 0]
        if email_searches:
            lines.append(f"     Searches with emails ({len(email_searches)}):")
            for s in sorted(email_searches, key=lambda x: x.get("unique_emails", 0), reverse=True)[:10]:
                lines.append(
                    f"       +{s.get('unique_emails',0)} emails  "
                    f"{s.get('posts_with_emails',0)} posts  "
                    f"{s.get('search_label','?')[:50]}"
                )

    # ── LOG SUMMARY ───────────────────────────────────────────
    section("📋 PER-RUN LOG STATS  (parsed from RUN.log files)")
    lines.append(f"  {'Run folder':<25} {'Posts':>7} {'w/Email':>8} {'Scrolls':>9} {'Failed':>7} {'Runtime':>10}")
    lines.append("  " + "─" * (W - 2))
    for rf in sorted(log_stats_per_run.keys()):
        ls = log_stats_per_run[rf]
        folder_name = os.path.basename(rf)
        rt_str = fmt_duration(ls.get("runtime_s") or 0)
        lines.append(
            f"  {folder_name:<25} "
            f"{ls.get('total_posts', 0):>7,} "
            f"{ls.get('total_with_email', 0):>8,} "
            f"{ls.get('total_scrolls', 0):>9,} "
            f"{ls.get('failed_scrolls', 0):>7,} "
            f"{rt_str:>10}"
        )

    # ── FOOTER ────────────────────────────────────────────────
    lines.append("\n" + "═" * W)
    lines.append(f"  END OF REPORT  |  {now}")
    lines.append(f"  linkedin_analytics.py  |  verbose-octo-carnival")
    lines.append("═" * W)

    return "\n".join(lines)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LinkedIn Scraper Analytics")
    parser.add_argument(
        "--dir",
        default=DEFAULT_OUT_DIR,
        help=f"Path to linkedin_runs folder (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Print report but don't save to file",
    )
    args = parser.parse_args()

    out_dir = args.dir
    if not os.path.isdir(out_dir):
        print(f"❌ Directory not found: {out_dir}")
        print("   Run from your project root, or pass --dir /full/path/to/linkedin_runs")
        sys.exit(1)

    print(f"\n🔍 Scanning {os.path.abspath(out_dir)} ...\n")

    report = run_analytics(out_dir)

    print(report)

    if not args.no_save:
        master_dir  = os.path.join(out_dir, MASTER_SUBDIR)
        os.makedirs(master_dir, exist_ok=True)
        out_path    = os.path.join(master_dir, "ANALYTICS_REPORT.txt")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        print(f"\n✅ Report saved to: {out_path}\n")


if __name__ == "__main__":
    main()
