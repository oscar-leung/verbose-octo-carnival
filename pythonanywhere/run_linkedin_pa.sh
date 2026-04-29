#!/bin/bash
# LinkedIn Easy Apply — wrapper for PythonAnywhere scheduled task.
#
# In PA → Tasks tab → schedule:
#   bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_linkedin_pa.sh
#
# (Replace holymushy with your actual PA username if different.)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$PROJECT_DIR/venv-pa/bin/python"
LOG_DIR="$PROJECT_DIR/runs/daily_logs"
DATE="$(date +%Y-%m-%d)"
TS="$(date +%H-%M-%S)"

mkdir -p "$LOG_DIR"
cd "$PROJECT_DIR"

# Hint Selenium toward PA's system Chromium — only effective on Hacker+ tier.
export CHROME_BIN="${CHROME_BIN:-/usr/bin/chromium}"
export PATH="/usr/bin:$PATH"

COOKIE="$PROJECT_DIR/linkedin_cookies.json"
if [ ! -f "$COOKIE" ]; then
    echo "[$(date)] FATAL: $COOKIE not found." | tee -a "$LOG_DIR/${DATE}_linkedin_pa.log"
    echo "         Run scripts/export_linkedin_cookies.py locally, then scp the file to PA." \
         | tee -a "$LOG_DIR/${DATE}_linkedin_pa.log"
    exit 1
fi

echo "===== LinkedIn PA run: $DATE $TS =====" | tee -a "$LOG_DIR/${DATE}_linkedin_pa.log"

# --max-applies 4 is intentionally low — LinkedIn flags accounts that submit
# too quickly. With 5 daily runs this still totals ~20 apps/day.
"$VENV_PY" scripts/035_linkedin_easy_apply_pa.py \
    --cookie-file "$COOKIE" \
    --max-applies 4 \
    >> "$LOG_DIR/${DATE}_linkedin_pa.log" 2>&1

echo "[$(date)] LinkedIn PA done." | tee -a "$LOG_DIR/${DATE}_linkedin_pa.log"
