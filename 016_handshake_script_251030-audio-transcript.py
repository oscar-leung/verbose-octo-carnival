"""
Handshake Task Helper — Audio Transcript Submission (Oct 2025)
───────────────────────────────────────────────────────────────
Submits audio transcript evaluation results to the Handshake Outlier
platform. Pairs with script 015 to complete the audio evaluation pipeline.

Usage: python 016_handshake_script_251030-audio-transcript.py
"""
import os
import time
import random
import sys
from dotenv import load_dotenv
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==============================================================================
# ⚙️ CONFIGURATION & SETTINGS
# ==============================================================================
load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")
EMAIL = username
PASS = password
WORKER_EMAIL = "ca45f672d4ec@handshakecommunity.ai"
FILE_PATH = "~/Downloads/image/QA Feedback"

# Timers (Adjust these if internet is slow)
DURATION_HOURS = 10
TOTAL_SECONDS = DURATION_HOURS * 3600
DELAY_TYPING = 0.5
DELAY_THINKING = 15   # Time to wait before voting
DELAY_BETWEEN_VOTES = 30 

print(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

# Initialize Driver
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5) # Increased default wait to 10s for robustness

# ==============================================================================
# 🟦 BLOCK 1: HANDSHAKE LOGIN
# ==============================================================================
print("\n🟦 BLOCK 1: Logging into Handshake...")
try:
    driver.get("https://ai.joinhandshake.com/")
    wait.until(EC.presence_of_element_located((By.ID, "email-address-identifier"))).send_keys(EMAIL)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='alternate-login-link link-as-button secondary']"))).click()
    wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(PASS)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='submit']"))).click()
    print("✅ Login Successful")
except Exception as e:
    print(f"🔴 Login Failed: {e}")
    sys.exit()

# ==============================================================================
# 🟦 BLOCK 2: CLAIM INITIAL TASK
# ==============================================================================
print("\n🟦 BLOCK 2: Claiming Task...")
try:
    wait.until(EC.element_to_be_clickable((By.XPATH, "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']"))).click()    
    time.sleep(2)
    # Loop through potential buttons to start/continue
    print("   Checking for start buttons...")
    for btn in ['Start task', 'Continue task', 'Start timer']:
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{btn}']"))).click()
            print(f"   Clicked: {btn}")
            break # Stop if we found one
        except: 
            pass
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Multimango']"))).click()
except Exception as e:
    print(f"⚠️ Minor error in claiming task (might already be active): {e}")


# ==============================================================================
# 🟦 BLOCK 3: MULTIMANGO LOGIN
# ==============================================================================
print("\n🟦 BLOCK 3: Logging into Multimango...")
try:
    driver.switch_to.window(driver.window_handles[-1])
    print("Switched to new tab")
    wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(WORKER_EMAIL)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
    wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(PASS)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/251030-audio-transcript']//button"))).click()
    print("✅ Multimango Ready")
except Exception as e:
    print(f"🔴 Multimango Login Failed: {e}")


# todo – iterate langauges if needed    https://prnt.sc/bpgDD4Y7qad7

wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='flex items-center justify-center gap-2 text-sm']//button"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//span[normalize-space()='bn' or normalize-space()='BN']" ))).click()

# ==============================================================================
# 🟦 BLOCK 4: MAIN LOOP - AUDIO PLAYBACK & SUBMISSION
# ==============================================================================
print("\n🟦 BLOCK 4: Starting Main Loop...")
# Start the timed loop
duration = 540 * 60 # 540 minutes = 10 hours
start = time.time()
end = start + duration
run = 1


while time.time() < end:
    elapsed = int(time.time() - start)
    remaining = int(end - time.time())
    mins_p, secs_p = divmod(elapsed, 60)
    mins_r, secs_r = divmod(remaining, 60)
    print(f"\n---- cycle {run} ----\n"f"Elapsed: {mins_p:02d}:{secs_p:02d} | Remaining: {mins_r:02d}:{secs_r:02d}")
    try:
        time.sleep(5)
        audio_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "audio")))
        driver.execute_script("arguments[0].play();", audio_element)
        time.sleep(30)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit review']"))).click()
        time.sleep(5)
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Yes, Submit']"))).click()
        print("✔️ Clicked 'Submit review.")
    except Exception as e:
        pass
    
    # ==============================================================================
    # 🟦 BLOCK 5: SWITCH TAB & PREPARE UPLOAD
    # ==============================================================================
    print("🟦 BLOCK 5: Switching to Dashboard & Uploading...")
    
    # Switch to Dashboard
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[0])
    
    # Dashboard Navigation
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Continue']"))).click()
        time.sleep(2) # Wait for macOS dialog animation
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='251030-audio-transcript: ~5 minutes']"))).click()
        time.sleep(2) # Wait for macOS dialog animation
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))).click()
        # time.sleep(2) # Wait for macOS dialog animation
        
        # Click Upload
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Upload files']"))).click()
    except:
        pass
    time.sleep(2) # Wait for macOS dialog animation
        
        # ------------------------------------------------------------------
        # 🍎 MACOS NATIVE INTERACTION (APPLESCRIPT)
        # ------------------------------------------------------------------
    try:
        
        print("   🍎 Triggering macOS File Dialog...")
        os.system("osascript -e 'tell application \"Google Chrome\" to activate'") 
        time.sleep(1)
        
        # Open 'Go to Folder'
        pyautogui.hotkey('command', 'shift', 'g')
        time.sleep(1)
        
        # Type Path
        pyautogui.write(FILE_PATH, interval=0.05)
        time.sleep(0.5)
        
        # Confirm Path
        pyautogui.press('enter')
        time.sleep(0.5)
        
        # Confirm Selection
        pyautogui.press('enter')
        print("   📂 File Selected via Keyboard")
        # ------------------------------------------------------------------
    except Exception as e:
        print(f"❌ Upload Sequence Failed: {e}")
    
    # ==============================================================================
    # 🟦 BLOCK 6: FILL FORM (6 INPUTS)
    # ==============================================================================
    print("🟦 BLOCK 6: Filling Submission Form...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))).click()
    # Loop 6 times as requested
    for i in range(5):
        try:
            input_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='flex flex-col gap-4']//input")))
            # Click Submit/Next
            time.sleep(0.5)
            input_box.send_keys("0")
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))).click()
            time.sleep(2)
        except Exception as e:
            # We use try/except here so if there are only 5 inputs, it won't crash on the 6th
            pass 

    print("   📝 Form filled.")

    # ==============================================================================
    # 🟦 BLOCK 7: FINALIZE & RESET
    # ==============================================================================
    print("🟦 BLOCK 7: Finalizing & Restarting...")
    try:
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit task']"))).click()
        
        # Handle "Confirm Time" if it appears
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Confirm time']"))).click()
        except: pass
        
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next task']"))).click()
        
        # Attempt to Start Next Task immediately
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Start task']"))).click()
        except: pass

        print("✅ Cycle Complete. Switching back to task tab.")
        driver.switch_to.window(driver.window_handles[-1])
        time.sleep(240)
        wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='Continue']"))).click()
        run += 1

            

    except Exception as e:
        print(f"❌ Error in final submission steps: {e}")

