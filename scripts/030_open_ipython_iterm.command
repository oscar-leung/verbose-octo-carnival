#!/bin/bash

# EDIT THIS: set your project directory (use an absolute path)
PROJECT_DIR="$HOME/verbose-octo-carnival"

osascript <<EOF
tell application "iTerm"
  activate
  set newWindow to (create window with default profile)
  tell current session of newWindow
    write text "cd \"$PROJECT_DIR\""
    write text "source venv/bin/activate"
    write text "ipython"
  end tell
end tell
EOF