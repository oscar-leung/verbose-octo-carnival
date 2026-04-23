"""
Handshake Task Helper — Text-to-Video Evaluation Variant (Sep 2025)
─────────────────────────────────────────────────────────────────────
Alternate submission flow for text-to-video human evaluations on
the Handshake Outlier platform. Handles edge cases and different
task configurations from the primary script 013.

Usage: python 018_handshake_script_250909-text-to-video-h2h.py
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
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/250909-text-to-video-h2h']//button"))).click()
    print("✅ Multimango Ready")
except Exception as e:
    print(f"🔴 Multimango Login Failed: {e}")

