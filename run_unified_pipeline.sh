#!/bin/bash
# Unified pipeline: Handshake apply → CalCareers monitor → GMass contacts
# Thin launchd-friendly wrapper. Per-session caps stay small so cron-style
# runs don't get flagged. Full logs live under runs/unified_<timestamp>/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-$SCRIPT_DIR/venv/bin/python}"
LOG_DIR="$SCRIPT_DIR/runs/daily_logs"
DATE="$(date +%Y-%m-%d)"
TIME="$(date +%H:%M:%S)"

mkdir -p "$LOG_DIR"

echo "[$TIME] unified pipeline start ($DATE)" | tee -a "$LOG_DIR/$DATE.log"

cd "$SCRIPT_DIR"
if "$PYTHON" 042_unified_pipeline.py \
      --handshake-max "${HANDSHAKE_MAX:-8}" \
      --calcareers-pages "${CALCAREERS_PAGES:-3}" \
      --gmass-push-sheet \
      >> "$LOG_DIR/${DATE}_unified.log" 2>&1; then
    echo "[$(date +%H:%M:%S)] unified pipeline done." | tee -a "$LOG_DIR/$DATE.log"
else
    echo "[$(date +%H:%M:%S)] unified pipeline FAILED — see ${DATE}_unified.log" | tee -a "$LOG_DIR/$DATE.log"
    exit 1
fi
