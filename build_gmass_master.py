#!/usr/bin/env python3
"""
build_gmass_master.py
Scans all jobs.csv run files, extracts recruiter emails from description_full,
and writes a merged gmass_contacts_master.csv ready to upload to GMass.
"""
import csv
import re
import glob
import os
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


contacts = []
seen: set[str] = set()
runs_dir = os.path.join(os.path.dirname(__file__), "runs")

for csv_path in sorted(glob.glob(os.path.join(runs_dir, "**/jobs.csv"), recursive=True)):
    try:
        with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                desc = row.get("description_full", "")
                email = extract_email(desc)
                if email and email not in seen:
                    seen.add(email)
                    contacts.append(
                        {
                            "Email": email,
                            "First Name": "",
                            "Last Name": "",
                            "Company": row.get("company", ""),
                            "Title": row.get("title", ""),
                            "Job URL": row.get("url", ""),
                            "Location": row.get("location", ""),
                            "Skills": row.get("skills_mentioned", ""),
                        }
                    )
    except Exception as e:
        print(f"[warn] skip {csv_path}: {e}", file=sys.stderr)

out_path = os.path.join(os.path.dirname(__file__), "gmass_contacts_master.csv")
fieldnames = ["Email", "First Name", "Last Name", "Company", "Title", "Job URL", "Location", "Skills"]

with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(contacts)

print(f"\nWrote {len(contacts)} unique recruiter contacts to: {out_path}\n")
print(f"{'Email':<48} {'Company':<32} {'Title'}")
print("-" * 110)
for c in contacts:
    print(f"  {c['Email']:<46} {c['Company'][:30]:<32} {c['Title'][:45]}")
