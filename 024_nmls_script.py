import os
import random
import time
import sys
import logging # New: For better logging
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, StaleElementReferenceException,
    NoSuchWindowException, WebDriverException,
    NoSuchElementException # New: For cases where element is simply not found
)
from selenium.webdriver.common.keys import Keys

# ==============================================================================
# ⚙️ CONFIGURATION & SETTINGS
# ==============================================================================
# EMAIL = 
# PASS = 
# WORKER_EMAIL =
# FILE_PATH = 
DURATION_HOURS = 8  # Total duration to run the script
WAIT_SEC = 5        # Default wait time for elements
# ==============================================================================
# 📝 LOGGING SETUP 
# ==============================================================================
logging.basicConfig(
    level=logging.INFO, # Set to logging.DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nmls.log"), # Log to a file
        logging.StreamHandler(sys.stdout)       # Also print to console
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

# Global variables
driver = None
wait = None

# Store window handles for easier switching
home_window_handle = None


# ==============================================================================
# 🛠️ HELPER FUNCTIONS - Enhanced with logging and specific error handling
# ==============================================================================

def init_driver():
    """Initializes the WebDriver and WebDriverWait."""
    global driver, wait
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Uncomment for headless browser (no UI)
    # options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, WAIT_SEC)
    logger.info("WebDriver initialized.")

def click_with_retry(locator, timeout=WAIT_SEC, retries=3, optional=False):
    """
    Attempts to click an element multiple times.
    Logs errors more specifically.
    """
    last_err = None
    for i in range(retries):
        try:
            el = wait.until(EC.element_to_be_clickable(locator))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            logger.debug(f"Clicked {locator} successfully.")
            return el
        except (TimeoutException, StaleElementReferenceException, NoSuchElementException) as e:
            last_err = e
            logger.warning(f"Attempt {i+1}/{retries}: Failed to click {locator}. Retrying... Error: {e}")
            time.sleep(1) # Wait a bit before retrying
        except Exception as e:
            last_err = e
            logger.error(f"Attempt {i+1}/{retries}: Unexpected error clicking {locator}. Retrying... Error: {e}")
            time.sleep(1)

    if not optional:
        logger.error(f"🔴 Failed to click {locator} after {retries} attempts. Last error: {last_err}")
        raise last_err # Re-raise if not optional and failed
    else:
        logger.info(f"Optional click on {locator} failed, but continuing as it's optional. Last error: {last_err}")
    return None

def safe_send_keys(locator, text, timeout=WAIT_SEC, clear_first=True):
    """
    Safely sends keys to an element, clearing it first if specified.
    Logs errors more specifically.
    """
    try:
        el = wait.until(EC.visibility_of_element_located(locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        if clear_first:
            el.clear()
            # Additional clearing for stubborn fields
            el.send_keys(Keys.COMMAND, "a") # Select all (macOS)
            el.send_keys(Keys.BACKSPACE)
            el.send_keys(Keys.CONTROL, "a") # Select all (Windows/Linux)
            el.send_keys(Keys.DELETE)
        el.send_keys(text)
        logger.debug(f"Typed '{text}' into {locator} successfully.")
        return el
    except (TimeoutException, NoSuchElementException) as e:
        logger.error(f"🔴 Failed to type into {locator}: Element not found or visible. Error: {e}")
        raise # Re-raise to indicate a critical failure
    except Exception as e:
        logger.error(f"🔴 Unexpected error typing into {locator}: {e}")
        raise # Re-raise

def switch_to_tab_by_url(url_substring, timeout=10):
            try:
                driver.switch_to.window(url_substring)
                current_url = driver.current_url
                if url_substring in (current_url or ""):
                    logger.info(f"Switched to tab with URL containing '{url_substring}'.")
            except (NoSuchWindowException, WebDriverException):
                pass

def safe_close_and_switch(target_handle=None):
    """
    Closes the current tab and switches to a specified or the last remaining tab.
    """
    if len(driver.window_handles) <= 1:
        logger.info("Only one tab open, cannot close.")
        return

    current_handle = driver.current_window_handle
    try:
        driver.close()
        logger.info(f"Closed tab {current_handle}")
    except (NoSuchWindowException, WebDriverException) as e:
        logger.warning(f"Error closing tab {current_handle}, might already be closed: {e}")
    finally:
        remaining_handles = driver.window_handles
        if remaining_handles:
            if target_handle and target_handle in remaining_handles:
                driver.switch_to.window(target_handle)
                logger.info(f"Switched to target tab {target_handle}.")
            else:
                driver.switch_to.window(remaining_handles[-1])
                logger.info(f"Switched to last remaining tab {remaining_handles[-1]}.")
        else:
            logger.critical("All tabs closed after closing one. Script might terminate.")
            raise RuntimeError("No browser tabs left to switch to.")

def move_window_to_topright():
    """Moves the current window to the top-right corner of the screen (macOS specific)."""
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    pyautogui.hotkey('ctrl', 'option', 'i') # Move window top right shortcut using magnet app 
    time.sleep(0.2)

def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)

    # zoom out (Cmd + -)
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')

# ==============================================================================
# 🟦 MAIN EXECUTION FLOW
# ==============================================================================

def run_automation():
    init_driver()
    driver.get("https://nmlsconsumeraccess.org/")
    move_window_to_topright()
    zoom_out()
    safe_send_keys((By.ID, "searchText"), "California", clear_first=True)
    click_with_retry((By.ID, "searchButton"))

if __name__ == "__main__":
    run_automation()
