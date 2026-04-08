# PythonAnywhere Setup

**Account:** [pythonanywhere.com/user/holymushy](https://www.pythonanywhere.com/user/holymushy/)

PythonAnywhere runs the headless scripts on a daily schedule so applications go out automatically without needing your laptop to be on.

---

## Scheduled Tasks

| Task | Script | Schedule | What it does |
|------|--------|----------|-------------|
| 1 | `035_linkedin_easy_apply_pa.py` | Daily 08:00 | LinkedIn Easy Apply (headless Chrome) |
| 2 | `029_linkedIn_emails_script.py` | Daily 09:00 | Scrapes recruiter emails from job posts |

---

## One-Command Setup

Run this in a PythonAnywhere Bash console:

```bash
git clone https://github.com/oscar-leung/verbose-octo-carnival.git
cd verbose-octo-carnival
bash PythonAnywhere/setup_pythonanywhere.sh
```

Then fill in your credentials:
```bash
nano .env
```

Then add the two scheduled tasks in **Dashboard → Tasks**.

---

## Files

| File | Purpose |
|------|---------|
| `setup_pythonanywhere.sh` | One-command install + prints task commands |
| `headless_linkedin_login.py` | Standalone headless login test script |
| `scripts/` | Debug screenshots from headless runs |
| `images/` | Reference screenshots |

---

## Notes

- **Handshake (036)** is blocked by Cloudflare in headless mode — run `033_handshake_applications.py` locally instead.
- **Indeed (037)** requires manual Google OAuth — run locally.
- **Greenhouse (038)** uses visible Chrome for Google search to avoid CAPTCHA — run locally.
- Google Sheets sync requires `gspread` and `google-auth` installed: `pip3 install --user gspread google-auth`
