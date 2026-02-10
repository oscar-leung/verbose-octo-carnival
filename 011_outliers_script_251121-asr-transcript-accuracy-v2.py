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
wait = WebDriverWait(driver, 5)
driver.get("https://www.multimango.com/")
wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(username)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
time.sleep(2)
wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(password)
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

duration = 600 * 60 # 540 minutes = 10 hours
# duration = 35 * 60 # 540 minutes = 9 hours
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
