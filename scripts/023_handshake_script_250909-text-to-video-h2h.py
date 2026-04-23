"""
Handshake Task Helper — Text-to-Video Pipeline (Sep 2025, Alternate Flow)
──────────────────────────────────────────────────────────────────────────
Third variant of the text-to-video human evaluation submission pipeline.
Handles a different task batch configuration for the Outlier Sep 2025
text-to-video evaluation campaign.

Usage: python 023_handshake_script_250909-text-to-video-h2h.py
"""
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
import os
from dotenv import load_dotenv
load_dotenv()
username = os.getenv("handshake_email")
password = os.getenv("handshake_password")
EMAIL = username
PASS = password
WORKER_EMAIL = "ca45f672d4ec@handshakecommunity.ai" # Kept for reference, not used in current login
FILE_PATH = os.path.expanduser("~/Downloads/image/QA Feedback") # Using expanduser for ~
CATEGORIES = ["Instruction Following", "Visual Quality", "Overall Choice"]
DELAY_THINKING = 3   # Time to wait before voting
DELAY_BETWEEN_VOTES = 5
TASK_ID = "250909-text-to-video-h2h"
COOLDOWN = 60 * .5  # Cooldown time between tasks in seconds
WAIT_SEC = 15 # Increased default wait slightly for more robustness


# Timers
DURATION_HOURS = 10
TOTAL_SECONDS = DURATION_HOURS * 3600

