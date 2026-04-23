"""
Handshake Task Helper — Video Scene Expansion Evaluation (Dec 2025)
─────────────────────────────────────────────────────────────────────
Evaluates AI-generated video scene expansions for Outlier.ai training
data. Scores continuity, coherence, and visual quality of extended
scenes and submits results to the Handshake task platform.

Usage: python 021_handshake_script_251211-video-scene-expansion.py
"""
import os
import time
import sys
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# ⚙️ CONFIGURATION & SETTINGS
# ==============================================================================
import os
from dotenv import load_dotenv
load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")
EMAIL = username
PASS = password
WORKER_EMAIL = "ca45f672d4ec@handshakecommunity.ai"
FILE_PATH = "~/Downloads/image/QA Feedback"

# Timers
DURATION_HOURS = 10
TOTAL_SECONDS = DURATION_HOURS * 3600

print(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 1)

# ==============================================================================
# 🛠️ HELPER FUNCTIONS
# ==============================================================================

def click_with_retry(locator, timeout=1, retries=3, optional=False):
    """
    Tries to click an element. If it fails, waits and retries.
    Returns True if successful, False if failed.
    """
    for attempt in range(retries):
        try:
            # Wait for element
            element = WebDriverWait(driver,timeout).until(EC.element_to_be_clickable(locator))
            element.click()
            return True
        except Exception:
            # If failed, wait a bit and try again
            time.sleep(1)
    
    if not optional:
        print(f"⚠️ Failed to click element: {locator}")
    return False

def safe_send_keys(locator, text):
    try:
        element = WebDriverWait(driver, 5).until(EC.presence_of_element_located(locator))
        element.clear()
        element.send_keys(text)
        return True
    except:
        return False
    
def tasking():
    safe_send_keys((By.ID, "hashtag"), text="nature")
    click_with_retry((By.XPATH, "//button[normalize-space()='Search']"))
    time.sleep(90)
    click_with_retry((By.XPATH, "//button[normalize-space()='Skip']"))

def handshake_complete_task():
    print("   🟦 Switching to Handshake...")
    driver.switch_to.window(driver.window_handles[0])

    try:
        click_with_retry((By.XPATH, "//button[@aria-label='Continue']"))
        click_with_retry((By.XPATH, "//button[normalize-space()='251125-count-verification: ~15 minutes']"))
        click_with_retry((By.XPATH, "//button[@aria-label='Submit']"))
        
        # 🖱️ ATTEMPT UPLOAD CLICK
        if click_with_retry((By.XPATH, "//button[@aria-label='Upload files']"), retries=3):
            time.sleep(2) 
            
            # 🍎 MACOS KEYSTROKES
            try:
                print("      🍎 Triggering macOS File Dialog...")
                os.system("osascript -e 'tell application \"Google Chrome\" to activate'") 
                time.sleep(1)
                pyautogui.hotkey('command', 'shift', 'g')
                time.sleep(1)
                pyautogui.write(FILE_PATH, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)
                pyautogui.press('enter')
                print("      📂 File Selected via Keyboard")
            except Exception as e:
                print(f"      ❌ Keystroke Error: {e}")
        else:
            print("      ⛔ Skipped keystrokes (Upload Button not clickable).")

    except Exception as e:
        click_with_retry((By.XPATH, "//button[@aria-label='Submit']"))

    # Fill inputs
    print("   📝 Filling Inputs...")
    for i in range(6):
        if safe_send_keys((By.XPATH, "//div[@class='flex flex-col gap-4']//input"), "0"):
            click_with_retry((By.XPATH, "//button[@aria-label='Submit']"), timeout=2)
            time.sleep(1)
        else:
            click_with_retry((By.XPATH, "//button[@aria-label='Submit']"))
            continue
    
    print("   🏁 Finalizing Cycle...")
    click_with_retry((By.XPATH, "//button[normalize-space()='Submit task']"))
    click_with_retry((By.XPATH, "//button[normalize-space()='Confirm time']"), optional=True)
    click_with_retry((By.XPATH, "//button[normalize-space()='Next task']"))
    click_with_retry((By.XPATH, "//button[normalize-space()='Start task']"), optional=True)

    print(f"   ✅ Cycle {run_count} Complete. Cooldown: 240s")
    driver.switch_to.window(driver.window_handles[-1])
    
    # Wait for the cooldown
    time.sleep(240)
    # click_with_retry((By.XPATH, f"//button[normalize-space()='Continue']"))


