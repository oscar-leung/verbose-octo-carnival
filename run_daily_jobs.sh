#!/bin/bash
# Job search automation — Oscar Leung
# Runs 5x/day at 9 AM, 12 PM, 3 PM, 6 PM, 9 PM.
# Daily caps: ~20 LinkedIn + ~40 Handshake + ~15 Indeed + ~25 Greenhouse
#             + ~10 Glassdoor + 100 employer follows + 20 people follows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"
LOG_DIR="$SCRIPT_DIR/runs/daily_logs"
DATE="$(date +%Y-%m-%d)"

mkdir -p "$LOG_DIR"

echo "===== Daily Job Search: $DATE =====" | tee -a "$LOG_DIR/$DATE.log"

run_script() {
    local name="$1"; shift
    echo "[$(date +%H:%M:%S)] Starting $name..." | tee -a "$LOG_DIR/$DATE.log"
    cd "$SCRIPT_DIR"
    if "$PYTHON" "$@" >> "$LOG_DIR/${DATE}_${name}.log" 2>&1; then
        echo "[$(date +%H:%M:%S)] $name done." | tee -a "$LOG_DIR/$DATE.log"
    else
        echo "[$(date +%H:%M:%S)] $name errored — check ${DATE}_${name}.log" | tee -a "$LOG_DIR/$DATE.log"
    fi
}

# ── LinkedIn Easy Apply (headless, ~4/session = ~20/day) ──────────
run_script "linkedin"    scripts/035_linkedin_easy_apply_pa.py --max-applies 4

# ── Handshake Apply (~8/session = ~40/day) ────────────────────────
run_script "handshake"   scripts/036_handshake_apply_pa.py    --max-applies 8

# ── Indeed Easy Apply (~3/session = ~15/day) ──────────────────────
# NOTE: First run requires manual login — open a terminal and run 037 manually once.
# After that, ~/.chrome-indeed-profile caches the session and this runs unattended.
run_script "indeed"      scripts/037_indeed_apply.py          --pages 3

# ── Greenhouse via Google/Bing (~5/session = ~25/day) ─────────────
run_script "greenhouse"  scripts/038_greenhouse_apply.py      --google-pages 4 --max-applies 5

# ── Handshake Follow Employers (~20/session = ~100/day) ───────────
run_script "hs_follow"   scripts/039_handshake_follow_employers.py --max-follows 20 --pages 5

# ── Handshake People + Jobs (~4 applies/session = ~20/day) ────────
run_script "hs_people"   scripts/040_handshake_people_jobs.py --max-follows 10 --max-applies 4 --people-pages 3 --job-pages 2

# ── Glassdoor Easy Apply (~2/session = ~10/day) ───────────────────
run_script "glassdoor"   scripts/041_glassdoor_apply.py       --max-applies 2 --pages 2

echo "===== Done: $DATE =====" | tee -a "$LOG_DIR/$DATE.log"
