#!/usr/bin/env python3
"""
build_gmass_master.py
Scans all jobs.csv run files, extracts recruiter emails from description_full,
and writes a merged gmass_contacts_master.csv ready to upload to GMass.

Optional: --push-sheet writes the same rows to a dedicated Google Sheet tab
("GMassContacts" by default) so a GMass sequence configured against that sheet
picks up new contacts on its next cycle — turning the CSV into a live feed.
"""
import argparse
import csv
import glob
import os
import re
import sys

EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.IGNORECASE)

# Domains to ignore — job boards, ATSes, CDNs, generic noise
BLOCKLIST = {
    "linkedin.com", "indeed.com", "greenhouse.io", "example.com",
    "sentry.io", "w3.org", "schema.org", "lever.co", "workday.com",
    "myworkdayjobs.com", "icims.com", "taleo.net", "bamboohr.com",
    "smartrecruiters.com", "applytojob.com", "ziprecruiter.com",
    "glassdoor.com", "monster.com", "handshake.com", "joinhandshake.com",
    "google.com", "microsoft.com", "apple.com",
}

# Local-part prefixes that are clearly not humans
NOISE_LOCAL = {
    "noreply", "no-reply", "donotreply", "support", "info", "hello",
    "contact", "admin", "webmaster", "postmaster", "accommodation",
    "immigration", "legal", "compliance", "security", "privacy",
    "feedback", "notifications", "newsletter", "unsubscribe",
    "bounces", "mailer-daemon",
}

FIELDNAMES = ["Email", "First Name", "Last Name", "Company", "Title",
              "Job URL", "Location", "Skills"]


def extract_email(text: str) -> str:
    for m in EMAIL_RE.finditer(text or ""):
        addr = m.group(0).lower()
        local, domain = addr.rsplit("@", 1)
        if domain in BLOCKLIST:
            continue
        if local in NOISE_LOCAL:
            continue
        return addr
    return ""


def collect_contacts(runs_dir: str) -> list[dict]:
    contacts: list[dict] = []
    seen: set[str] = set()
    for csv_path in sorted(glob.glob(os.path.join(runs_dir, "**/jobs.csv"), recursive=True)):
        try:
            with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
                for row in csv.DictReader(f):
                    desc = row.get("description_full", "") or row.get("raw_row", "")
                    email = extract_email(desc)
                    if email and email not in seen:
                        seen.add(email)
                        contacts.append({
                            "Email":      email,
                            "First Name": "",
                            "Last Name":  "",
                            "Company":    row.get("company", ""),
                            "Title":      row.get("title", ""),
                            "Job URL":    row.get("url", ""),
                            "Location":   row.get("location", "") or row.get("location_raw", ""),
                            "Skills":     row.get("skills_mentioned", ""),
                        })
        except Exception as e:
            print(f"[warn] skip {csv_path}: {e}", file=sys.stderr)
    return contacts


def write_csv(contacts: list[dict], out_path: str):
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        w.writeheader()
        w.writerows(contacts)


def push_to_sheet(contacts: list[dict], tab_name: str = "GMassContacts") -> int:
    """Write contacts to a dedicated worksheet tab so GMass can read from it."""
    import gspread
    from google.oauth2.service_account import Credentials

    key_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    sheet_id = os.getenv("GMASS_SHEET_ID") or os.getenv("GOOGLE_SHEET_ID")
    if not key_path or not sheet_id:
        raise EnvironmentError("Set GOOGLE_SERVICE_ACCOUNT_JSON and GMASS_SHEET_ID (or GOOGLE_SHEET_ID)")

    creds = Credentials.from_service_account_file(
        key_path, scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    gc = gspread.authorize(creds)
    spreadsheet = gc.open_by_key(sheet_id)
    try:
        ws = spreadsheet.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(tab_name, rows=5000, cols=len(FIELDNAMES))
        ws.append_row(FIELDNAMES)

    existing_emails = {r.get("Email", "").lower() for r in ws.get_all_records()}
    new_rows = [
        [c[k] for k in FIELDNAMES]
        for c in contacts
        if c["Email"].lower() not in existing_emails
    ]
    if new_rows:
        ws.append_rows(new_rows, value_input_option="USER_ENTERED")
    return len(new_rows)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--push-sheet", action="store_true",
                   help="Also append new contacts to the GMassContacts Google Sheet tab")
    p.add_argument("--runs-dir", default=None, help="Runs directory to scan (default: ./runs)")
    p.add_argument("--out", default=None, help="Output CSV path")
    a = p.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    runs_dir   = a.runs_dir or os.path.join(script_dir, "runs")
    out_path   = a.out or os.path.join(script_dir, "gmass_contacts_master.csv")

    contacts = collect_contacts(runs_dir)
    write_csv(contacts, out_path)

    print(f"\nWrote {len(contacts)} unique recruiter contacts to: {out_path}\n")
    print(f"{'Email':<48} {'Company':<32} {'Title'}")
    print("-" * 110)
    for c in contacts[:50]:
        print(f"  {c['Email']:<46} {c['Company'][:30]:<32} {c['Title'][:45]}")
    if len(contacts) > 50:
        print(f"  … and {len(contacts) - 50} more")

    pushed = 0
    if a.push_sheet:
        try:
            pushed = push_to_sheet(contacts)
            print(f"\nPushed {pushed} new rows to GMassContacts sheet.")
        except Exception as e:
            print(f"[warn] sheet push failed (non-fatal): {e}", file=sys.stderr)

    # Summary line consumed by the unified pipeline
    print(f"GMASS_SUMMARY total={len(contacts)} pushed_to_sheet={pushed} csv={out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
