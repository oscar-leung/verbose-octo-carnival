"""
Gmail Job Tracker — scan Gmail for recruiter/ATS updates, track status in JSON.
───────────────────────────────────────────────────────────────────────────────
Fills the missing half of the pipeline: scripts 035–040 *send* applications;
this one *reads* the replies. It scans recent inbox mail from known ATS and
recruiter senders, classifies each message as applied / assessment / interview
/ offer / rejection / ghosted, and maintains job_tracker.json as the source of
truth. Optionally posts a summary to Slack and appends status rows to the same
Google Sheet used by library/gsheets.py.

Flow:
  1. Gmail API OAuth (token.json auto-refreshed on expiry)
  2. Search:  newer_than:{N}d  from:{ATS senders}  OR  subject:{keywords}
  3. Parse each message → (company, role, location, status, date)
  4. Diff against job_tracker.json → detect new entries + status transitions
  5. Write back the tracker; optionally Slack-notify and Sheets-sync

Usage:
  python 043_gmail_job_tracker.py                    # last 7 days
  python 043_gmail_job_tracker.py --days 30          # last 30 days (initial backfill)
  python 043_gmail_job_tracker.py --dry-run          # parse only, no file writes
  python 043_gmail_job_tracker.py --verbose          # debug logging
  python 043_gmail_job_tracker.py --no-slack --no-sheets

One-time setup:
  1. console.cloud.google.com → enable Gmail API
  2. APIs & Services → Credentials → Create OAuth client ID (Desktop app)
  3. Download as gmail_oauth_client.json in repo root
  4. First run opens browser for consent; writes gmail_token.json
  5. (optional) .env:
       SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
       GOOGLE_SERVICE_ACCOUNT_JSON=...   # already used by library/gsheets.py
       GOOGLE_SHEET_ID=...

Install:
  pip install google-api-python-client google-auth-oauthlib
"""

import argparse
import base64
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from email.utils import parseaddr, parsedate_to_datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
TRACKER_PATH = ROOT / "job_tracker.json"
OAUTH_CLIENT_PATH = ROOT / "gmail_oauth_client.json"
OAUTH_TOKEN_PATH = ROOT / "gmail_token.json"

# ── Gmail search ──────────────────────────────────────────────────────────────
# Narrow-ish set of senders where we expect real recruiter/ATS traffic.
# Anything matching these OR a strong subject keyword is fetched, then the
# classifier decides what to do with it.
ATS_SENDER_DOMAINS = [
    "linkedin.com",
    "greenhouse.io",
    "us.greenhouse-mail.io",
    "hire.lever.co",
    "lever.co",
    "workable.com",
    "ashbyhq.com",
    "workday.com",
    "myworkdayjobs.com",
    "myworkday.com",
    "jobvite.com",
    "smartrecruiters.com",
    "icims.com",
    "successfactors.com",
    "bamboohr.com",
    "recruitee.com",
    "eightfold.ai",
    "joinhandshake.com",
    "notify.joinhandshake.com",
    "indeed.com",
    "triplebyte.com",
    "hired.com",
    "dover.com",
    "ripplematch.com",
]

SUBJECT_KEYWORDS = [
    "your application",
    "application received",
    "thanks for applying",
    "thank you for applying",
    "next steps",
    "interview",
    "phone screen",
    "coding challenge",
    "assessment",
    "take-home",
    "offer",
    "unfortunately",
    "regret to inform",
    "not moving forward",
    "moving forward",
]

