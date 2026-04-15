"""
Chest/Reward Opening Automation
────────────────────────────────
Selenium script that automates clicking reward chests or bonus buttons
on a prize/gaming platform. Loops through available chests and collects
rewards without manual interaction.

Usage: python 004_open_chest.py
"""
import logging
import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException

# Load variables from .env
load_dotenv()
username = os.getenv("habitica_email")
password = os.getenv("habitica_password")


driver = webdriver.Chrome()
driver.get("https://habitica.com/login?redirectTo=%2Fparty")


wait = WebDriverWait(driver, 60)
username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id="usernameInput"]')))
username_input.send_keys(username)

password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id="passwordInput"]')))
password_input.send_keys(password)

signin_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class="btn btn-info"]')))
signin_button.click()

driver.get("https://habitica.com/shops/market")

# Define the number of attempts
num_attempts = 36

for _ in range(34):

        # Wait for the chest button to be present
        chest_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.shop_armoire')))
        chest_btn.click()

        # Wait for the buy button to be present
        buy_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[tabindex="0"]')))
        buy_btn.click()

        # You may want to add some additional logic here to handle what happens after clicking the buy button
        time.sleep(1)
