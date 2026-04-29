#!/bin/bash
# Handshake Apply — wrapper for PythonAnywhere scheduled task.
#
# In PA → Tasks tab → schedule:
#   bash /home/holymushy/verbose-octo-carnival/pythonanywhere/run_handshake_pa.sh
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

export CHROME_BIN="${CHROME_BIN:-/usr/bin/chromium}"
export PATH="/usr/bin:$PATH"

COOKIE="$PROJECT_DIR/handshake_cookies.json"
if [ ! -f "$COOKIE" ]; then
    echo "[$(date)] FATAL: $COOKIE not found." | tee -a "$LOG_DIR/${DATE}_handshake_pa.log"
    echo "         Run scripts/export_handshake_cookies.py locally, then scp the file to PA." \
         | tee -a "$LOG_DIR/${DATE}_handshake_pa.log"
    exit 1
fi

echo "===== Handshake PA run: $DATE $TS =====" | tee -a "$LOG_DIR/${DATE}_handshake_pa.log"

# --max-applies 8 per session × 5 daily runs ≈ 40 apps/day, matching local setup.
"$VENV_PY" scripts/036_handshake_apply_pa.py \
    --cookie-file "$COOKIE" \
    --max-applies 8 \
    >> "$LOG_DIR/${DATE}_handshake_pa.log" 2>&1

echo "[$(date)] Handshake PA done." | tee -a "$LOG_DIR/${DATE}_handshake_pa.log"
