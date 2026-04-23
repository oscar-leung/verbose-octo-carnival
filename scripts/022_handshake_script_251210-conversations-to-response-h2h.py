"""
Handshake Task Helper — Conversation-to-Response Quality Evaluation (Dec 2025)
───────────────────────────────────────────────────────────────────────────────
Evaluates AI chatbot response quality for Outlier.ai. Compares AI-generated
responses on relevance, accuracy, and helpfulness metrics and submits
head-to-head rankings to the Outlier training data pipeline.

Usage: python 022_handshake_script_251210-conversations-to-response-h2h.py
"""
import os
import random
import time
import sys
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchWindowException, WebDriverException

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
WORKER_EMAIL = "ca45f672d4ec@handshakecommunity.ai"
FILE_PATH = "~/Downloads/image/QA Feedback"
CATEGORIES = ["Instruction Following", "Visual Quality", "AI Generated", "Overall Preference"]
DELAY_THINKING = 3   # Time to wait before voting
DELAY_BETWEEN_VOTES = 5
TASK_ID = "251210-conversations-to-response-h2h"
COOLDOWN = 60 * .5  # Cooldown time between tasks in seconds
WAIT_SEC = 10


# Timers
DURATION_HOURS = 10
TOTAL_SECONDS = DURATION_HOURS * 3600

print(f"🚀 Script Starting... Target Duration: {DURATION_HOURS} Hours")

# ==============================================================================
# 🛠️ HELPER FUNCTIONS
# ==============================================================================

def login_handshake():
    try:
        safe_send_keys((By.ID, "email-address-identifier"), EMAIL)
        click_with_retry((By.XPATH, "//button[normalize-space()='Next']"))
        click_with_retry((By.XPATH, "//a[@class='alternate-login-link link-as-button secondary']"))
        safe_send_keys((By.ID, "password"), PASS)
        click_with_retry((By.XPATH, "//button[@aria-label='submit']"))
        print("✅ Login Successful")
    except Exception:
        print(f"🔴 Login Failed ")
def login_multimango(TASK_ID):
    try:
        # safe_send_keys((By.ID, "identifier-field"), WORKER_EMAIL)
        click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))
        time.sleep(2)
        safe_send_keys((By.ID, "password-field"), PASS)
        click_with_retry((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))
        click_with_retry((By.XPATH, "//a[@data-sidebar='menu-button']"))
        click_with_retry((By.XPATH, f"//a[@href='/tasks/{TASK_ID}']//button"))
        click_with_retry((By.XPATH, "//div[@role='dialog']//button"), optional=True)
        print("✅ Multimango Ready")
    except Exception as e:
        print(f"🔴 Multimango Login Failed ")

def switch_to_tab_by_url(driver, url_substring, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        handles = driver.window_handles
        for h in handles:
            try:
                driver.switch_to.window(h)
                if url_substring in (driver.current_url or ""):
                    return h
            except (NoSuchWindowException, WebDriverException):
                continue
        time.sleep(0.2)
    # fallback: last available tab
    handles = driver.window_handles
    if handles:
        driver.switch_to.window(handles[-1])
        return handles[-1]
    raise RuntimeError("No browser tabs available.")

    raise RuntimeError(f"No tab found with URL containing: {url_substring}")

def click_and_wait_new_tab(click_locator, timeout=10):
    before = set(driver.window_handles)
    click_with_retry(click_locator, timeout=WAIT_SEC, retries=3)
    end = time.time() + timeout
    while time.time() < end:
        after = set(driver.window_handles)
        new = list(after - before)
        if new:
            driver.switch_to.window(new[0])
            return new[0]
        time.sleep(0.2)
    return None

def safe_close_current_tab():
    handles = driver.window_handles
    if len(handles) <= 1:
        return
    try:
        driver.close()
    finally:
        remaining = driver.window_handles
        if remaining:
            driver.switch_to.window(remaining[-1])

def click_with_retry(locator, timeout=WAIT_SEC, retries=3, optional=False):
    last_err = None
    for _ in range(retries):
        try:
            el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            el.click()
            return el
        except Exception as e:
            last_err = e
            time.sleep(0.5)

    if not optional:
        print(f"Failed to click {locator}. Last error: {last_err}")
    return None

def safe_send_keys(locator, text, timeout=WAIT_SEC):
    try:
        el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        el.clear()
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.BACKSPACE)
        el.send_keys(text)
        return el
    except Exception as e:
        print(f"Failed to type into {locator}: {e}")
        return None
    
