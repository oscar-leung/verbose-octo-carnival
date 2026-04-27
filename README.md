# verbose-octo-carnival — Job Application Automation Suite

A personal automation toolkit built with Python + Selenium that applies to jobs across LinkedIn, Handshake, Indeed, and Greenhouse — scrapes job data, logs every result, and syncs everything to a Google Sheets dashboard. **Scheduled to run automatically 5× per day** via macOS launchd.

**Portfolio:** [oscar-leung.netlify.app](https://oscar-leung.netlify.app)
**LinkedIn:** [linkedin.com/in/oscar-leung](https://www.linkedin.com/in/oscar-leung/)
**PythonAnywhere:** [pythonanywhere.com/user/holymushy](https://www.pythonanywhere.com/user/holymushy/)

---

## What it does

1. **Discovers jobs** across 4 platforms (LinkedIn, Handshake, Indeed, Greenhouse via Google site: search)
2. **Filters titles** automatically — skips Senior/Lead/Manager/Director/Sales/Founding roles
3. **Applies via Easy Apply** where available; logs all others as skipped with reason
4. **Logs every job** to CSV + JSON in a timestamped `runs/` folder
5. **Syncs to Google Sheets** for a centralized dashboard (Huntr/Simplify-style)
6. **Runs headlessly on PythonAnywhere** (LinkedIn + email scraper scheduled daily)
7. **Follows 276+ employers** and active recruiters on Handshake for networking
8. **Extracts emails** from LinkedIn and Handshake posts for direct outreach

---

## Daily Automation (`run_daily_jobs.sh`)

The shell script `run_daily_jobs.sh` is scheduled via macOS launchd to run **5 times per day** at:
**9 AM · 12 PM · 3 PM · 6 PM · 9 PM**

Each session applies to a small cap of jobs to stay under platform radar:

| Session | LinkedIn | Handshake | Daily Total |
|---------|----------|-----------|-------------|
| Per run | 4 apps   | 8 apps    | —           |
| **Daily** | **~20**  | **~40**   | **~60 apps/day** |

Logs are written to `runs/daily_logs/YYYY-MM-DD.log`.

---

## Scripts

### Active Job Hunt (035–045) — Core automation suite

| # | Script | Platform | Mode | What it does |
|---|--------|----------|------|--------------|
| 035 | `035_linkedin_easy_apply_pa.py` | LinkedIn | Headless | Headless Easy Apply — 4 apps/session, runs in launchd schedule |
| 036 | `036_handshake_apply_pa.py` | Handshake | Visible UC | Easy Apply via undetected_chromedriver to bypass Cloudflare |
| 037 | `037_indeed_apply.py` | Indeed | Local visible | Auto-applies to Indeed Easy Apply QA/SWE jobs |
| 038 | `038_greenhouse_apply.py` | Greenhouse | Local visible | Google `site:boards.greenhouse.io` search → applies on the ATS |
| 039 | `039_handshake_follow_employers.py` | Handshake | Visible UC | Follows 276+ tech/gov employers; updates student profile |
| 040 | `040_handshake_people_jobs.py` | Handshake | Visible UC | Follows active recruiters/engineers, extracts emails, auto-applies |
| 041 | `041_calcareers_monitor.py` | CalCareers | Headless HTTP | Monitors calcareers.ca.gov for new QA/SWE state-job postings |
| 042 | `042_unified_pipeline.py` | Orchestrator | — | Chains Handshake apply → CalCareers monitor → GMass contact build |
| 043 | `043_gmail_job_tracker.py` | Gmail | Headless API | Scans ATS/recruiter email, classifies status (applied / interview / offer / rejection), writes `job_tracker.json`, optional Slack + Sheets sync |
| 044 | `044_runs_dashboard.py` | Reporting | — | Walks `runs/` + `job_tracker.json` and renders a per-script health view as either a self-contained HTML page (`runs/dashboard.html`) or an ANSI summary in the terminal (`--terminal`) |
| 045 | `045_dashboard_server.py` | Web dashboard | Flask | Localhost web app (`http://127.0.0.1:5050`) — searchable application table, per-company timeline, "Scan Gmail now" button that runs 043 in a thread |

### Web Dashboard (045)

Live UI on top of `043_gmail_job_tracker.py` and `044_runs_dashboard.py`. The
server reads `job_tracker.json` for the application table and per-company
timelines, embeds 044's per-script health page at `/scripts`, and exposes a
**Scan Gmail now** button that runs the same code path as the 043 CLI in a
background thread.

```bash
pip install flask
python3 045_dashboard_server.py            # http://127.0.0.1:5050
python3 045_dashboard_server.py --port 8080
```

Routes:

| Path | What it does |
|------|--------------|
| `/` | Pipeline pills + searchable, filterable table of every tracked application |
| `/entry/<key>` | One company/role — full email status timeline + Gmail thread links |
| `/scripts` | Embedded 044 dashboard (per-script run health, daily timeline) |
| `/api/tracker` | Raw `job_tracker.json` as JSON |
| `/api/refresh` (POST) | Kicks Gmail rescan in a thread |
| `/api/refresh-status` | Live progress (`running`, `last_result`, `last_error`) |

Deliberately localhost-only by default — it reads/writes `gmail_token.json`
on disk and has no auth. To open it past localhost, put it behind an SSH
tunnel or a reverse proxy that handles login.

### Unified Pipeline (042)

`042_unified_pipeline.py` is a single runner that chains the three
discovery-and-outreach stages together, so a launchd/cron entry fires one
command instead of three:

```
┌────────────────────┐   ┌──────────────────────┐   ┌──────────────────────────┐
│ 036 Handshake      │ → │ 041 CalCareers       │ → │ build_gmass_master.py    │
│ Easy Apply         │   │ new-posting monitor  │   │ (+ optional sheet push)  │
└────────────────────┘   └──────────────────────┘   └──────────────────────────┘
```

Each stage runs as a subprocess — a failure in one does not abort the others.
Per-stage logs and a `summary.json` land under `runs/unified_<timestamp>/`.

```bash
# Full run (logs + summary under runs/unified_<ts>/)
python3 042_unified_pipeline.py

# Forward dry-run to every stage
python3 042_unified_pipeline.py --dry-run

# Skip one stage, or run only one
python3 042_unified_pipeline.py --skip handshake
python3 042_unified_pipeline.py --only gmass

# Also push new GMass contacts to the GMassContacts sheet tab
python3 042_unified_pipeline.py --gmass-push-sheet
```

For launchd/cron, use `run_unified_pipeline.sh` — reads `HANDSHAKE_MAX` and
`CALCAREERS_PAGES` from the environment and tees to `runs/daily_logs/`.

### Email & Outreach

| # | Script | Purpose |
|---|--------|---------|
| 029 | `029_linkedIn_emails_script.py` | Scrapes recruiter contact emails from LinkedIn posts and feeds |
| `build_gmass_master.py` | — | Builds a deduplicated GMass email list; `--push-sheet` appends new contacts to the `GMassContacts` sheet tab so GMass sequences pick them up on their next cycle |

### Earlier Versions & Prototypes

| # | Script | Purpose |
|---|--------|---------|
| 025 | `025_easy_apply.py` | Original LinkedIn Easy Apply loop (pre-PythonAnywhere) |
| 033 | `033_handshake_applications.py` | Earlier Handshake apply script |
| 034 | `034_handshake_job_scraper.py` | Handshake job listing scraper |
| 028 | `028_linkedIn_emails_script.py` | Original LinkedIn email extractor (v1, superseded) |

### Outlier AI Contractor Tasks (Oct 2025 – Feb 2026)

Scripts 010–023 and 032 automate evaluation tasks from Outlier.ai contracting work:
text-to-video, ASR transcription accuracy, perception labeling, ELO ranking, and more.

### Other Automation

| # | Script | Purpose |
|---|--------|---------|
| 001 | `001-installing-workday-paystubs.py` | Workday HR portal paystub downloader |
| 002/003 | LinkedIn frameworks | LinkedIn automation prototypes (Nov 2023) |
| 008 | `008_stake_script.py` | Stake.us daily bonus collection |
| 009 | `009_samplicio.py` | Samplicio.us survey automation |
| 024 | `024_nmls_script.py` | NMLS mortgage licensing registry lookup |
| 026/027 | PrizeRebel scripts | Survey reward automation |
| 031 | `031_linkedin_analytics.py` | LinkedIn profile analytics scraper |

### Shared Library (`library/`)

| File | Purpose |
|------|---------|
| `library/gsheets.py` | Google Sheets sync — deduplicates by `platform|job_id`, appends new rows |

---

## Job Search Filter

Current LinkedIn/Handshake title filter (targets mid-level individual contributor roles):

```
((software engineer OR qa OR AI OR Salesforce OR web)
  AND NOT "Founding" AND NOT "sr" AND NOT "Sales" AND NOT "Senior"
  AND NOT "Product" AND NOT "Robotics" AND NOT "Campus"
  AND NOT "Customer" AND NOT "Manager" AND NOT "Digital"
  AND NOT "filmware" AND NOT "lead" AND NOT "field")
```

---

## Setup

### Prerequisites

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
LINKIN_USERNAME=your_linkedin_email@gmail.com
LINKIN_PASSWORD=your_linkedin_password
handshake_email=your_handshake_email@gmail.com
handshake_password=your_handshake_password
PHONE_NUMBER=+14155551234
RESUME_PDF_PATH=/absolute/path/to/Oscar_Leung_Resume.pdf
GOOGLE_SERVICE_ACCOUNT_JSON=/absolute/path/to/service_account.json
GOOGLE_SHEET_ID=your_google_sheet_id
# Optional — separate sheet for the GMass sequence (falls back to GOOGLE_SHEET_ID)
GMASS_SHEET_ID=your_gmass_sheet_id
```

### Run a script

```bash
# LinkedIn Easy Apply (local)
python3 025_easy_apply.py

# Handshake applications (local)
python3 033_handshake_applications.py

# Greenhouse via Google site: search
python3 038_greenhouse_apply.py --dry-run           # preview, no submissions
python3 038_greenhouse_apply.py --google-pages 10   # live run, 10 pages (~100 jobs)

# LinkedIn headless (PA-compatible)
python3 035_linkedin_easy_apply_pa.py --dry-run
```

---

## Output & Runs

Every script writes to a timestamped folder under `runs/`:

```
runs/
  greenhouse_apply_2026-04-07_18-27-51/
    run.log       ← full execution log
    jobs.json     ← all jobs with status, title, company, location, salary, skills
    jobs.csv      ← same data as spreadsheet
    job_urls.txt  ← raw URLs collected (Greenhouse only)
```

---

## Google Sheets Dashboard

All scripts sync to a shared Google Sheet via `library/gsheets.py`.

**Schema:**

| Column | Description |
|--------|-------------|
| date_applied | ISO timestamp |
| platform | LinkedIn / Handshake / Indeed / Greenhouse |
| job_id | Platform-specific ID (dedup key) |
| title | Job title |
| company | Company name |
| location | City/State or Remote |
| remote_type | remote / hybrid / onsite |
| url | Direct job URL |
| employment_type | full-time / contract / internship |
| salary_min / salary_max | Parsed salary range |
| salary_unit | /yr or /hr |
| skills_mentioned | Comma-separated tech skills found in description |
| apply_type | easy_apply / full_form / external |
| status | applied / skipped / error / dry_run |
| days_since_posted | Age of posting in days |
| notes | Skip reason or error message |

**Dashboard:** Connect with [Looker Studio](https://lookerstudio.google.com) → New Report → Google Sheets data source.

---

## PythonAnywhere (Automated Scheduled Tasks)

> See [`PythonAnywhere/setup_pythonanywhere.sh`](PythonAnywhere/setup_pythonanywhere.sh) for one-command setup.

**Recommended scripts for PA (headless-compatible):**

| Script | Schedule | What it does |
|--------|----------|-------------|
| `035_linkedin_easy_apply_pa.py` | Daily 08:00 | Applies to LinkedIn Easy Apply jobs |
| `029_linkedIn_emails_script.py` | Daily 09:00 | Scrapes recruiter emails from LinkedIn |

**Setup steps:**

```bash
# 1. SSH into PythonAnywhere Bash console
# 2. Clone the repo
git clone https://github.com/oscar-leung/verbose-octo-carnival.git
cd verbose-octo-carnival

# 3. Run setup
bash PythonAnywhere/setup_pythonanywhere.sh

# 4. Fill in .env with credentials
nano .env

# 5. Add scheduled tasks in PA Dashboard → Tasks
#    Task 1: cd ~/verbose-octo-carnival && python3 035_linkedin_easy_apply_pa.py
#    Task 2: cd ~/verbose-octo-carnival && python3 029_linkedIn_emails_script.py
```

**Note:** Handshake (036) is blocked by Cloudflare in headless mode — run locally instead. Indeed (037) requires manual Google OAuth — run locally.

---

## Run Results (April 7, 2026)

| Platform | Jobs Found | Applied | Skipped | Notes |
|----------|-----------|---------|---------|-------|
| LinkedIn (headless) | 1,029 | 0 | 1,028 | Dry-run mode; 1,000+ jobs indexed |
| Handshake | 79 | 28 | 51 | 26 already applied, 24 external |
| Greenhouse | 20 | 7 (dry) | 13 | `skipped_no_button` = jobs needing login |
| Indeed | 0 | 0 | 0 | Indeed blocked job card selectors |

---

## Project History

| Date | Milestone |
|------|-----------|
| Nov 2023 | Started with Workday paystub scraper (001) |
| Nov 2023 | First LinkedIn Easy Apply bot — 400+ applications |
| Dec 2023 | Built more robust framework with IPython (003) |
| Nov 2025 | Outlier task automation — 4hrs of work in 30 min |
| Feb 2026 | Handshake ELO task scripts (032) |
| Apr 2026 | Full job application suite: LinkedIn + Handshake + Indeed + Greenhouse |
| Apr 2026 | Google Sheets dashboard + PythonAnywhere deployment |
| Apr 2026 | macOS launchd automation — 5×/day schedule, ~60 apps/day |
| Apr 2026 | Followed 276+ tech/gov employers on Handshake (039) |
| Apr 2026 | People follow + email extraction + recruiter outreach pipeline (040) |

---

## Tech Stack

- **Python 3.12** + **Selenium 4** — browser automation
- **ChromeDriver** — anti-detection (`--disable-blink-features=AutomationControlled`)
- **gspread** + **google-auth** — Google Sheets sync
- **python-dotenv** — credential management
- **PythonAnywhere** — headless scheduled execution
- **Looker Studio** — free dashboard frontend

---

*Automating the job hunt so I can focus on interview prep.*
