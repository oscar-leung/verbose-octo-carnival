"""
Export LinkedIn session cookies → linkedin_cookies.json
Run this LOCALLY (not on PA) whenever cookies expire.

Usage:
  python scripts/export_linkedin_cookies.py

Then upload to PythonAnywhere:
  scp linkedin_cookies.json holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/
"""

import json
import os
import sys
import time

from selenium import webdriver

OUTPUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "linkedin_cookies.json")

def main():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_argument("--start-maximized")
    driver = webdriver.Chrome(options=opts)

    print("Opening LinkedIn... Log in if prompted. You have 120 seconds.")
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(5)

    if "login" in driver.current_url or "authwall" in driver.current_url:
        print("Not logged in — log in in the browser window. Waiting 120s...")
        for _ in range(120):
            time.sleep(1)
            if "feed" in driver.current_url:
                break

    cookies = driver.get_cookies()
    driver.quit()

    with open(OUTPUT, "w") as f:
        json.dump(cookies, f, indent=2)

    print(f"✓ Exported {len(cookies)} cookies → {OUTPUT}")
    print()
    print("Upload to PythonAnywhere:")
    print(f"  scp {OUTPUT} holymushy@ssh.pythonanywhere.com:~/verbose-octo-carnival/linkedin_cookies.json")

if __name__ == "__main__":
    main()
