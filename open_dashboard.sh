#!/bin/bash
# Job Search Live Dashboard
# Opens iTerm2 with 4 panes showing live script output and logs.
#
# Usage:
#   bash open_dashboard.sh          # view-only (tails latest logs)
#   bash open_dashboard.sh --run    # also kicks off a fresh 040 Handshake apply run

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve latest log files
DAILY_LOG="$SCRIPT_DIR/runs/daily_logs/$(date +%Y-%m-%d).log"
LI_LOG=$(ls -t "$SCRIPT_DIR/runs/linkedin_easy_apply_pa_"*/run.log 2>/dev/null | head -1)
HS_LOG=$(ls -t "$SCRIPT_DIR/runs/handshake_apply_pa_"*/run.log 2>/dev/null | head -1)
P40_LOG=$(ls -t "$SCRIPT_DIR/runs/handshake_people_"*/run.log 2>/dev/null | head -1)

if [[ "$1" == "--run" ]]; then
  CMD4="cd '$SCRIPT_DIR' && source venv/bin/activate && python 040_handshake_people_jobs.py --skip-people --max-applies 20"
else
  CMD4="echo '=== Latest 040 Run ===' && tail -f '$P40_LOG'"
fi

osascript - "$DAILY_LOG" "$LI_LOG" "$HS_LOG" "$CMD4" <<'APPLESCRIPT'
on run argv
  set dailyLog to item 1 of argv
  set liLog    to item 2 of argv
  set hsLog    to item 3 of argv
  set cmd4     to item 4 of argv

  tell application "iTerm2"
    activate
    set w to (create window with default profile)

    -- Top-left: Daily automation log
    tell current session of w
      set name to "Daily Log"
      write text "clear; echo '== Daily Automation Log =='; tail -f " & quoted form of dailyLog & " 2>/dev/null || echo 'No log yet today.'"
    end tell

    -- Top-right: LinkedIn
    tell current session of w
      set liPane to (split vertically with default profile)
    end tell
    tell liPane
      set name to "LinkedIn"
      write text "clear; echo '== LinkedIn Applies =='; tail -f " & quoted form of liLog & " 2>/dev/null || echo 'No LinkedIn log found.'"
    end tell

    -- Bottom-left: Handshake apply (036)
    tell current session of w
      set hsPane to (split horizontally with default profile)
    end tell
    tell hsPane
      set name to "Handshake Apply"
      write text "clear; echo '== Handshake Apply (036) =='; tail -f " & quoted form of hsLog & " 2>/dev/null || echo 'No Handshake log found.'"
    end tell

    -- Bottom-right: 040 people+jobs
    tell liPane
      set p40Pane to (split horizontally with default profile)
    end tell
    tell p40Pane
      set name to "Handshake People+Jobs"
      write text "clear; echo '== Handshake People+Jobs (040) =='; " & cmd4
    end tell

  end tell
end run
APPLESCRIPT

echo "Dashboard opened."