def tasking():
        switch_to_tab_by_url(driver, "multimango.com")
        for title in CATEGORIES:
            try:
                # Find the container for this category
                block = driver.find_element(
                    By.XPATH,
                    f"//h3[normalize-space()='{title}']/ancestor::div[contains(@class,'border-b')]"
                )
                buttons = block.find_elements(By.TAG_NAME, "button")
                
                if buttons:
                    choice = random.choice(buttons)
                    print(f"   🤔 Thinking for {DELAY_THINKING}s before voting on '{title}'...")
                    time.sleep(DELAY_THINKING)
                    
                    choice.click()
                    print(f"   👉 Clicked: {choice.text}")
                    
                    print(f"   😴 Resting {DELAY_BETWEEN_VOTES}s...")
                    time.sleep(DELAY_BETWEEN_VOTES)
                else:
                    print(f"   ⚠️ No buttons found for {title}")
                    
            except Exception as e:
                print(f"   ❌ Error voting on {title} ")

        # Submit Initial Vote
        try:
            submit = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'bg-green-600')]")))
            submit.click()
            print("✅ Initial Vote Submitted")
        except Exception as e:
            print(f"❌ Initial Submit Failed ")
        driver.close()  

def uploadfile():
        # 🖱️ ATTEMPT UPLOAD CLICK
        if click_with_retry((By.XPATH, "//button[@aria-label='Upload files']"), retries=3):
            time.sleep(2) 
            
            # 🍎 MACOS KEYSTROKES
            try:
                print("      🍎 Triggering macOS File Dialog...")
                os.system("osascript -e 'tell application \"Google Chrome\" to activate'") 
                time.sleep(1)
                pyautogui.hotkey('command', 'shift', 'g')
                time.sleep(1)
                pyautogui.write(FILE_PATH, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')
                time.sleep(0.5)
                pyautogui.press('enter')
                print("      📂 File Selected via Keyboard")
            except Exception as e:
                print(f"      ❌ Keystroke Error ")
        else:
            print("      ⛔ Skipped keystrokes (Upload Button not clickable).")

def wait_click(locator, timeout=15):
    el = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    el.click()
    return el

def wait_type(locator, text, timeout=15, clear=True):
    el = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
    if clear:
        el.clear()
        # sometimes clear() fails visually; this helps:
        el.send_keys(Keys.COMMAND, "a")
        el.send_keys(Keys.BACKSPACE)
    el.send_keys(text)
    return el

def submit_and_wait_next_input(input_locator, submit_locator, value="0", timeout=20):
    # 1) Wait for current input
    current_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(input_locator)
    )

    # 2) Type value
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", current_input)
    current_input.clear()
    current_input.send_keys(value)

    # 3) Click submit
    submit_btn = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(submit_locator)
    )
    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", submit_btn)
    submit_btn.click()

    # 4) Wait until the current input is stale (page moved to next question)
    WebDriverWait(driver, timeout).until(EC.staleness_of(current_input))

    # 5) Wait for next input to appear
    next_input = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located(input_locator)
    )
    return next_input

def fill_handshake_questions(num_questions=5, value="0"):
    input_locator = (By.XPATH, "//div[contains(@class,'flex') and contains(@class,'flex-col')]//input")
    submit_locator = (By.XPATH, "//button[@aria-label='Submit']")

    # First question: just wait for it, then loop submit transitions
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located(input_locator))

    for _ in range(num_questions - 1):
        submit_and_wait_next_input(input_locator, submit_locator, value=value, timeout=20)

    # Last one: submit, but you may not get another input—so don’t wait for next input
    wait_type(input_locator, value, timeout=20)
    wait_click(submit_locator, timeout=20)

