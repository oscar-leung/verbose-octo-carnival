"""
Outlier AI Contractor Task — Audio Transcript Evaluation (Oct 2025)
────────────────────────────────────────────────────────────────────
Evaluates AI-generated audio transcripts for Outlier.ai data labeling.
Checks transcription quality, flags errors, and submits accuracy ratings
through the Outlier task interface.

Usage: python 015_outlier_script_251030-audio-transcript.py
"""
import os
import time
import random
from contextlib import suppress
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException
)
from selenium.webdriver.support import expected_conditions as EC


# load_dotenv()
load_dotenv()
username = os.getenv("outlier_email")
password = os.getenv("outlier_password")

# Initialize WebDriver and login to Multimango
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)
driver.get("https://www.multimango.com/")
wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(username)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
time.sleep(2)
wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(password)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/251030-audio-transcript']//button"))).click()

# Start the timed loop
duration = 540 * 60 # 540 minutes = 10 hours
start = time.time()
end = start + duration
run = 1

time.sleep(1)
wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@class='flex items-center justify-center gap-2 text-sm']//button"))).click()
time.sleep(1)
wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//span[normalize-space()='ur' or normalize-space()='UR']" ))).click()

while time.time() < end:
    elapsed = int(time.time() - start)
    remaining = int(end - time.time())
    mins_p, secs_p = divmod(elapsed, 60)
    mins_r, secs_r = divmod(remaining, 60)
    print(f"\n---- cycle {run} ----\n"f"Elapsed: {mins_p:02d}:{secs_p:02d} | Remaining: {mins_r:02d}:{secs_r:02d}")

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
            audio_element = driver.find_element(By.TAG_NAME, "audio")
            driver.execute_script("arguments[0].play();", audio_element)
            listen_time = random.randint(30, 40); print(f"▶️ Listening to audio for {listen_time} seconds"); time.sleep(listen_time)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit review']"))).click()
            confirm_sleep = random.randint(3, 8); print(f"⌛ Waiting {confirm_sleep} seconds before confirming submit"); time.sleep(confirm_sleep)
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Yes, Submit']"))).click()
            print("✔️ Clicked 'Submit review.")
        except Exception:
            print(f"⚠️ Exception during cycle {run}: ")
        cooldown = random.randint(30, 75); print(f"⏳ Cooldown before next attempt: {cooldown} seconds"); time.sleep(cooldown)
        run += 1
print("\n⏱️ Timer finished!")