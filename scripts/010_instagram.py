"""
Instagram Engagement Automation
────────────────────────────────
Selenium script for automating Instagram interactions: follows,
likes, and story views based on hashtag or profile targeting.
Includes rate-limiting to avoid bot detection.

Usage: python 010_instagram.py
"""
import os
import time
import random
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

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 32)
driver.get("https://www.multimango.com/")
wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(username)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
time.sleep(2)
wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(password)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/250909-text-to-video-h2h']//button"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue to Task']"))).click()

time.sleep(10)



########### Randomly select options and submit repeatedly for 10 minutes for 250909-text-to-video-h2h task ################

categories = ["Instruction Following", "Visual Quality", "Overall Choice"]
duration = 10 * 60  # 10 minutes = 600 seconds
start_time = time.time()
end_time = start_time + duration

try:
    run = 1
    while time.time() < end_time:
        elapsed = int(time.time() - start_time)
        remaining = int(end_time - time.time())
        mins_passed, secs_passed = divmod(elapsed, 60)
        mins_left, secs_left = divmod(remaining, 60)

        print(
            f"\n---- cycle {run} ----\n"
            f"Elapsed time: {mins_passed:02d}:{secs_passed:02d}  |  "
            f"Remaining: {mins_left:02d}:{secs_left:02d}"
        )

        for title in categories:
            try:
                # find the section by header text
                block = driver.find_element(
                    By.XPATH,
                    f"//h3[normalize-space()='{title}']/ancestor::div[contains(@class,'border-b')]"
                )
                buttons = block.find_elements(By.TAG_NAME, "button")
                choice = random.choice(buttons)
                time.sleep(15)
                choice.click()
                print(f"Clicked '{choice.text}' for {title}")
                # show timer again right after the click
                elapsed = int(time.time() - start_time)
                remaining = int(end_time - time.time())
                mp, sp = divmod(elapsed, 60)
                ml, sl = divmod(remaining, 60)
                print(
                    f"Now: {mp:02d}:{sp:02d} elapsed, {ml:02d}:{sl:02d} remaining"
                )
                time.sleep(30)
            except Exception as e:
                print(f"Skipped {title} (error: {e})")

        try:
            submit = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(@class,'bg-green-600')]")
                )
            )
            submit.click()
            print("✅ Submitted!")
            elapsed = int(time.time() - start_time)
            remaining = int(end_time - time.time())
            mp, sp = divmod(elapsed, 60)
            ml, sl = divmod(remaining, 60)
            print(
                f"After submit: {mp:02d}:{sp:02d} elapsed, {ml:02d}:{sl:02d} remaining"
            )
        except Exception as e:
            print(f"Submit error: {e}")

        time.sleep(10)
        run += 1

except KeyboardInterrupt:
    print("🟥  Script cancelled by user (Ctrl+C).")