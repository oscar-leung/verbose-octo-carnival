"""
Export Handshake session cookies → handshake_cookies.json
Run this LOCALLY (not on PA) whenever cookies expire (~monthly).

Usage:
  python scripts/export_handshake_cookies.py

Then upload the output file to PythonAnywhere:
  scp handshake_cookies.json holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import library.uc_compat  # noqa: F401
import undetected_chromedriver as uc

CHROME_PROFILE = os.path.expanduser("~/.chrome-handshake-profile")
OUTPUT        = os.path.join(os.path.dirname(os.path.dirname(__file__)), "handshake_cookies.json")

def main():
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        p = os.path.join(CHROME_PROFILE, lock)
        if os.path.exists(p) or os.path.islink(p):
            try:
                os.remove(p)
            except Exception:
                pass

    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1440,900")
    opts.add_argument(f"--user-data-dir={CHROME_PROFILE}")
    driver = uc.Chrome(options=opts, use_subprocess=True, version_main=147)

    print("Navigating to Handshake...")
    driver.get("https://app.joinhandshake.com/explore")
    time.sleep(6)

    if "login" in driver.current_url:
        print("Not logged in — logging in now (you have 60s)...")
        time.sleep(60)

    cookies = driver.get_cookies()
    driver.quit()

    with open(OUTPUT, "w") as f:
        json.dump(cookies, f, indent=2)

    print(f"✓ Exported {len(cookies)} cookies → {OUTPUT}")
    print()
    print("Upload to PythonAnywhere:")
    print(f"  scp {OUTPUT} holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/handshake_cookies.json")

if __name__ == "__main__":
    main()
