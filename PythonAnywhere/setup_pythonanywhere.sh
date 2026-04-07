#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# PythonAnywhere Setup Script
# Run this once in a PythonAnywhere Bash console to install dependencies
# and register the two scheduled tasks (035 + 029).
#
# Usage (in PythonAnywhere Bash console):
#   bash setup_pythonanywhere.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
PA_USER=$(whoami)
REPO_DIR="/home/$PA_USER/verbose-octo-carnival"

echo "=== PythonAnywhere Setup for Oscar's Job Bot ==="
echo "User: $PA_USER"
echo "Repo: $REPO_DIR"
echo ""

# ── 1. Install Python packages ────────────────────────────────────────────────
echo "[1/4] Installing Python packages..."
pip3 install --user \
    selenium \
    python-dotenv \
    gspread \
    google-auth \
    webdriver-manager

echo "Done."

# ── 2. Install Chromium + Chromedriver ────────────────────────────────────────
echo ""
echo "[2/4] Checking Chromium..."
if command -v chromium-browser &>/dev/null; then
    CHROME_VER=$(chromium-browser --version | grep -oP '[\d.]+' | head -1)
    echo "  Chromium found: $CHROME_VER"
else
    echo "  WARNING: chromium-browser not found."
    echo "  PythonAnywhere free tier does not support Chromium."
    echo "  Upgrade to a paid plan or use the selenium-wire/requests approach."
fi

# ── 3. Set up .env file ───────────────────────────────────────────────────────
echo ""
echo "[3/4] Checking .env..."
ENV_FILE="$REPO_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "  Creating $ENV_FILE — fill in your credentials."
    cat > "$ENV_FILE" << 'EOF'
LINKIN_USERNAME=your_linkedin_email@gmail.com
LINKIN_PASSWORD=your_linkedin_password
handshake_email=your_handshake_email@gmail.com
handshake_password=your_handshake_password
GOOGLE_SERVICE_ACCOUNT_JSON=/home/YOUR_PA_USER/verbose-octo-carnival/service_account.json
GOOGLE_SHEET_ID=your_google_sheet_id
EOF
    echo "  Created. Edit $ENV_FILE before running scripts."
else
    echo "  .env already exists."
fi

# ── 4. Print scheduled task commands ─────────────────────────────────────────
echo ""
echo "[4/4] Add these as Scheduled Tasks in PythonAnywhere Dashboard:"
echo ""
echo "  Dashboard → Tasks → Add a new task"
echo ""
echo "  Task 1 — LinkedIn Easy Apply (daily at 08:00)"
echo "    Hour: 8  Minute: 0"
echo "    Command: cd $REPO_DIR && python3 035_linkedin_easy_apply_pa.py"
echo ""
echo "  Task 2 — LinkedIn Email Scraper (daily at 09:00)"
echo "    Hour: 9  Minute: 0"
echo "    Command: cd $REPO_DIR && python3 029_linkedIn_emails_script.py"
echo ""
echo "  Note: 036 (Handshake) is blocked by Cloudflare in headless mode."
echo "  Run 033_handshake_applications.py locally instead."
echo ""
echo "=== Setup complete ==="