# ==============================================================================
# 📝 LOGGING SETUP (New)
# ==============================================================================
logging.basicConfig(
    level=logging.INFO, # Set to logging.DEBUG for more verbose output
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"), # Log to a file
        logging.StreamHandler(sys.stdout)       # Also print to console
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

# Global WebDriver and Wait (less ideal for large projects, but common for scripts)
driver = None
wait = None

# Store window handles for easier switching
handshake_window_handle = None
multimango_window_handle = None

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
    """
    Switches to a tab whose URL contains the given substring.
    Updates global window handles if necessary.
    """
    global handshake_window_handle, multimango_window_handle
    original_handle = driver.current_window_handle
    end = time.time() + timeout
    while time.time() < end:
        handles = driver.window_handles
        for h in handles:
            try:
                driver.switch_to.window(h)
                current_url = driver.current_url
                if url_substring in (current_url or ""):
                    logger.info(f"Switched to tab with URL containing '{url_substring}'.")
                    if "handshake.com" in url_substring:
                        handshake_window_handle = h
                    elif "multimango.com" in url_substring:
                        multimango_window_handle = h
                    return h
            except (NoSuchWindowException, WebDriverException):
                continue
        time.sleep(0.5) # Wait a bit before retrying to find the tab

    logger.warning(f"Could not find tab with URL containing '{url_substring}' within {timeout}s. Switching to last available tab.")
    # Fallback: if not found, switch back to original or last active
    if original_handle in driver.window_handles:
        driver.switch_to.window(original_handle)
    elif driver.window_handles:
        driver.switch_to.window(driver.window_handles[-1])
    else:
        logger.critical("No browser tabs available after trying to switch!")
        raise RuntimeError("No browser tabs available.")
    return driver.current_window_handle # Return the handle of the tab we ended up on

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

# ==============================================================================
# 🚀 MAIN AUTOMATION LOGIC
# ==============================================================================

def login_handshake():
    """Performs the login flow for Handshake."""
    global handshake_window_handle
    time.sleep(5) # Give time for tab switch
    zoom_out() # Ensure UI elements are visible
    try:
        driver.get("https://ai.joinhandshake.com/fellow/projects")
        handshake_window_handle = driver.current_window_handle
        logger.info("Attempting Handshake login...")

        safe_send_keys((By.ID, "email-address-identifier"), EMAIL)
        click_with_retry((By.XPATH, "//button[normalize-space()='Next']"))
        # Using a more robust locator for "Log in with password instead" or similar
        click_with_retry((By.XPATH, "//a[contains(@class, 'alternate-login-link') and contains(@class, 'link-as-button')] | //a[contains(text(), 'password')]"), optional=True)
        safe_send_keys((By.ID, "password"), PASS)
        click_with_retry((By.XPATH, "//button[@aria-label='submit' or normalize-space()='Log in']"))
        logger.info("✅ Handshake Login Successful")
    except Exception as e:
        logger.error(f"🔴 Handshake Login Failed: {e}", exc_info=True)
        raise # Re-raise to stop if login fails

def login_multimango():
    """Performs the login flow for Multimango. Assumes we are on the Multimango tab."""
    global multimango_window_handle
    switch_to_tab_by_url("multimango.com")
    time.sleep(5) # Give time for tab switch
    zoom_out() # Ensure UI elements are visible

    try:
        multimango_window_handle = driver.current_window_handle
        logger.info("Attempting Multimango login...")

        # Based on the original code, it seems to expect to click a button immediately
        # without filling email, or email is pre-filled.
        # If email input is needed, uncomment and use WORKER_EMAIL:
        # safe_send_keys((By.ID, "identifier-field"), WORKER_EMAIL)

        # This button click might be "Continue", "Next", or "Log in with password" if email is pre-filled
        click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary' or normalize-space()='Continue']"), optional=True)
        time.sleep(1) # Small pause for UI transition
        safe_send_keys((By.ID, "password-field"), PASS)
        click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary' or normalize-space()='Log in']"))

        logger.info("✅ Multimango Ready for Tasking")
    except Exception as e:
        logger.error(f"🔴 Multimango Login/Task Setup Failed: {e}", exc_info=True)
        raise

def zoom_out():
    os.system('osascript -e \'tell application "Google Chrome" to activate\'')
    time.sleep(0.2)

    # zoom out (Cmd + -)
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')
    pyautogui.hotkey('command', '-')

def nav_to_task():
        # Navigate to the specific task
        switch_to_tab_by_url("multimango.com")
        click_with_retry((By.XPATH, "//a[@data-sidebar='menu-button']")) # Open sidebar/menu
        click_with_retry((By.XPATH, f"//a[@href='/tasks/{TASK_ID}']//button")) # Click the task button
        time.sleep(30)
        click_with_retry((By.XPATH, "//div[@role='dialog']//button")) # Close any initial dialog

def multimango_tasking_cycle():
    """Performs a single tasking cycle on Multimango."""
    logger.info("Starting Multimango tasking...")
    # Ensure we are on the Multimango tab before starting
    switch_to_tab_by_url("multimango.com")
    click_with_retry((By.XPATH, "//button[@title='Dismiss for this page']"), optional=True) # Dismiss any popups if present

    for title in CATEGORIES:
        try:
            # Find the container for this category
            block_locator = (By.XPATH,
                             f"//h3[normalize-space()='{title}']/ancestor::div[contains(@class,'border-b') or contains(@class,'bg-gray-50')]") # More general block
            block = wait.until(EC.presence_of_element_located(block_locator))
            buttons = block.find_elements(By.TAG_NAME, "button")

            if buttons:
                choice = random.choice(buttons)
                logger.info(f"   🤔 Thinking for {DELAY_THINKING}s before voting on '{title}'...")
                time.sleep(DELAY_THINKING)

                # Ensure button is visible and clickable
                wait.until(EC.element_to_be_clickable(choice))
                choice.click()
                logger.info(f"   👉 Clicked: {choice.text} for category '{title}'")

                logger.info(f"   😴 Resting {DELAY_BETWEEN_VOTES}s...")
                time.sleep(DELAY_BETWEEN_VOTES)
            else:
                logger.warning(f"   ⚠️ No buttons found for category '{title}'. Skipping.")

        except TimeoutException:
            logger.error(f"   ❌ Timeout waiting for block for '{title}'. Skipping this category.")
        except Exception as e:
            logger.error(f"   ❌ Error voting on category '{title}': {e}", exc_info=True)

    # Submit Initial Vote
    try:
        submit = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'bg-green-600')]")))
        submit.click()
        logger.info("✅ Multimango Vote Submitted")
    except Exception as e:
        logger.error(f"❌ Multimango Submit Failed: {e}", exc_info=True)
        raise # Re-raise to indicate a failure in the tasking

    # Close Multimango tab after submission
    # Use global handle to switch back to Handshake more reliably
    safe_close_and_switch(handshake_window_handle)
    logger.info("Multimango tab closed.")