# ── Status classifier ─────────────────────────────────────────────────────────
# Order matters: OFFER beats INTERVIEW beats ASSESSMENT beats REJECTION beats
# APPLIED. Each entry is (status, compiled_regex).
STATUS_RULES = [
    ("offer", re.compile(
        r"(pleased to (?:extend|offer)|offer letter|we'?re excited to offer|"
        r"your offer|formal offer|offer of employment)",
        re.I)),
    ("interview", re.compile(
        r"(schedule (?:a|your|an)?\s*(?:phone|video|onsite|technical)?\s*"
        r"(?:interview|screen|conversation|chat)|"
        r"invite you to interview|like to (?:schedule|set up) (?:a|an) "
        r"(?:interview|call|chat)|"
        r"invitation to interview|"
        r"next round|final round|onsite interview|"
        r"phone screen|video interview|hiring manager)",
        re.I)),
    ("assessment", re.compile(
        r"(coding challenge|take[- ]home|online assessment|hackerrank|codility|"
        r"codesignal|technical assessment|skills assessment|work sample)",
        re.I)),
    ("rejection", re.compile(
        r"(unfortunately|regret to inform|not (?:be )?moving forward|"
        r"decided (?:to pursue|not to (?:move|proceed))|other candidates|"
        r"not to proceed|will not be proceeding|we'?ve decided to move forward "
        r"with other|no longer under consideration|"
        r"position has been filled|wish you (?:the best|success))",
        re.I)),
    ("applied", re.compile(
        r"(application (?:has been )?received|thanks? for applying|"
        r"thank you for (?:your interest|applying)|we have received your "
        r"application|successfully submitted|your application is under review)",
        re.I)),
]

STATUS_PRIORITY = {"applied": 0, "assessment": 1, "interview": 2, "offer": 3, "rejection": 3}

# ── Dataclasses ───────────────────────────────────────────────────────────────
@dataclass
class ParsedEmail:
    gmail_id: str
    thread_id: str
    from_name: str
    from_addr: str
    subject: str
    body_preview: str
    received: str            # ISO
    company: str
    role: str
    location: str
    status: str              # one of STATUS_RULES keys, or "unknown"

    def key(self) -> str:
        return f"{self.company.lower()}|{self.role.lower()}" if self.company else f"thread|{self.thread_id}"


@dataclass
class TrackerEntry:
    company: str
    role: str
    location: str = ""
    status: str = "applied"
    first_seen: str = ""
    last_updated: str = ""
    gmail_thread_ids: list = field(default_factory=list)
    history: list = field(default_factory=list)   # [{status, date, gmail_id, subject}]


# ── Gmail API ─────────────────────────────────────────────────────────────────
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def gmail_service():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError:
        sys.exit("pip install google-api-python-client google-auth-oauthlib")

    creds = None
    if OAUTH_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(OAUTH_TOKEN_PATH), GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_PATH.exists():
                sys.exit(f"Missing {OAUTH_CLIENT_PATH.name}. See file header for setup.")
            flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_CLIENT_PATH), GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        OAUTH_TOKEN_PATH.write_text(creds.to_json())
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def build_query(days: int) -> str:
    from_clause = " OR ".join(f"from:{d}" for d in ATS_SENDER_DOMAINS)
    subj_clause = " OR ".join(f'subject:"{k}"' for k in SUBJECT_KEYWORDS)
    return f"newer_than:{days}d (({from_clause}) OR ({subj_clause}))"


def list_message_ids(service, query: str) -> list[str]:
    ids, page_token = [], None
    while True:
        resp = service.users().messages().list(
            userId="me", q=query, pageToken=page_token, maxResults=500
        ).execute()
        ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


def _decode_part(data: str) -> str:
    return base64.urlsafe_b64decode(data.encode()).decode(errors="replace")


