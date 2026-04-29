#!/bin/bash
# One-time PythonAnywhere setup — run this from a PA Bash console.
#
#   pip --version    # confirm you're on PA
#   cd ~
#   git clone https://github.com/oscar-leung/verbose-octo-carnival.git
#   cd verbose-octo-carnival
#   bash pythonanywhere/setup.sh
#
# Re-running is safe: it only creates things that don't already exist.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/venv-pa"
PY_VERSION="${PY_VERSION:-3.10}"   # PA supports 3.10/3.11/3.12 — pick what `which python3.10` resolves

echo "==> Project: $PROJECT_DIR"
echo "==> Venv:    $VENV_DIR"
echo "==> Python:  $PY_VERSION"

# ── 1. Create venv ────────────────────────────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
    echo "==> Creating venv-pa with Python $PY_VERSION"
    "python$PY_VERSION" -m venv "$VENV_DIR"
else
    echo "==> venv-pa already exists, skipping create"
fi

# ── 2. Install requirements ───────────────────────────────────────────────────
echo "==> Installing PA requirements"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/pythonanywhere/requirements_pa.txt"

# ── 3. Sanity-check Chromium + chromedriver ───────────────────────────────────
echo "==> Checking Chromium / chromedriver availability"
CHROMIUM_BIN="$(command -v chromium-browser || command -v chromium || true)"
CHROMEDRIVER_BIN="$(command -v chromedriver || true)"

if [ -z "$CHROMIUM_BIN" ]; then
    echo "    !! No chromium-browser on PATH."
    echo "       PA Hacker plan and above ship Chromium under /usr/bin/chromium-browser."
    echo "       On the free tier this is NOT installed and the scripts will not run here."
fi
if [ -z "$CHROMEDRIVER_BIN" ]; then
    echo "    !! No chromedriver on PATH."
    echo "       Selenium 4 will try Selenium Manager — that needs outbound HTTPS to googleapis.com,"
    echo "       which is gated on the free tier. On Hacker+ this resolves automatically."
fi
[ -n "$CHROMIUM_BIN" ]    && echo "    chromium-browser : $CHROMIUM_BIN ($($CHROMIUM_BIN --version 2>/dev/null || echo '?'))"
[ -n "$CHROMEDRIVER_BIN" ] && echo "    chromedriver     : $CHROMEDRIVER_BIN ($($CHROMEDRIVER_BIN --version 2>/dev/null || echo '?'))"

# ── 4. Create runs/ folder ────────────────────────────────────────────────────
mkdir -p "$PROJECT_DIR/runs"
echo "==> runs/ ready"

# ── 5. Cookie-file presence check ─────────────────────────────────────────────
echo "==> Checking for cookie files"
for cookie in handshake_cookies.json linkedin_cookies.json; do
    if [ -f "$PROJECT_DIR/$cookie" ]; then
        echo "    found $cookie"
    else
        echo "    MISSING $cookie — generate locally with scripts/export_${cookie%_cookies.json}_cookies.py"
        echo "                       then scp it to ~/verbose-octo-carnival/ on PA"
    fi
done

# ── 6. .env presence check ────────────────────────────────────────────────────
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "==> .env found"
else
    echo "==> MISSING .env — copy your local .env to ~/verbose-octo-carnival/.env on PA"
fi

# ── 7. Make wrappers executable ───────────────────────────────────────────────
chmod +x "$PROJECT_DIR/pythonanywhere/run_linkedin_pa.sh"  || true
chmod +x "$PROJECT_DIR/pythonanywhere/run_handshake_pa.sh" || true

echo
echo "==> Setup complete."
echo "    Next: paste this into PA → Tasks → Schedule a new task:"
echo
echo "      bash $PROJECT_DIR/pythonanywhere/run_linkedin_pa.sh"
echo "      bash $PROJECT_DIR/pythonanywhere/run_handshake_pa.sh"
echo
