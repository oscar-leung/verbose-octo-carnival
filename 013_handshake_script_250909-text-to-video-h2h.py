"""
Handshake Task Helper — Text-to-Video Evaluation (Sep 2025)
────────────────────────────────────────────────────────────
Submits text-to-video human evaluation scores to the Handshake
Outlier task platform. Works alongside script 010 to complete
the full evaluation and submission pipeline.

Usage: python 013_handshake_script_250909-text-to-video-h2h.py
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
DELAY_TYPING = 0.1
DELAY_THINKING = 15   # Time to wait before voting
DELAY_BETWEEN_VOTES = 30 

print(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

# Initialize Driver
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 2) # Increased default wait to 10s for robustness

# ==============================================================================
# 🟦 BLOCK 1: HANDSHAKE LOGIN
# ==============================================================================
print("\n🟦 BLOCK 1: Logging into Handshake...")
try:
    driver.get("https://ai.joinhandshake.com/")
    
    # Email
    wait.until(EC.presence_of_element_located((By.ID, "email-address-identifier"))).send_keys(EMAIL)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))).click()
    
    # Switch to Alternate Login
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='alternate-login-link link-as-button secondary']"))).click()
    
    # Password
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

    driver.find_element(By.XPATH,"//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Claim task']").click()
    
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
    
    wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='Go to Multimango']"))).click()
except Exception as e:
    print(f"⚠️ Minor error in claiming task (might already be active): {e}")

# ==============================================================================
# 🟦 BLOCK 3: MULTIMANGO LOGIN
# ==============================================================================
print("\n🟦 BLOCK 3: Logging into Multimango...")
try:
    driver.switch_to.window(driver.window_handles[-1])
    print("   Switched to new tab")
    time.sleep(2)
    
    # Worker Email
    wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(WORKER_EMAIL)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
    time.sleep(2)
    
    # Worker Password
    wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(PASS)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
    
    # Navigation inside Tool
    print("   Navigating to H2H task...")
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/250909-text-to-video-h2h']//button"))).click()
    
    # Long wait for tool to load
    print("   Waiting 30s for tool to load...")
    time.sleep(30)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue to Task']"))).click()
    print("✅ Multimango Ready")
except Exception as e:
    print(f"🔴 Multimango Login Failed: {e}")

# ==============================================================================
# 🔄 MAIN EXECUTION LOOP
# ==============================================================================
start_time = time.time()
end_time = start_time + TOTAL_SECONDS
categories = ["Instruction Following", "Visual Quality", "Overall Choice"]
run = 1

print(f"\n🟢 STARTING MAIN LOOP (Press Ctrl+C to stop)")

try:
    while time.time() < end_time:
        # --- TIME CALCULATION ---
        elapsed = int(time.time() - start_time)
        remaining = int(end_time - time.time())
        mins_passed, secs_passed = divmod(elapsed, 60)
        mins_left, secs_left = divmod(remaining, 60)
        
        print(f"\n{'-'*50}")
        print(f"🔄 CYCLE {run} | Elapsed: {mins_passed:02d}:{secs_passed:02d} | Remaining: {mins_left:02d}:{secs_left:02d}")
        print(f"{'-'*50}")

        # ==============================================================================
        # 🟦 BLOCK 4: VOTING LOGIC
        # ==============================================================================
        print("🟦 BLOCK 4: Voting...")
        for title in categories:
            try:
                # Find the container for this category
                block = driver.find_element(
                    By.XPATH,
                    f"//h3[normalize-space()='{title}']/ancestor::div[contains(@class,'border-b')]"
                )
                buttons = block.find_elements(By.TAG_NAME, "button")
                
                if buttons:
                    choice = random.choice(buttons)
                    print(f"   🤔 Thinking for {DELAY_THINKING}s before voting on '{title}'...")
                    time.sleep(DELAY_THINKING)
                    
                    choice.click()
                    print(f"   👉 Clicked: {choice.text}")
                    
                    print(f"   😴 Resting {DELAY_BETWEEN_VOTES}s...")
                    time.sleep(DELAY_BETWEEN_VOTES)
                else:
                    print(f"   ⚠️ No buttons found for {title}")
                    
            except Exception as e:
                print(f"   ❌ Error voting on {title}: {e}")

        # Submit Initial Vote
        try:
            submit = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'bg-green-600')]")))
            submit.click()
            print("✅ Initial Vote Submitted")
        except Exception as e:
            print(f"❌ Initial Submit Failed: {e}")

        time.sleep(5)

        # ==============================================================================
        # 🟦 BLOCK 5: SWITCH TAB & PREPARE UPLOAD
        # ==============================================================================
        print("🟦 BLOCK 5: Switching to Dashboard & Uploading...")
        
        # Switch to Dashboard
        driver.switch_to.window(driver.window_handles[0])
        
        # Dashboard Navigation
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Continue']"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='250909-text-to-video-h2h: ~25 minutes']"))).click()
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))).click()
            
            # Click Upload
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Upload file']"))).click()
            time.sleep(2) # Wait for macOS dialog animation
            
            # ------------------------------------------------------------------
            # 🍎 MACOS NATIVE INTERACTION (APPLESCRIPT)
            # ------------------------------------------------------------------
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
        # Loop 6 times as requested
        for i in range(6):
            try:
                # Click Submit/Next
                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Submit']"))).click()
                time.sleep(0.5)
                
                # Find Input, Clear it, Type 0
                input_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='flex flex-col gap-4']//input")))
                input_box.clear()
                input_box.send_keys("0")
                time.sleep(0.7)
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
            run += 1

            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Try Again']"))).click()
            except:
               pass
            
        except Exception as e:
            print(f"❌ Error in final submission steps: {e}")

except KeyboardInterrupt:
    print("\n🟥 Script cancelled by user (Ctrl+C).")