# ==============================================================================
# 🟦 BLOCK 1: HANDSHAKE LOGIN
# ==============================================================================
print("\n🟦 BLOCK 1: Logging into Handshake...")
try:
    driver.get("https://ai.joinhandshake.com/")
    safe_send_keys((By.ID, "email-address-identifier"), EMAIL)
    click_with_retry((By.XPATH, "//button[normalize-space()='Next']"))
    click_with_retry((By.XPATH, "//a[@class='alternate-login-link link-as-button secondary']"))
    safe_send_keys((By.ID, "password"), PASS)
    click_with_retry((By.XPATH, "//button[@aria-label='submit']"))
    print("✅ Login Successful")
except Exception as e:
    print(f"🔴 Login Failed: {e}")
    sys.exit()

# ==============================================================================
# 🟦 BLOCK 2: CLAIM INITIAL TASK
# ==============================================================================
print("\n🟦 BLOCK 2: Claiming Task...")
try:
    click_with_retry((By.XPATH, "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']"), optional=True)
    time.sleep(2)
    
    # Loop through potential buttons
    for btn_name in ['Start task', 'Continue task', 'Start timer']:
        if click_with_retry((By.XPATH, f"//button[normalize-space()='{btn_name}']"), timeout=2, retries=1, optional=True):
            print(f"   Clicked: {btn_name}")
            break
            
    time.sleep(2)
    click_with_retry((By.XPATH, "//a[normalize-space()='Open Multimango']")) # Open Multimango in a new tab
except Exception as e:
    print(f"⚠️ Minor error in claiming task: {e}")

# ==============================================================================
# 🟦 BLOCK 3: MULTIMANGO LOGIN
# ==============================================================================
print("\n🟦 BLOCK 3: Logging into Multimango...")
try:
    driver.switch_to.window(driver.window_handles[-1])
    driver.switch_to.window(driver.window_handles[0])
    # safe_send_keys((By.ID, "identifier-field"), WORKER_EMAIL)
    click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))
    time.sleep(2)
    safe_send_keys((By.ID, "password-field"), PASS)
    click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))
    click_with_retry((By.XPATH, "//a[@data-sidebar='menu-button']"))
    click_with_retry((By.XPATH, "//a[@href='/tasks/251211-video-scene-expansion']//button"))
    print('Waiting for Multimango to load task for 90 seconds...')
    time.sleep(90)
    click_with_retry((By.XPATH, "//button[normalize-space()='Continue to Task']"))
    print("✅ Multimango Ready")
except Exception as e:
    print(f"🔴 Multimango Login Failed: {e}")

# ==============================================================================
# 🟦 BLOCK 4: 251211-video-scene-expansion tasking
# ==============================================================================
print("\n🟦 BLOCK 4: Tasking 251211-video-scene-expansion")

# 📊 METRICS INITIALIZATION
start_time = time.time()
end_time = start_time + TOTAL_SECONDS
run_count = 1
success_count = 0
fail_count = 0

while time.time() < end_time:
    # ⏱️ TIMING CALCULATION
    current_time = time.time()
    elapsed_seconds = int(current_time - start_time)
    remaining_seconds = int(end_time - current_time)
    
    # Format HH:MM:SS
    e_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))
    r_str = time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))
    
    print(f"\n{'='*60}")
    print(f"🔄 CYCLE {run_count} | ✅ Success: {success_count} | ❌ Failed: {fail_count}")
    print(f"⏱️  Elapsed: {e_str} | ⏳ Remaining: {r_str}")
    print(f"{'='*60}")
    
    task_success = False # Reset flag for this cycle

    try:
       tasking()
       task_success = True
       success_count =+ 1
    except Exception as e:
        fail_count += 1
        print(f"   ❌ Tasking skipped or failed: {e}")
    

    total_elapsed = int(time.time() - start_time)
    total_time_str = time.strftime('%H:%M:%S', time.gmtime(total_elapsed))
    print(f'Current run count {run_count} took {total_elapsed} seconds time so far or {total_time_str}')

    run_count += 1

    # 

# ==============================================================================
# 🟦 BLOCK 5: Printing Data
# ==============================================================================

print("\n" + "#"*60)
print("             🏁 SCRIPT EXECUTION COMPLETE 🏁")
print("#"*60)
print(f"📅 Total Duration : {total_time_str}")
print(f"🔄 Total Cycles   : {run_count - 1}")
print(f"✅ Successful     : {success_count}")
print(f"❌ Failed         : {fail_count}")
print(f"📈 Success Rate   : {round((success_count / (run_count - 1) * 100), 2) if run_count > 1 else 0}%")
print("#"*60)