"""
Gmail Job Tracker — scan Gmail for recruiter/ATS updates, track status in JSON.
───────────────────────────────────────────────────────────────────────────────
Fills the missing half of the pipeline: scripts 035–042 *send* applications;
this one *reads* the inbox. Each scanned message is dispatched into one of
four buckets and written to a dedicated store in the repo root:

  application_reply  → job_tracker.json   (applied → ... → offer/rejection)
  recruiter_outreach → contacts.json      (recruiters / headhunters / agencies)
  job_alert          → alerts.json        (job rows surfaced in digests)
  unknown            → ignored

Flow:
  1. Gmail API OAuth (token.json auto-refreshed on expiry)
  2. Search:  newer_than:{N}d  (from:{senders}  OR  subject:{keywords})
  3. Classify each message; route to the matching parser
  4. Diff against the per-bucket store → detect new + status changes
  5. Write back; optionally Slack-notify and Sheets-sync application replies

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
import hashlib
import json
import logging
import os
import re
import sys
from collections import Counter
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
CONTACTS_PATH = ROOT / "contacts.json"
ALERTS_PATH = ROOT / "alerts.json"
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

# ── Recruiter / agency / job-alert detection ─────────────────────────────────
# Cold-outreach senders. Anything from these domains, when the body has
# recruiter phrasing, becomes a Contact instead of a tracker entry.
RECRUITER_AGENCY_DOMAINS = [
    "randstad.com", "roberthalf.com", "rht.com", "aerotek.com",
    "insightglobal.com", "kforce.com", "modis.com", "akkodis.com",
    "experis.com", "manpowergroup.com", "manpower.com",
    "tek-systems.com", "teksystems.com", "creativecircle.com",
    "trueblue.com", "adeccogroup.com", "adecco.com",
    "allegisgroup.com", "kellyservices.com", "robertwalters.com",
    "michaelpage.com", "hays.com", "harveynashgroup.com",
    "harnham.com", "vacoholding.com", "vaco.com",
    "brookwoodgroup.com",
]

# Senders that ship job-listing digests (treated as alerts, not interactions).
JOB_ALERT_SENDERS = {
    "jobs-noreply@linkedin.com", "jobalerts-noreply@linkedin.com",
    "jobs@linkedin.com", "alerts@indeed.com", "alert@indeed.com",
    "noreply@indeed.com", "noreply@joinhandshake.com",
    "jobs@joinhandshake.com", "noreply@glassdoor.com",
    "alerts@glassdoor.com", "noreply@ziprecruiter.com",
    "alerts@ziprecruiter.com", "jobalerts@dice.com",
    "alerts@simplyhired.com", "jobs@monster.com",
}

RECRUITER_PHRASES_RE = re.compile(
    r"(came across your (?:profile|background|resume)|caught my eye|"
    r"reach(?:ed|ing) out (?:about|regarding)|(?:would|i'?d) love to "
    r"(?:chat|connect|discuss|set up a)|"
    r"open to (?:new|a) opportunit|recruiter at|"
    r"talent (?:acquisition|partner)|head ?hunter|"
    r"interested in your (?:background|profile|experience)|"
    r"(?:have|got) an (?:exciting|interesting) (?:role|opportunity)|"
    r"hiring (?:for|at) [A-Z]|looking for a (?:talented|skilled))",
    re.I,
)

JOB_ALERT_SUBJECT_RE = re.compile(
    r"(jobs? (?:you may be interested in|for you|matching|of the day)|"
    r"new (?:jobs|matches|listings)|job alerts?|"
    r"top (?:jobs|matches) for|recommended jobs?|"
    r"weekly job digest|jobs in [\w ]+|"
    r"\d+ new (?:jobs|opportunities))",
    re.I,
)

# Listing pattern inside a digest body — best-effort, errs toward false negatives.
# Anchored to single lines so adjacent listings don't run together.
JOB_LISTING_RE = re.compile(
    r"^(?P<title>[A-Z][^\n]{3,90}?)\s+(?:at|@|—|-|·)\s+(?P<company>[A-Z][^\n]{1,60}?)\s*$",
    re.MULTILINE,
)

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


@dataclass
class Contact:
    email: str
    name: str = ""
    company: str = ""
    kind: str = "recruiter"          # recruiter | agency | hiring_manager | unknown
    first_seen: str = ""
    last_seen: str = ""
    message_count: int = 0
    subjects: list = field(default_factory=list)        # capped, most recent first
    gmail_thread_ids: list = field(default_factory=list)


@dataclass
class JobAlert:
    id: str                    # hash of source|company|role
    source: str                # linkedin | indeed | glassdoor | ziprecruiter | ...
    company: str
    role: str
    url: str = ""
    location: str = ""
    first_seen: str = ""
    last_seen: str = ""
    seen_count: int = 1
    gmail_message_ids: list = field(default_factory=list)
    seen_by_user: bool = False


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
    senders = list(set(
        ATS_SENDER_DOMAINS
        + RECRUITER_AGENCY_DOMAINS
        + [s.split("@")[-1] for s in JOB_ALERT_SENDERS]
    ))
    subj = SUBJECT_KEYWORDS + [
        "jobs you may be interested in", "new jobs", "job alert",
        "recommended jobs", "matching your search", "opportunity",
    ]
    from_clause = " OR ".join(f"from:{d}" for d in senders)
    subj_clause = " OR ".join(f'subject:"{k}"' for k in subj)
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


# ── Message-kind dispatcher ───────────────────────────────────────────────────
def classify_message_kind(from_addr: str, subject: str, body: str) -> str:
    """Return one of: application_reply, recruiter_outreach, job_alert, unknown."""
    addr = (from_addr or "").lower()
    domain = addr.split("@")[-1] if "@" in addr else ""

    # 1. Job alerts come from a small, curated set of senders/subjects
    if addr in JOB_ALERT_SENDERS:
        return "job_alert"
    if JOB_ALERT_SUBJECT_RE.search(subject):
        return "job_alert"

    # 2. Recruiter outreach — only when it doesn't smell like an automated reply
    is_noreply = any(tag in addr for tag in ("noreply", "no-reply", "donotreply", "do-not-reply"))
    if not is_noreply:
        if any(domain == d or domain.endswith("." + d) for d in RECRUITER_AGENCY_DOMAINS):
            return "recruiter_outreach"
        if RECRUITER_PHRASES_RE.search(body[:3000]) and "applying" not in body[:1000].lower():
            return "recruiter_outreach"

    # 3. Otherwise treat as a (possible) application reply — let classify_status decide
    return "application_reply"


# ── Recruiter / agency contact parser ─────────────────────────────────────────
def parse_contact(msg: dict) -> Optional[Contact]:
    subject = header(msg, "Subject")
    from_raw = header(msg, "From")
    date_raw = header(msg, "Date")
    from_name, from_addr = parseaddr(from_raw)
    if not from_addr:
        return None
    try:
        received = parsedate_to_datetime(date_raw).astimezone(timezone.utc).isoformat()
    except Exception:
        received = datetime.now(timezone.utc).isoformat()

    body = _extract_body(msg.get("payload", {}))
    domain = from_addr.split("@")[-1].lower()

    if any(domain == d or domain.endswith("." + d) for d in RECRUITER_AGENCY_DOMAINS):
        kind = "agency"
        company = domain.split(".")[0].title()
    else:
        kind = "recruiter"
        # Try "Recruiter at Company" / "Hiring Manager at Company" in body or signature
        m = re.search(r"(?:recruiter|talent\s+\w+|hiring\s+\w+)\s+at\s+"
                      r"([A-Z][\w&.'’\- ]{1,40})", body[:3000], re.I)
        company = m.group(1).strip(" .,-—") if m else (from_name.split(",")[-1].strip() or "")
        if not company:
            company = domain.split(".")[0].title()

    return Contact(
        email=from_addr.lower(),
        name=from_name.strip().strip('"'),
        company=company,
        kind=kind,
        first_seen=received,
        last_seen=received,
        message_count=1,
        subjects=[subject][:1],
        gmail_thread_ids=[msg["threadId"]],
    )


# ── Job alert parser ──────────────────────────────────────────────────────────
def parse_alerts(msg: dict) -> list[JobAlert]:
    from_raw = header(msg, "From")
    date_raw = header(msg, "Date")
    _, from_addr = parseaddr(from_raw)
    try:
        received = parsedate_to_datetime(date_raw).astimezone(timezone.utc).isoformat()
    except Exception:
        received = datetime.now(timezone.utc).isoformat()
    domain = (from_addr or "").split("@")[-1].lower()
    source = (
        "linkedin" if "linkedin" in domain else
        "indeed" if "indeed" in domain else
        "glassdoor" if "glassdoor" in domain else
        "ziprecruiter" if "ziprecruiter" in domain else
        "handshake" if "handshake" in domain else
        "dice" if "dice" in domain else
        "monster" if "monster" in domain else
        domain.split(".")[0] or "unknown"
    )

    body = _extract_body(msg.get("payload", {}))
    out: list[JobAlert] = []
    seen_keys: set[str] = set()
    DENY_COMPANY = {
        "easy apply", "promoted", "actively recruiting", "remote", "hybrid",
        "onsite", "view job", "see more", "apply now", "viewed", "applied",
        "linkedin", "indeed", "glassdoor", "ziprecruiter", "monster", "dice",
    }
    for m in JOB_LISTING_RE.finditer(body):
        title = m.group("title").strip(" .,-—:|")
        company = m.group("company").strip(" .,-—:|")
        if any(w in title.lower() for w in ("unsubscribe", "view in browser", "click here",
                                             "view on", "visit our", "see all jobs")):
            continue
        if len(title) < 4 or len(company) < 2 or company.lower() in DENY_COMPANY:
            continue
        # title must contain at least one alpha word of 4+ chars (rejects bare location lines)
        if not re.search(r"[A-Za-z]{4,}", title):
            continue
        k = hashlib.sha1(f"{source}|{company.lower()}|{title.lower()}".encode()).hexdigest()[:12]
        if k in seen_keys:
            continue
        seen_keys.add(k)
        # url near the listing
        u = re.search(r"https?://[^\s<>\"'\)]+", body[m.start():m.start() + 600])
        out.append(JobAlert(
            id=k,
            source=source,
            company=company,
            role=title,
            url=(u.group(0)[:300] if u else ""),
            first_seen=received,
            last_seen=received,
            seen_count=1,
            gmail_message_ids=[msg["id"]],
        ))
    return out


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


def load_contacts() -> dict[str, Contact]:
    if not CONTACTS_PATH.exists():
        return {}
    data = json.loads(CONTACTS_PATH.read_text())
    return {k: Contact(**v) for k, v in data.get("contacts", {}).items()}


def save_contacts(contacts: dict[str, Contact]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contacts": {k: asdict(v) for k, v in contacts.items()},
    }
    CONTACTS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))


def load_alerts() -> dict[str, JobAlert]:
    if not ALERTS_PATH.exists():
        return {}
    data = json.loads(ALERTS_PATH.read_text())
    return {k: JobAlert(**v) for k, v in data.get("alerts", {}).items()}


def save_alerts(alerts: dict[str, JobAlert]) -> None:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "alerts": {k: asdict(v) for k, v in alerts.items()},
    }
    ALERTS_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True))


def merge_contact(contacts: dict[str, Contact], c: Contact) -> bool:
    """Returns is_new."""
    k = c.email
    if k not in contacts:
        contacts[k] = c
        return True
    existing = contacts[k]
    existing.message_count += 1
    if c.last_seen > (existing.last_seen or ""):
        existing.last_seen = c.last_seen
    if not existing.first_seen or c.first_seen < existing.first_seen:
        existing.first_seen = c.first_seen
    if c.subjects and c.subjects[0] not in existing.subjects:
        existing.subjects.insert(0, c.subjects[0])
        existing.subjects = existing.subjects[:10]
    if c.gmail_thread_ids and c.gmail_thread_ids[0] not in existing.gmail_thread_ids:
        existing.gmail_thread_ids.append(c.gmail_thread_ids[0])
    if not existing.name and c.name:
        existing.name = c.name
    return False


def merge_alert(alerts: dict[str, JobAlert], a: JobAlert) -> bool:
    """Returns is_new."""
    if a.id not in alerts:
        alerts[a.id] = a
        return True
    existing = alerts[a.id]
    existing.seen_count += 1
    if a.last_seen > (existing.last_seen or ""):
        existing.last_seen = a.last_seen
    if a.gmail_message_ids and a.gmail_message_ids[0] not in existing.gmail_message_ids:
        existing.gmail_message_ids.append(a.gmail_message_ids[0])
    return False


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
    contacts = load_contacts()
    alerts = load_alerts()
    counts: Counter = Counter()
    notable_events: list[ParsedEmail] = []

    for mid in msg_ids:
        msg = fetch_message(service, mid)
        subject = header(msg, "Subject")
        from_raw = header(msg, "From")
        _, from_addr = parseaddr(from_raw)
        body_for_kind = _extract_body(msg.get("payload", {}))[:3000]
        kind = classify_message_kind(from_addr, subject, body_for_kind)

        if kind == "application_reply":
            parsed = parse_email(msg)
            if not parsed:
                continue
            counts["app_parsed"] += 1
            is_new, is_change = merge(entries, parsed)
            if is_new:
                counts["app_new"] += 1
                notable_events.append(parsed)
            if is_change:
                counts["app_changed"] += 1
                notable_events.append(parsed)

        elif kind == "recruiter_outreach":
            c = parse_contact(msg)
            if c:
                counts["contact_msgs"] += 1
                if merge_contact(contacts, c):
                    counts["contact_new"] += 1

        elif kind == "job_alert":
            for a in parse_alerts(msg):
                counts["alert_seen"] += 1
                if merge_alert(alerts, a):
                    counts["alert_new"] += 1

    log.info(
        f"Scanned {len(msg_ids)} — "
        f"applications: {counts['app_new']} new, {counts['app_changed']} changed; "
        f"contacts: {counts['contact_new']} new ({counts['contact_msgs']} msgs); "
        f"job alerts: {counts['alert_new']} new ({counts['alert_seen']} seen)"
    )

    if args.dry_run:
        log.info("--dry-run: skipping all writes, Slack, and Sheets sync")
        for e in notable_events[:20]:
            log.info(f"  · [{e.status}] {e.company or '?'} — {e.role or '?'} "
                     f"({e.received[:10]})  {e.subject!r}")
        return

    save_tracker(entries)
    save_contacts(contacts)
    save_alerts(alerts)
    log.info(f"Wrote {TRACKER_PATH.name}, {CONTACTS_PATH.name}, {ALERTS_PATH.name}")

    if notable_events and not args.no_slack:
        lines = [f"*Gmail Job Tracker* — "
                 f"{counts['app_new']} new applications, "
                 f"{counts['app_changed']} status changes, "
                 f"{counts['contact_new']} new recruiters, "
                 f"{counts['alert_new']} new alerts"]
        for e in notable_events[:15]:
            lines.append(f"• [{e.status}] {e.company or '?'} — {e.role or '?'} "
                         f"_{e.received[:10]}_")
        post_to_slack("\n".join(lines))

    if notable_events and not args.no_sheets:
        sync_to_sheets(notable_events)


if __name__ == "__main__":
    main()
