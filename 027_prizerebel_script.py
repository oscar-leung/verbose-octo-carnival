import logging
import time
from selenium import webdriver
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
import random


# helper fn
def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)

    # zoom out (Cmd + -)
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')

def move_window_to_topright():
    """Moves the current window to the top-right corner of the screen (macOS specific)."""
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i') # Move window top right shortcut using magnet app 
    time.sleep(0.2)

def clickWebElement(xpath, timeout=5):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
        driver.execute_script("arguments[0].click();", element)
        logging.info(f"Clicked: {xpath}")
        return True
    except Exception as e:
        logging.debug(f"Click failed: {xpath} | {e}")
        return False

def element_exists(xpath):
    try:
        return driver.find_elements(By.XPATH, xpath) != []
    except:
        return False

def click_continue(sleep=1):
    continue_xpaths = [
        "//input[@id='btn_continue']",
        "//input[@id='ctl00_Content_btnContinue']",
        "//div[@id='oc_in4']",
        "//input[@type='submit' and contains(@value,'Continue')]",
        "//button[normalize-space()='Continue']",
        "//button[normalize-space()='Next']",
        "//input[@value='Continue']"
    ]

    for xp in continue_xpaths:
        if clickWebElement(xp):
            logging.info("➡️ Continue clicked")
            time.sleep(sleep)
            return True

    logging.debug("➡️ No Continue button found")
    return False

def close_current_tab():
    if len(driver.window_handles) > 1:
        driver.close()
        driver.switch_to.window(driver.window_handles[0])




# Initialize variables
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)

driver.get("https://www.prizerebel.com/login")
zoom_out()
move_window_to_topright()

# login


driver.find_element(By.ID, 'loginSubmit').click()


driver.switch_to.window(driver.window_handles[-1])
click_continue()