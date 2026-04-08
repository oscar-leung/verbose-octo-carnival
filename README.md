# verbose-octo-carnival — Job Application Automation Suite

A personal automation toolkit built with Python + Selenium that applies to jobs across LinkedIn, Handshake, Indeed, and Greenhouse — scrapes job data, logs every result, and syncs everything to a Google Sheets dashboard.

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

---

## Scripts

### Active Job Application Scripts

| # | Script | Platform | Mode | Notes |
|---|--------|----------|------|-------|
| 025 | `025_easy_apply.py` | LinkedIn | Local (visible) | Main LinkedIn Easy Apply loop |
| 029 | `029_linkedIn_emails_script.py` | LinkedIn | Local/PA headless | Scrapes recruiter emails from job posts |
| 033 | `033_handshake_applications.py` | Handshake | Local (visible) | Applies to all Easy Apply Handshake jobs |
| 034 | `034_handshake_job_scraper.py` | Handshake | Local (visible) | Scrapes job listings without applying |
| 035 | `035_linkedin_easy_apply_pa.py` | LinkedIn | **Headless / PA** | Best for PythonAnywhere scheduled tasks |
| 036 | `036_handshake_apply_pa.py` | Handshake | Headless / PA | Cookie-based session to bypass Cloudflare |
| 037 | `037_indeed_apply.py` | Indeed | Local (visible) | Manual Google OAuth login, then auto-apply |
| 038 | `038_greenhouse_apply.py` | Greenhouse | Local (visible) | Google `site:boards.greenhouse.io` search → apply |

### Supporting Scripts

| # | Script | Purpose |
|---|--------|---------|
| 031 | `031_linkedin_analytics.py` | LinkedIn profile analytics scraper |
| 032 | `032_handshake_script_*.py` | Handshake ELO/omni task automation |

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