def _extract_body(payload: dict) -> str:
    """Walk MIME tree and return first text/plain (fallback text/html stripped)."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return _decode_part(payload["body"]["data"])
    for part in payload.get("parts", []) or []:
        text = _extract_body(part)
        if text:
            return text
    # fallback to text/html stripped
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        html = _decode_part(payload["body"]["data"])
        return re.sub(r"<[^>]+>", " ", html)
    return ""


def fetch_message(service, msg_id: str) -> dict:
    return service.users().messages().get(userId="me", id=msg_id, format="full").execute()


# ── Parsing ───────────────────────────────────────────────────────────────────
def header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


# "Greenhouse <no-reply@us.greenhouse-mail.io>" → display name often holds company
COMPANY_IN_NAME = re.compile(r"^(?P<name>[^<]+?)\s*(?:<|$)")

# Subject patterns we see a lot:
#   "Your application to Acme Co for Software Engineer"
#   "Thanks for applying to Acme Co"
#   "Your Acme Co application: Software Engineer"
#   "[Acme Co] Interview invitation — Software Engineer"
SUBJECT_PATTERNS = [
    re.compile(r"application to\s+(?P<company>[^-–—:|]+?)(?:\s+for\s+(?P<role>.+))?$", re.I),
    re.compile(r"applying to\s+(?P<company>[^-–—:|]+?)(?:[:\-–—]\s*(?P<role>.+))?$", re.I),
    re.compile(r"your\s+(?P<company>.+?)\s+application[:\-–—\s]+(?P<role>.+)?$", re.I),
    re.compile(r"\[(?P<company>[^\]]+)\]\s*.*?(?:[-–—:]\s*(?P<role>.+))?$", re.I),
    re.compile(r"(?P<role>.+?)\s+at\s+(?P<company>[^-–—:|]+?)$", re.I),
]


def guess_company(from_name: str, from_addr: str, subject: str, body: str) -> str:
    for pat in SUBJECT_PATTERNS:
        m = pat.search(subject)
        if m:
            c = (m.groupdict().get("company") or "").strip(" .,-–—:|")
            if c and c.lower() not in {"linkedin", "greenhouse", "lever", "workday"}:
                return c
    # "Team Acme" or "Acme Recruiting" in the from name
    if from_name:
        nm = from_name.strip().strip('"')
        nm = re.sub(r"\b(team|recruiting|talent|careers|hiring|hr)\b", "", nm, flags=re.I).strip()
        domain = from_addr.split("@")[-1].lower() if "@" in from_addr else ""
        # skip generic ATS branding
        if nm and not any(d in domain for d in ["linkedin.com", "greenhouse", "lever", "workday",
                                                "indeed.com", "joinhandshake"]):
            return nm
    # Body: "Thank you for applying to Acme Co"
    m = re.search(r"applying to\s+([A-Z][\w&.,'’\- ]{1,60})", body)
    if m:
        return m.group(1).strip(" .,-–—:|")
    return ""


def guess_role(subject: str, body: str) -> str:
    for pat in SUBJECT_PATTERNS:
        m = pat.search(subject)
        if m:
            r = (m.groupdict().get("role") or "").strip(" .,-–—:|")
            if r and len(r) < 120:
                return r
    m = re.search(r"(?:for|role of|position of|position[:\-–—]|role[:\-–—])\s+"
                  r"([A-Z][\w /&,+\-]{2,80})", body)
    if m:
        return m.group(1).strip(" .,-–—:|")
    return ""


def guess_location(body: str) -> str:
    m = re.search(r"(?:Location|Based in|Office)[:\s]+([A-Z][\w ,./\-]{2,60})", body)
    if m:
        return m.group(1).strip(" .,-–—:|")
    if re.search(r"\bremote\b", body, re.I):
        return "Remote"
    return ""


def classify_status(subject: str, body: str) -> str:
    haystack = f"{subject}\n{body[:2000]}"
    best = ("unknown", -1)
    for status, pat in STATUS_RULES:
        if pat.search(haystack):
            rank = STATUS_PRIORITY.get(status, 0)
            if rank > best[1]:
                best = (status, rank)
    return best[0]


def parse_email(msg: dict) -> Optional[ParsedEmail]:
    subject = header(msg, "Subject")
    from_raw = header(msg, "From")
    date_raw = header(msg, "Date")
    from_name, from_addr = parseaddr(from_raw)
    try:
        received = parsedate_to_datetime(date_raw).astimezone(timezone.utc).isoformat()
    except Exception:
        received = datetime.now(timezone.utc).isoformat()

    body = _extract_body(msg.get("payload", {}))
    status = classify_status(subject, body)
    if status == "unknown":
        return None    # nothing actionable — don't pollute the tracker

    return ParsedEmail(
        gmail_id=msg["id"],
        thread_id=msg["threadId"],
        from_name=from_name,
        from_addr=from_addr,
        subject=subject,
        body_preview=body[:240].replace("\n", " ").strip(),
        received=received,
        company=guess_company(from_name, from_addr, subject, body),
        role=guess_role(subject, body),
        location=guess_location(body),
        status=status,
    )


# ── Tracker file ──────────────────────────────────────────────────────────────
def load_tracker() -> dict[str, TrackerEntry]:
    if not TRACKER_PATH.exists():
        return {}
    data = json.loads(TRACKER_PATH.read_text())
    return {k: TrackerEntry(**v) for k, v in data.get("entries", {}).items()}


def save_tracker(entries: dict[str, TrackerEntry]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entries": {k: asdict(v) for k, v in entries.items()},
    }
    TRACKER_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))


def merge(entries: dict[str, TrackerEntry], email: ParsedEmail) -> tuple[bool, bool]:
    """Returns (is_new_entry, is_status_change)."""
    k = email.key()
    now = email.received
    is_new = k not in entries
    is_change = False

    entry = entries.get(k) or TrackerEntry(
        company=email.company,
        role=email.role,
        location=email.location,
        status=email.status,
        first_seen=now,
    )
    # Only promote status forward (offer/rejection are terminal, interview > applied, etc.)
    if not is_new and STATUS_PRIORITY.get(email.status, 0) > STATUS_PRIORITY.get(entry.status, -1):
        entry.status = email.status
        is_change = True
    # Fill in missing fields opportunistically
    entry.company = entry.company or email.company
    entry.role = entry.role or email.role
    entry.location = entry.location or email.location
    entry.last_updated = now
    if email.thread_id not in entry.gmail_thread_ids:
        entry.gmail_thread_ids.append(email.thread_id)
    # History append only if this gmail_id is new
    if not any(h.get("gmail_id") == email.gmail_id for h in entry.history):
        entry.history.append({
            "status": email.status,
            "date": now,
            "gmail_id": email.gmail_id,
            "subject": email.subject,
        })

    entries[k] = entry
    return is_new, is_change


# ── Notifications ─────────────────────────────────────────────────────────────
def post_to_slack(summary: str) -> None:
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url:
        return
    try:
        import requests
        requests.post(url, json={"text": summary}, timeout=10)
    except Exception as e:
        log.warning(f"[slack] post failed: {e}")


def sync_to_sheets(new_rows: list[ParsedEmail]) -> None:
    if not new_rows:
        return
    try:
        from library.gsheets import sync_jobs
    except Exception as e:
        log.info(f"[sheets] skipped: {e}")
        return
    jobs = [{
        "job_id": e.thread_id,
        "timestamp": e.received,
        "title": e.role,
        "company": e.company,
        "location": e.location,
        "status": e.status,
        "notes": e.subject[:200],
    } for e in new_rows]
    sync_jobs(jobs, platform="Gmail")


# ── Main ──────────────────────────────────────────────────────────────────────
log = logging.getLogger("gmail_job_tracker")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--no-slack", action="store_true")
    parser.add_argument("--no-sheets", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    service = gmail_service()
    query = build_query(args.days)
    log.info(f"Gmail query: {query}")

    msg_ids = list_message_ids(service, query)
    log.info(f"Found {len(msg_ids)} candidate messages in the last {args.days}d")

    entries = load_tracker()
    new_count = change_count = parsed_count = 0
    notable_events: list[ParsedEmail] = []

    for mid in msg_ids:
        msg = fetch_message(service, mid)
        parsed = parse_email(msg)
        if not parsed:
            continue
        parsed_count += 1
        is_new, is_change = merge(entries, parsed)
        if is_new:
            new_count += 1
            notable_events.append(parsed)
        if is_change:
            change_count += 1
            notable_events.append(parsed)

    log.info(f"Parsed {parsed_count} recruiting messages — "
             f"{new_count} new entries, {change_count} status changes")

    if args.dry_run:
        log.info("--dry-run: skipping tracker write, Slack, and Sheets sync")
        for e in notable_events[:20]:
            log.info(f"  · [{e.status}] {e.company or '?'} — {e.role or '?'} "
                     f"({e.received[:10]})  {e.subject!r}")
        return

    save_tracker(entries)
    log.info(f"Wrote {TRACKER_PATH}")

    if notable_events and not args.no_slack:
        lines = [f"*Gmail Job Tracker* — {new_count} new, {change_count} status changes"]
        for e in notable_events[:15]:
            lines.append(f"• [{e.status}] {e.company or '?'} — {e.role or '?'} "
                         f"_{e.received[:10]}_")
        post_to_slack("\n".join(lines))

    if notable_events and not args.no_sheets:
        sync_to_sheets(notable_events)


if __name__ == "__main__":
    main()