def handshake_complete_task():
    print("   🟦 Switching to Handshake...")
    switch_to_tab_by_url(driver, "ai.joinhandshake.com")
    click_with_retry((By.XPATH, "//button[normalize-space()='Other']"))
    click_with_retry((By.XPATH, "//button[@aria-label='Submit']"))
    uploadfile()
    time.sleep(2)
    driver.find_element(By.XPATH, "//textarea").send_keys('251210-conversations-to-response-h2h')
    time.sleep(2)
    click_with_retry((By.XPATH, "//button[@aria-label='Submit']"))

    # Fill inputs
    print("   📝 Filling Inputs...")
    fill_handshake_questions(num_questions=5, value="0")


    # Finalize & Restart
    click_with_retry((By.XPATH, "//button[normalize-space()='Submit task']"))
    click_with_retry((By.XPATH, "//button[normalize-space()='Confirm time']"), optional=True)
    click_with_retry((By.XPATH, "//button[normalize-space()='Next task']"))


    click_with_retry((By.XPATH, "//button[normalize-space()='Open Multimango']")) # Open Multimango in a new tab very important, this must open to start the timer
    driver.switch_to.window(driver.window_handles[-1])
    click_with_retry((By.XPATH, "//a[@data-sidebar='menu-button']"))
    click_with_retry((By.XPATH, f"//a[@href='/tasks/{TASK_ID}']//button"))
    time.sleep(2)
    click_with_retry((By.XPATH, "//div[@role='dialog']/button"))
    time.sleep(2)
    print(f"   ✅ Cycle {run_count} Complete. Cooldown: {COOLDOWN}s")
    
    # Wait for the cooldown
    time.sleep(COOLDOWN)
    # click_with_retry((By.XPATH, f"//button[normalize-space()='Continue']"))


# ==============================================================================
# 🟦 BLOCK 1: Handshake Flow
# ==============================================================================
driver = webdriver.Chrome()
wait = WebDriverWait(driver, WAIT_SEC)
driver.get("https://ai.joinhandshake.com/fellow/projects")
login_handshake()
click_with_retry((By.XPATH, "//p[normalize-space()='Project Hedgehog']/ancestor::section//button[normalize-space()='Start task']"))
click_with_retry((By.XPATH, "//button[normalize-space()='Open Multimango']")) # Open Multimango in a new tab

# ==============================================================================
# 🟦 BLOCK 2: MULTIMANGO Flow
# ==============================================================================
print("\n🟦 BLOCK 3: Logging into Multimango...")
driver.switch_to.window(driver.window_handles[-1])
login_multimango(TASK_ID)

# ==============================================================================
# 🟦 BLOCK 4: 251211-video-scene-expansion tasking
# ==============================================================================
print("\n🟦 BLOCK 4: Tasking 251210-conversations-to-response-h2h")

# 📊 METRICS INITIALIZATION
start_time = time.time()
end_time = start_time + TOTAL_SECONDS
run_count = 1
success_count = 0
fail_count = 0

while time.time() < end_time:
    # ⏱️ TIMING CALCULATION
    current_time = time.time()
    elapsed_seconds = int(current_time - start_time)
    remaining_seconds = int(end_time - current_time)
    
    # Format HH:MM:SS
    e_str = time.strftime('%H:%M:%S', time.gmtime(elapsed_seconds))
    r_str = time.strftime('%H:%M:%S', time.gmtime(remaining_seconds))
    
    print(f"\n{'='*60}")
    print(f"🔄 CYCLE {run_count} | ✅ Success: {success_count} | ❌ Failed: {fail_count}")
    print(f"⏱️  Elapsed: {e_str} | ⏳ Remaining: {r_str}")
    print(f"{'='*60}")
    
    task_success = False # Reset flag for this cycle

    try:
       tasking()
       task_success = True
       success_count += 1
    except Exception as e:
        fail_count += 1
        print(f"   ❌ Tasking skipped or failed ")

    total_elapsed = int(time.time() - start_time)
    total_time_str = time.strftime('%H:%M:%S', time.gmtime(total_elapsed))
    print(f'Current run count {run_count} took {total_elapsed} seconds time so far or {total_time_str}')
    run_count += 1
    handshake_complete_task()

# ==============================================================================
# 🟦 BLOCK 5: Printing Data
# ==============================================================================

print("\n" + "#"*60)
print("             🏁 SCRIPT EXECUTION COMPLETE 🏁")
print("#"*60)
print(f"📅 Total Duration : {total_time_str}")
print(f"🔄 Total Cycles   : {run_count - 1}")
print(f"✅ Successful     : {success_count}")
print(f"❌ Failed         : {fail_count}")
print(f"📈 Success Rate   : {round((success_count / (run_count - 1) * 100), 2) if run_count > 1 else 0}%")
print("#"*60)