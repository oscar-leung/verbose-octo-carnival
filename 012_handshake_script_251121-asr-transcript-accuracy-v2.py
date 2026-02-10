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
import pyautogui
import pyscreeze


load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)
driver.get("https://ai.joinhandshake.com/")
wait.until(EC.presence_of_element_located((By.ID, "email-address-identifier"))).send_keys(username)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@class='alternate-login-link link-as-button secondary']"))).click()

wait.until(EC.presence_of_element_located((By.ID, "password"))).send_keys(password)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='submit']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Claim task']"))).click()
driver.find_element(By.XPATH,"//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Claim task']").click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue task']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue task']"))).click()
try:
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Go to Multimango']"))).click()
except:
    wait.until(EC.element_to_be_clickable((By.XPATH, "//a[normalize-space()='Open Multimango']"))).click()
    
driver.switch_to.window(driver.window_handles[-1])

wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys("ca45f672d4ec@handshakecommunity.ai")
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
time.sleep(2)
wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys("Bumblebee5%2025")
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/251121-asr-transcript-accuracy-v2']//button"))).click()
time.sleep(30)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue to Task']"))).click()
try:
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Select locale']"))).click()
    # wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='en']"))).click()
    # wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//span[normalize-space()='ja' or normalize-space()='JA']" ))).click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role='option']//span[normalize-space()='zh' or normalize-space()='ZH']" ))).click()
except:
    pass
time.sleep(2)

task = 1

# contract agreement states 10-40 hrs. So do 10 hours to be safe per day
duration = 600 * 60 # 600 minutes = 10 hours
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
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit review']"))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Refresh queue']"))).click()
        print("✔️ Clicked 'Submit review' and 'Refresh queue'.")
    except Exception as e:
        pass
    time.sleep(30)
    run += 1
print("\n⏱️ Timer finished!")

# driver.switch_to.window(driver.window_handles[0])
# wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue']"))).click()
# wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='251121-asr-transcript-accuracy-v2']"))).click()
# wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
# wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Upload file']"))).click()

# just leave this on and do this part manually unless needed for now

# pyautogui.focus('Open')  # Focus the 'Open' dialog
# pyautogui.locateOnScreen('Screenshot 2025-11-29 at 1.01.40 PM')  # Image of the file path input box
# img_path = os.path.expanduser("~/Downloads/image/image.png")
# center   = pyautogui.locateCenterOnScreen(img_path)
# print(center)
# pyautogui.click()
# pyautogui.press('up')
# pyautogui.hotkey("return")
# pyautogui.hotkey("down")