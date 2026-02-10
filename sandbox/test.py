import os, time, logging
from dotenv import load_dotenv
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By

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


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler("linkedin.log", encoding="utf-8"),
              logging.StreamHandler()],
)

load_dotenv()
USERNAME = os.getenv("LINKIN_USERNAME")
PASSWORD = os.getenv("LINKIN_PASSWORD")

driver = webdriver.Chrome()
zoom_out()
move_window_to_topright()

try:
    logging.info("Opening LinkedIn login...")
    driver.get("https://www.linkedin.com/login")

    driver.find_element(By.ID, "username").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    logging.info("Clicked submit")

    time.sleep(5)
    logging.info("Done")
except Exception:
    logging.exception("Unhandled error")  # logs full stack trace
finally:
    driver.quit()
    logging.info("Closed browser")