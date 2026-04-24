<div align="center">

<h1>🤖 Job Hunt Automation Suite</h1>

<p><strong>Python + Selenium platform that applies to 50+ jobs/day across LinkedIn, Handshake, Indeed & Greenhouse — 24/7, fully headless, zero manual effort.</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-43B02A?style=flat-square&logo=selenium&logoColor=white)](https://selenium.dev)
[![Google Sheets](https://img.shields.io/badge/Google_Sheets_API-Live_Dashboard-34A853?style=flat-square&logo=googlesheets&logoColor=white)](https://developers.google.com/sheets)
[![PythonAnywhere](https://img.shields.io/badge/Deployed-PythonAnywhere-1D9FD7?style=flat-square)](https://pythonanywhere.com)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

<br/>

**[Portfolio](https://oscar-leung.github.io) · [LinkedIn](https://linkedin.com/in/oscar-leung) · [YouTube](https://www.youtube.com/@oscarleung7579)**

</div>

---

## 🎯 What This Is

A **production-grade automation system** that runs 5× per day on a schedule and handles the entire job application pipeline end-to-end:

```
Discover jobs → Filter by title/location → Apply via Easy Apply → Log results → Sync to Google Sheets
```

This isn't a tutorial project — it handles **rate limiting, anti-detection, Cloudflare bypass, multi-platform form filling, deduplication across 1,000+ listings per run**, and maintains a live dashboard. Built entirely from scratch with no commercial tools.

---

## 📊 Live Stats

| Metric | Value |
|--------|-------|
| Platforms covered | LinkedIn · Handshake · Indeed · Greenhouse |
| Daily applications | ~60 (20 LinkedIn · 40 Handshake) |
| Jobs scraped per run | 1,000+ listings |
| Employers followed on Handshake | 276+ |
| Schedule | 5× daily: 9AM · 12PM · 3PM · 6PM · 9PM |
| Dashboard | Real-time Google Sheets via API |
| Deployment | PythonAnywhere (headless) + macOS launchd (local) |

---

## 🏗️ Architecture

```
verbose-octo-carnival/
├── scripts/
│   ├── 035_linkedin_easy_apply_pa.py     # LinkedIn headless Easy Apply
│   ├── 036_handshake_apply_pa.py         # Handshake (undetected-chromedriver)
│   ├── 037_indeed_apply.py               # Indeed Easy Apply
│   ├── 038_greenhouse_apply.py           # Greenhouse via Bing search fallback
│   ├── 039_handshake_follow_employers.py # Follow 276+ employers
│   └── 040_handshake_people_jobs.py      # People/networking jobs
├── library/
│   ├── gsheets.py                        # Google Sheets API sync
│   ├── uc_compat.py                      # undetected-chromedriver compatibility
│   └── utils.py                          # Shared helpers
├── run_daily_jobs.sh                     # Shell script triggered by launchd
└── runs/daily_logs/                      # Timestamped run logs
```

---

## ⚙️ Key Technical Features

### Anti-Detection
- **undetected-chromedriver** for Cloudflare Turnstile bypass (Handshake)
- Human-pacing delays between interactions (randomized 1.5–4s)
- User-agent rotation and headless fingerprint masking
- Daily apply caps per platform to stay under radar

### Smart Filtering
```python
SKIP_KEYWORDS = ["Senior", "Lead", "Manager", "Director", "Principal",
                 "Staff", "VP", "Head of", "Founding", "Sales", "Recruiter"]
```
Auto-skips roles above target seniority — only QA, SDET, SWE, and Automation titles proceed.

### Deduplication
URL fingerprinting across runs — jobs already applied to or skipped are never re-processed.

### Google Sheets Dashboard
Every application logs: `job_title · company · url · platform · status · date · location · salary`  
Live sync via `gspread` API — acts as a personal Huntr/Simplify replacement.

---

## 🚀 Active Scripts

| # | Script | Platform | Strategy | Daily Cap |
|---|--------|----------|----------|-----------|
| 035 | `linkedin_easy_apply_pa.py` | LinkedIn | Headless Easy Apply, Bay Area + Remote | 20 |
| 036 | `handshake_apply_pa.py` | Handshake | Visible UC, Cloudflare bypass | 40 |
| 037 | `indeed_apply.py` | Indeed | Easy Apply scraper | 15 |
| 038 | `greenhouse_apply.py` | Greenhouse | Bing `site:boards.greenhouse.io` fallback | 10 |
| 039 | `handshake_follow_employers.py` | Handshake | Follow 276+ tech/gov employers | — |
| 040 | `handshake_people_jobs.py` | Handshake | Networking-based job discovery | — |

---

## 🛠️ Setup

### Prerequisites
- Python 3.10+
- Chrome / Chromium
- A Google Cloud project with Sheets API enabled

### Install
```bash
git clone https://github.com/oscar-leung/verbose-octo-carnival.git
cd verbose-octo-carnival
pip install -r requirements.txt
```

### Configure
```bash
cp .env.example .env
# Fill in: LINKEDIN_EMAIL, LINKEDIN_PASSWORD, HANDSHAKE_EMAIL,
#          HANDSHAKE_PASSWORD, GOOGLE_SHEETS_CREDS_JSON, SHEET_ID
```

### Run a single script
```bash
python3 scripts/035_linkedin_easy_apply_pa.py --max-applies 8
python3 scripts/036_handshake_apply_pa.py --max-applies 15
```

### Schedule with launchd (macOS)
```bash
cp com.oscar.jobsearch.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.oscar.jobsearch.plist
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `selenium` | Browser automation |
| `undetected-chromedriver` | Cloudflare bypass |
| `gspread` | Google Sheets API |
| `python-dotenv` | Environment config |
| `requests` | HTTP utilities |
| `beautifulsoup4` | HTML parsing fallback |

---

## 📁 Logs & Output

Each run generates timestamped output in `runs/daily_logs/`:
```
YYYY-MM-DD.log           ← human-readable run log
runs/YYYY-MM-DD/
  ├── applied.csv         ← jobs successfully applied to
  ├── skipped.csv         ← jobs skipped with reason
  └── errors.log          ← exceptions + stack traces
```

---

## 🗺️ Roadmap

- [ ] Fix Indeed job card selector (currently finding 0 jobs)
- [ ] Fix Greenhouse Google CAPTCHA (Bing fallback in progress)
- [ ] Cookie-based LinkedIn auth for headless email scraper
- [ ] Deploy full suite to PythonAnywhere
- [ ] Slack/email notification on daily run completion
- [ ] Analytics dashboard from accumulated run data

---

## 👤 About

**Oscar Leung** — Software Engineer & QA Automation specialist, Bay Area CA

> Built this to solve my own job hunt at scale. It's the same automation mindset I bring to every engineering role: if you're doing something repetitive, automate it.

[![Portfolio](https://img.shields.io/badge/Portfolio-oscar--leung.github.io-38bdf8?style=flat-square)](https://oscar-leung.github.io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/oscar-leung)
[![YouTube](https://img.shields.io/badge/YouTube-Channel-FF0000?style=flat-square&logo=youtube)](https://www.youtube.com/@oscarleung7579)
