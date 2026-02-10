import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import pyautogui
from dotenv import load_dotenv
import os
from datetime import datetime
# Add these imports
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load variables from .env
load_dotenv()

# Replace your current driver creation with:
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

username = os.getenv("LINKIN_USERNAME")
password = os.getenv("LINKIN_PASSWORD")


driver = webdriver.Chrome()
driver.get("https://google.com")
driver.
# driver.find_element(By.ID,"username").send_keys(username)
# driver.find_element(By.ID,"password").send_keys(password)
