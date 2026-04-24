#!/bin/bash
# Job search automation — Oscar Leung
# Runs 5x/day at 9 AM, 12 PM, 3 PM, 6 PM, 9 PM.
# Per-session caps are small so totals stay reasonable (~20 LinkedIn + ~40 Handshake/day).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/venv/bin/python"
LOG_DIR="$SCRIPT_DIR/runs/daily_logs"
DATE="$(date +%Y-%m-%d)"

mkdir -p "$LOG_DIR"

echo "===== Daily Job Search: $DATE =====" | tee -a "$LOG_DIR/$DATE.log"

TIME="$(date +%H:%M:%S)"

# ── LinkedIn Easy Apply (headless, ~4/session = ~20/day) ───────────
echo "[$TIME] Starting LinkedIn..." | tee -a "$LOG_DIR/$DATE.log"
cd "$SCRIPT_DIR"
"$PYTHON" scripts/035_linkedin_easy_apply_pa.py --max-applies 4 \
    >> "$LOG_DIR/${DATE}_linkedin.log" 2>&1 \
    && echo "[$(date +%H:%M:%S)] LinkedIn done." | tee -a "$LOG_DIR/$DATE.log" \
    || echo "[$(date +%H:%M:%S)] LinkedIn errored — check ${DATE}_linkedin.log" | tee -a "$LOG_DIR/$DATE.log"

# ── Handshake (visible browser, ~8/session = ~40/day) ─────────────
echo "[$(date +%H:%M:%S)] Starting Handshake..." | tee -a "$LOG_DIR/$DATE.log"
"$PYTHON" scripts/036_handshake_apply_pa.py --max-applies 8 \
    >> "$LOG_DIR/${DATE}_handshake.log" 2>&1 \
    && echo "[$(date +%H:%M:%S)] Handshake done." | tee -a "$LOG_DIR/$DATE.log" \
    || echo "[$(date +%H:%M:%S)] Handshake errored — check ${DATE}_handshake.log" | tee -a "$LOG_DIR/$DATE.log"

echo "===== Done: $DATE =====" | tee -a "$LOG_DIR/$DATE.log"