def upload_file_to_handshake():
    """Handles the file upload process for Handshake."""
    logger.info("   📂 Attempting file upload...")
    if click_with_retry((By.XPATH, "//button[@aria-label='Upload files'] | //button[normalize-space()='Upload files']"), retries=3):
        time.sleep(1) # Give a moment for the dialog to appear

        # Check if the file input element is directly accessible (more robust)
        try:
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(FILE_PATH)
            logger.info(f"      📁 File '{FILE_PATH}' selected via Selenium send_keys.")
            return True
        except NoSuchElementException:
            logger.info("      Falling back to pyautogui for file upload (input type=file not found).")
            # Fallback to pyautogui for native file dialogs (macOS specific)
            try:
                # Ensure Chrome is frontmost. This can sometimes be flaky.
                os.system("osascript -e 'tell application \"Google Chrome\" to activate'")
                time.sleep(1) # Give it time to activate

                pyautogui.hotkey('command', 'shift', 'g') # Go to folder
                time.sleep(0.5)
                pyautogui.write(FILE_PATH, interval=0.02) # Slower typing for reliability
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)
                pyautogui.press('enter') # Confirm file selection
                logger.info("      🍎 File Selected via macOS Keystrokes (PyAutoGUI)")
                return True
            except Exception as e:
                logger.error(f"      ❌ PyAutoGUI Keystroke Error: {e}", exc_info=True)
                return False
    else:
        logger.warning("      ⛔ Skipped file upload (Upload Button not clickable).")
        return False

