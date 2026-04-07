"""
library/gsheets.py — Shared Google Sheets sync for all job application scripts.

Setup (one-time):
  1. Go to console.cloud.google.com → New project → Enable "Google Sheets API"
  2. IAM & Admin → Service Accounts → Create → Download JSON key
  3. Save the JSON key path in .env:  GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/key.json
  4. Create a Google Sheet, share it with the service account email (Editor)
  5. Copy the sheet ID from the URL and add to .env: GOOGLE_SHEET_ID=<id>

Install: pip install gspread google-auth

All scripts call: sync_jobs(all_jobs)  at the end of a run.
"""

import os
import logging
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

# ── Column order (matches Looker Studio dashboard schema) ─────────────────────
COLUMNS = [
    "date_applied",       # YYYY-MM-DD
    "platform",           # LinkedIn | Handshake | Indeed
    "job_id",
    "title",
    "company",
    "location",
    "remote_type",        # remote | onsite | hybrid
    "url",
    "employment_type",    # full-time | internship | part-time
    "salary_min",
    "salary_max",
    "salary_unit",        # yr | hr | mo
    "skills_mentioned",
    "apply_type",         # easy_apply | external | unknown
    "status",             # applied | skipped_* | error | scraped_only
    "days_since_posted",
    "notes",
]

_sheet = None   # cached worksheet

log = logging.getLogger(__name__)


def _get_sheet():
    """Return (and cache) the 'Applications' worksheet."""
    global _sheet
    if _sheet is not None:
        return _sheet

    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        raise ImportError("Run: pip install gspread google-auth")

    key_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not key_path or not sheet_id:
        raise EnvironmentError(
            "Set GOOGLE_SERVICE_ACCOUNT_JSON and GOOGLE_SHEET_ID in .env"
        )

    creds = Credentials.from_service_account_file(
        key_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(sheet_id)

    # Get or create the Applications tab
    try:
        ws = spreadsheet.worksheet("Applications")
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet("Applications", rows=10000, cols=len(COLUMNS))
        ws.append_row(COLUMNS)   # write header
        log.info("Created 'Applications' worksheet with headers.")

    _sheet = ws
    return ws


def _existing_ids(ws) -> set[str]:
    """Return set of 'platform|job_id' already in the sheet (dedup guard)."""
    try:
        records = ws.get_all_records()
        return {f"{r.get('platform','')}|{r.get('job_id','')}" for r in records if r.get("job_id")}
    except Exception:
        return set()


def _job_to_row(job: dict, platform: str) -> list:
    """Map a job dict (any script format) to the unified COLUMNS row."""
    # Normalise location field (scripts use different key names)
    location = (
        job.get("location_raw") or
        job.get("location") or
        job.get("city") or ""
    )
    return [
        job.get("timestamp", datetime.now().isoformat())[:10],   # date only
        platform,
        str(job.get("job_id", "")),
        job.get("title", ""),
        job.get("company", ""),
        location,
        job.get("remote_type", ""),
        job.get("url", ""),
        job.get("employment_type", ""),
        job.get("salary_min", ""),
        job.get("salary_max", ""),
        job.get("salary_unit", ""),
        job.get("skills_mentioned", ""),
        job.get("apply_type", ""),
        job.get("status", ""),
        job.get("days_since_posted", ""),
        job.get("notes", ""),
    ]


def sync_jobs(jobs: list[dict], platform: str, applied_only: bool = False):
    """
    Append new jobs to the Google Sheet.

    Args:
        jobs:         List of job dicts from any application script.
        platform:     "LinkedIn" | "Handshake" | "Indeed"
        applied_only: If True, only sync jobs with status="applied".
    """
    if not jobs:
        return
    try:
        ws = _get_sheet()
        existing = _existing_ids(ws)

        rows = []
        for job in jobs:
            if applied_only and job.get("status") != "applied":
                continue
            uid = f"{platform}|{job.get('job_id', '')}"
            if uid in existing:
                continue   # already synced
            rows.append(_job_to_row(job, platform))

        if rows:
            ws.append_rows(rows, value_input_option="USER_ENTERED")
            log.info(f"[gsheets] Synced {len(rows)} new rows to Google Sheets ({platform})")
        else:
            log.info("[gsheets] No new rows to sync.")
    except Exception as e:
        log.warning(f"[gsheets] Sync failed (non-fatal): {e}")
