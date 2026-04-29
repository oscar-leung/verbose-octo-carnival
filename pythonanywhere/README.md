# PythonAnywhere Deployment

Deploys `035_linkedin_easy_apply_pa.py` and `036_handshake_apply_pa.py` to PythonAnywhere as scheduled tasks.

## Read this first — free-tier reality check

Your earlier answer said "free tier, several times per day." Both halves of that conflict with PA's free-tier constraints:

| Constraint | Free tier | What you need |
|---|---|---|
| Number of scheduled tasks | 1 total | Hacker plan ($5/mo) for 2+ tasks (LinkedIn + Handshake) |
| Schedule frequency | Once per 24h, fixed time | Hacker plan for hourly/multi-daily |
| Outbound network | Allowlisted sites only — `linkedin.com` ✓, `joinhandshake.com` ✗ | Paid tier removes the allowlist entirely |
| Chromium / chromedriver | Not installed | Hacker+ ships system Chromium under `/usr/bin` |
| CPU seconds | 100/day | 2000+ on Hacker, more on higher tiers |

**Practical conclusion:** the LinkedIn script *might* limp along on free tier if PA later adds Chromium to free accounts (they don't right now). The Handshake script **cannot** run on free tier — `joinhandshake.com` isn't whitelisted, so the very first `driver.get("https://app.joinhandshake.com")` will fail with a connection refused.

If you don't want to upgrade to Hacker, the realistic alternatives are:
- A small DigitalOcean / Hetzner / Linode droplet (~$4/mo) with full network + apt access
- GitHub Actions on a private repo (free for personal accounts, headless Chromium pre-installed)
- Keep the local `launchd` setup you already have

For the rest of this guide I'll assume you've gone with the **Hacker plan**, since that's the cheapest path that actually makes the script work.

---

## ToS reminder

LinkedIn (User Agreement § 8.2) and Handshake (Terms of Use) both prohibit automated submissions. The realistic detection outcome is a permanent account ban, not a warning. The scripts already throttle aggressively (1.5–4s between actions, 60–120s breaks every 4 applies, daily caps), but no amount of human-pacing eliminates that risk. You've built the project knowing this — just flagging it again because deploying to a remote server *increases* your exposure: PA IP ranges are well-known to LinkedIn's anti-bot team.

---

## One-time setup

### 1. On your Mac, generate fresh cookies

```bash
cd ~/verbose-octo-carnival
python scripts/export_linkedin_cookies.py     # if you haven't created this yet, mirror export_handshake_cookies.py
python scripts/export_handshake_cookies.py
```

Both produce JSON files in the project root: `linkedin_cookies.json` and `handshake_cookies.json`. They're typically valid for ~30 days for LinkedIn, ~60–90 days for Handshake before the platforms invalidate them.

### 2. Push to PA

In a PA Bash console:

```bash
cd ~
git clone https://github.com/oscar-leung/verbose-octo-carnival.git
cd verbose-octo-carnival
```

Then from your Mac, push the secrets that aren't (and shouldn't be) in git:

```bash
scp .env                     holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/
scp linkedin_cookies.json    holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/
scp handshake_cookies.json   holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/
```

(scp from PA's free tier inbound is fine; only outbound is allowlisted.)

### 3. Run setup

In the PA Bash console:

```bash
cd ~/verbose-octo-carnival
bash pythonanywhere/setup.sh
```

This creates `venv-pa/`, installs the PA-specific subset of requirements (no `pyautogui`, no `undetected-chromedriver`), and sanity-checks that Chromium + chromedriver are present.

### 4. Smoke-test before scheduling

Always run a dry-run by hand once:

```bash
cd ~/verbose-octo-carnival
./venv-pa/bin/python scripts/035_linkedin_easy_apply_pa.py \
    --cookie-file linkedin_cookies.json --dry-run --max-applies 1
```

Watch the output. If the cookies are stale you'll see a redirect to the login page — go back to step 1, re-export, and re-upload.

### 5. Schedule the tasks

PA dashboard → **Tasks** tab → "Schedule a new task":

| Time (UTC) | Command |
|---|---|
| 16:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_linkedin_pa.sh` |
| 17:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_handshake_pa.sh` |
| 19:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_linkedin_pa.sh` |
| 20:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_handshake_pa.sh` |
| 22:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_linkedin_pa.sh` |
| 23:00 | `bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_handshake_pa.sh` |

(Pacific = UTC − 7 during DST, so 16:00 UTC ≈ 9 AM PT. PA's scheduler is UTC-only.)

**Don't run them simultaneously.** Both scripts spawn Chromium, and PA's per-task memory cap will OOM-kill you if two browsers are alive at once.

---

## Day-to-day operations

### Where to look when something breaks

```
runs/
├── daily_logs/2026-04-29_linkedin_pa.log    # wrapper-level stdout
├── daily_logs/2026-04-29_handshake_pa.log
├── linkedin_easy_apply_pa_2026-04-29_16-00-00/
│   ├── run.log                               # detailed per-job log
│   ├── jobs.json
│   ├── jobs.csv
│   ├── login_page.png                        # if login failed — open this first
│   └── login_success.png
└── handshake_apply_pa_2026-04-29_17-00-00/
    └── ...
```

### Refreshing cookies

When you start seeing `RuntimeError: Could not find LinkedIn email field` or every job is "skipped — no Easy Apply button," the cookies have expired:

1. Re-run the export script on your Mac
2. `scp` the new JSON to PA
3. Done — next scheduled run picks them up

Set a calendar reminder for the 25th of each month to do this proactively.

### Killing a stuck task

PA dashboard → Tasks → click "Stop" on the running task. The wrapper's `set -euo pipefail` will not leave orphaned Chrome processes, but if you suspect one survived: PA Bash console → `pkill -f chromium` is safe.

---

## What's intentionally not done

- **Not running the other six scripts on PA.** Indeed/Greenhouse/Glassdoor/etc. all rely on `undetected-chromedriver` + persistent Chrome profiles + non-headless mode for Cloudflare bypass. None of that works on PA. Keep those on the Mac via launchd.
- **Not syncing cookies automatically.** A cron that downloads cookies from somewhere would defeat the point of having them be secrets. The manual scp is intentional.
- **Not parallelizing runs.** Sequential by design (see memory note above).

---

## Files in this folder

| File | Purpose |
|---|---|
| `setup.sh` | One-time PA bootstrap: venv, pip install, sanity checks |
| `requirements_pa.txt` | PA-only deps (no pyautogui, no UC) |
| `run_linkedin_pa.sh` | Wrapper for LinkedIn scheduled task |
| `run_handshake_pa.sh` | Wrapper for Handshake scheduled task |
| `README.md` | This file |