def submit_and_wait_next_input(input_locator, submit_locator, value="0", timeout=WAIT_SEC):
    """
    Fills an input, clicks submit, and waits for the input element to become stale
    and the next input to appear, indicating a page transition.
    """
    try:
        current_input = wait.until(EC.visibility_of_element_located(input_locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", current_input)
        current_input.clear()
        current_input.send_keys(value)
        logger.debug(f"Inputted '{value}' into {input_locator}")

        submit_btn = wait.until(EC.element_to_be_clickable(submit_locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
        submit_btn.click()
        logger.debug(f"Clicked submit button {submit_locator}")

        # Wait until the current input is stale, meaning the page has moved on
        wait.until(EC.staleness_of(current_input))
        logger.debug("Previous input became stale. Waiting for next input...")

        # Wait for the next input to appear
        next_input = wait.until(EC.visibility_of_element_located(input_locator))
        logger.debug("Next input appeared.")
        return next_input
    except TimeoutException:
        logger.warning(f"Timeout during submit_and_wait_next_input for {input_locator}. May be the last question.")
        return None # Indicate that a next input wasn't necessarily found
    except Exception as e:
        logger.error(f"Error during submit_and_wait_next_input for {input_locator}: {e}", exc_info=True)
        raise

def fill_handshake_questions(num_questions=5, value="0"):
    """Fills a series of input questions on Handshake."""
    input_locator = (By.XPATH, "//div[contains(@class,'flex') and contains(@class,'flex-col')]//input")
    submit_locator = (By.XPATH, "//button[@aria-label='Submit' or normalize-space()='Submit']")

    logger.info(f"   📝 Filling {num_questions} Handshake inputs with value '{value}'...")

    try:
        # First question: just wait for it to appear
        wait.until(EC.visibility_of_element_located(input_locator))

        for i in range(num_questions - 1):
            logger.debug(f"    - Filling question {i+1}...")
            submit_and_wait_next_input(input_locator, submit_locator, value=value)
            time.sleep(0.5) # Short pause between questions

        # Last one: submit, but don't expect a new input to appear
        logger.debug(f"    - Filling final question {num_questions}...")
        safe_send_keys(input_locator, value) # Use safe_send_keys for the last one
        click_with_retry(submit_locator)
        logger.info("   ✅ All Handshake questions filled and submitted.")
    except Exception as e:
        logger.error(f"   ❌ Error filling Handshake questions: {e}", exc_info=True)
        raise

def handshake_complete_task():
    """Completes the Handshake task and prepares for the next cycle."""
    logger.info("   🟦 Switching to Handshake to complete task...")
    switch_to_tab_by_url("ai.joinhandshake.com") # Ensure we are on Handshake tab

    try:
        click_with_retry((By.XPATH, f"//button[normalize-space()='250909-text-to-video-h2h: ~25 minutes'] | //label[normalize-space()='250909-text-to-video-h2h: ~25 minutes']/parent::div//button")) # More robust locator
        click_with_retry((By.XPATH, "//button[@aria-label='Submit' or normalize-space()='Submit']"))
        upload_file_to_handshake()
        time.sleep(1) # Give time for upload UI to settle
        safe_send_keys((By.XPATH, "//textarea[@aria-label='Description' or @placeholder='Description'] | //textarea"), TASK_ID, clear_first=False)
        time.sleep(1)
        click_with_retry((By.XPATH, "//button[@aria-label='Submit' or normalize-space()='Submit']"))

        fill_handshake_questions(num_questions=5, value="0")

        # Finalize & Restart
        click_with_retry((By.XPATH, "//button[normalize-space()='Submit task']"))
        click_with_retry((By.XPATH, "//button[normalize-space()='Confirm time']"), optional=True) # This might not always appear
        click_with_retry((By.XPATH, "//button[normalize-space()='Next task']"))

        logger.info("   ✅ Handshake task completed and new task initiated.")

        # Open Multimango for the next cycle - this is critical for loop continuation
        click_with_retry((By.XPATH, "//button[normalize-space()='Open Multimango']"))
    
        logger.info(f"   ✅ Cycle Complete. Cooldown: {COOLDOWN}s")
        time.sleep(COOLDOWN) # Apply cooldown
        return True # Indicate success
    except Exception as e:
        logger.error(f"🔴 Handshake task completion failed: {e}", exc_info=True)
        return False # Indicate failure

# ==============================================================================
# 🟦 MAIN EXECUTION FLOW
# ==============================================================================

def run_automation():
    global run_count, success_count, fail_count, start_time

    init_driver()

    try:
        # 🟦 BLOCK 1: Handshake Initial Setup
        login_handshake()
        # Navigate to the project and open Multimango
        click_with_retry((By.XPATH, "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']"))
        click_with_retry((By.XPATH, "//button[normalize-space()='Open Multimango']")) # This opens Multimango in a new tab

        # 🟦 BLOCK 2: MULTIMANGO Initial Login
        
        login_multimango()

        # 📊 METRICS INITIALIZATION
        start_time = time.time()
        end_time = start_time + TOTAL_SECONDS
        run_count = 1
        success_count = 0
        fail_count = 0

        # 🟦 BLOCK 4: Main Tasking Loop
        while time.time() < end_time:
            current_time = time.time()
            elapsed_seconds = int(current_time - start_time)
            remaining_seconds = int(end_time - current_time)

            e_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))
            r_str = time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))

            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 CYCLE {run_count} | ✅ Success: {success_count} | ❌ Failed: {fail_count}")
            logger.info(f"⏱️  Elapsed: {e_str} | ⏳ Remaining: {r_str}")
            logger.info(f"{'='*60}")

            cycle_start_time = time.time()
            task_success = False

            try:
                nav_to_task()
                multimango_tasking_cycle()
                task_success = True
                success_count += 1
            except Exception as e:
                fail_count += 1
                logger.error(f"🔴 Multimango tasking failed in cycle {run_count}: {e}", exc_info=True)
                # Attempt to close the multimango tab if it's still open and switch back to handshake
                if multimango_window_handle and multimango_window_handle in driver.window_handles:
                    try:
                        driver.switch_to.window(multimango_window_handle)
                        safe_close_and_switch(handshake_window_handle)
                    except Exception as switch_e:
                        logger.warning(f"Could not safely close Multimango tab after failure: {switch_e}")
                # If Multimango failed, Handshake completion will likely also fail, but we try.

            total_elapsed_cycle = int(time.time() - cycle_start_time)
            logger.info(f'Current cycle {run_count} took {total_elapsed_cycle} seconds.')

            # Always attempt Handshake completion, even if Multimango failed,
            # to keep the overall process moving if possible.
            try:
                if handshake_complete_task():
                    logger.info("Handshake completion successful.")
                else:
                    logger.error("Handshake completion failed.")
                    fail_count += 1 # Count as a full cycle failure if Handshake fails too
            except Exception as e:
                fail_count += 1
                logger.error(f"🔴 Handshake task completion failed in cycle {run_count}: {e}", exc_info=True)
                # If Handshake fails here, the state might be broken, might need to restart browser.
                # For now, we'll just log and continue the loop, hoping for recovery.

            run_count += 1
            # The cooldown is now handled inside handshake_complete_task after successful completion

    except Exception as main_e:
        logger.critical(f"Unhandled critical error in main automation loop: {main_e}", exc_info=True)
    finally:
        # 🟦 BLOCK 5: Printing Data and Cleanup
        total_elapsed_final = int(time.time() - start_time)
        total_time_str = time.strftime('%H:%M:%S', time.gmtime(total_elapsed_final))

        logger.info("\n" + "#"*60)
        logger.info("             🏁 SCRIPT EXECUTION COMPLETE 🏁")
        logger.info("#"*60)
        logger.info(f"📅 Total Duration : {total_time_str}")
        logger.info(f"🔄 Total Cycles   : {run_count - 1}")
        logger.info(f"✅ Successful     : {success_count}")
        logger.info(f"❌ Failed         : {fail_count}")
        logger.info(f"📈 Success Rate   : {round((success_count / (run_count - 1) * 100), 2) if run_count > 1 else 0}%")
        logger.info("#"*60)

        if driver:
            logger.info("Closing WebDriver.")
            driver.quit()

if __name__ == "__main__":
    run_automation()