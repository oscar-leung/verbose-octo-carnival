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
from collections import defaultdict

# =======================
# LOGGING SETUP
# =======================

LOG_DIR = "brand_survey_logs"
os.makedirs(LOG_DIR, exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(LOG_DIR, f"survey_run_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logging.info("🚀 Survey automation started")
logging.info(f"📝 Log file: {log_file}")


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

def clickWebElement(xpath, timeout=2):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});", element
        )
        driver.execute_script("arguments[0].click();", element)

        logging.info(f"✅ Clicked element: {xpath}")
        return True
    except TimeoutException:
        logging.debug(f"⏳ Timeout waiting for: {xpath}")
    except Exception as e:
        logging.debug(f"❌ Click failed: {xpath} | {e}")
    return False

def element_exists(xpath):
    try:
        exists = len(driver.find_elements(By.XPATH, xpath)) > 0
        logging.debug(f"🔍 Element exists [{exists}]: {xpath}")
        return exists
    except Exception as e:
        logging.debug(f"⚠️ element_exists error: {xpath} | {e}")
        return False

def click_continue(sleep=1):
    continue_xpaths = [
        "//input[@id='btn_continue']",
        "//input[@id='ctl00_Content_btnContinue']",
        "//div[@id='oc_in4']",
        "//input[@type='submit' and contains(@value,'Continue')]",
        "//button[normalize-space()='Continue']",
        "//button[@title='NEXT']",
        "//button[normalize-space()='']",
        "//button[normalize-space()='Accept']",
        "//a[@id='acceptAndTakeSurveyLink1']",
        "//a[@class='btn primary take-survey-btn']",
        "//a[@data-testid='common-surveyfooter-button-advance']"
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

def is_samplicio_survey():
    try:
        url = driver.current_url.lower()
        page = driver.page_source.lower()

        return (
            "samplicio" in url
            or "surveyrouter" in url
            or "js-question-options" in page
            or "gtm-agree-button" in page
        )
    except:
        return False

def skip_samplicio_survey():
    logging.warning("⛔ Samplicio survey detected — skipping")

    try:
        clickWebElement("//button[@id='gtm-agree-button']")
        close_current_tab()
        time.sleep(2)
    except Exception as e:
        logging.error(f"Failed to skip Samplicio: {e}")


# help fns for ssisurveys


def fill_numeric_inputs(value="1"):
    inputs = driver.find_elements(
        By.XPATH,
        "//input[@type='number' and contains(@class,'imperium-numeric-question')]"
    )

    for inp in inputs:
        try:
            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", inp
            )
            inp.clear()
            inp.send_keys(value)
        except:
            pass

def click_random_radio():
    try:
        options = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'answers')]//label"
        )
        if options:
            driver.execute_script(
                "arguments[0].click();",
                random.choice(options)
            )
            return True
    except:
        pass
    return False

def answer_radio_table():
    rows = driver.find_elements(
        By.XPATH,
        "//tbody//tr[contains(@class,'row-elements')]"
    )

    if not rows:
        return False

    for row in rows:
        try:
            labels = row.find_elements(By.XPATH, ".//label")
            if labels:
                driver.execute_script(
                    "arguments[0].click();",
                    random.choice(labels)
                )
        except:
            pass

    return True

def rate(min_val=0, max_val=10):
    labels = driver.find_elements(
        By.XPATH,
        "//table//tr[contains(@class,'row-elements')]//label"
    )

    if not labels:
        return False

    driver.execute_script(
        "arguments[0].click();",
        random.choice(labels[min_val:max_val + 1])
    )
    return True
    

# help fns for itrafficcenter surveys

def itraffic_handle_page() -> bool:
    """Try iTraffic actions in priority order. Return True if we did something."""
    acted = False

    # --- screening defaults (simple, deterministic) ---
    if element_exists("//div[@id='screening__gender']"):
        acted |= clickWebElement("//label[@for='screening__gender-1']")

    if element_exists("//input[@id='screening__zip_code']"):
        try:
            z = driver.find_element(By.XPATH, "//input[@id='screening__zip_code']")
            z.clear()
            z.send_keys("94502")
            logging.info("✅ Entered zipcode 94502")
            acted = True
        except:
            pass

    if element_exists("//div[@id='screening__race']"):
        acted |= clickWebElement("//input[@id='screening__race-3']")

    if element_exists("//div[@id='screening__education']"):
        acted |= clickWebElement("//input[@id='screening__education-8']")

    if element_exists("//div[@id='screening__hispanic']"):
        acted |= clickWebElement("//input[@id='screening__hispanic-1']")

    if element_exists("//div[@id='screening__income']"):
        acted |= clickWebElement("//input[@id='screening__income-18']")

    if element_exists("//input[@id='screening__age']"):
        try:
            a = driver.find_element(By.XPATH, "//input[@id='screening__age']")
            a.clear()
            a.send_keys("30")
            logging.info("✅ Entered age 30")
            acted = True
        except:
            pass

    if acted:
        return True

    # --- specific “always choose” cases ---
    # Acceptance/consent yes (by id you used earlier)
    try:
        el = driver.find_element(By.XPATH, "//input[@id='acceptance-input-1' and @type='radio']")
        driver.execute_script("arguments[0].click();", el)
        logging.info("✅ Acceptance YES selected")
        return True
    except:
        pass

    # Brokerage account YES (generic yes-label match)
    if itraffic_radio_select_yes():
        logging.info("✅ Selected YES radio")
        return True

    # Employed full-time (specific checkbox label match)
    if itraffic_select_employed_full_time():
        logging.info("✅ Selected employed full-time")
        return True

    # MaxDiff (valid: most/least different)
    if itraffic_maxdiff_random_valid():
        logging.info("✅ MaxDiff valid selection made")
        return True

    # --- open-ended text (choose based on prompt text) ---
    try:
        prompt = driver.find_element(By.XPATH, "//div[contains(@class,'form-group') and contains(@class,'required')]//label[@for='survey__response']").text.lower()
        if "perfect day" in prompt:
            return ai_fill_perfect_day()
        if "favorite song" in prompt:
            return ai_fill_favorite_song()
    except:
        pass

    # --- general required pickers (fallbacks) ---
    if itraffic_checkbox_pick_one_required():
        logging.info("✅ Picked checkbox in required form-group")
        return True

    if itraffic_radio_pick_one_required():
        logging.info("✅ Picked radio in required form-group")
        return True

    # any generic confirmation checkbox (like MaterialPlus or similar)
    if clickWebElement("//label[@class='checkbox']"):
        logging.info("✅ Confirmation checkbox clicked")
        return True

    return False

def itraffic_checkbox_pick_one_required() -> bool:
    try:
        clicked = False
        groups = driver.find_elements(By.XPATH, "//div[contains(@class,'form-group') and contains(@class,'required')]")
        for g in groups:
            opts = g.find_elements(By.XPATH,
                ".//label[not(contains(translate(normalize-space(.),"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'none of the above'))]"
                "//input[@type='checkbox']"
            )
            if opts:
                driver.execute_script("arguments[0].click();", random.choice(opts))
                clicked = True
        return clicked
    except:
        return False

def itraffic_radio_pick_one_required() -> bool:
    try:
        clicked = False
        groups = driver.find_elements(By.XPATH, "//div[contains(@class,'form-group') and contains(@class,'required')]")
        for g in groups:
            opts = g.find_elements(By.XPATH,
                ".//label[not(contains(translate(normalize-space(.),"
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'none of the above'))]"
                "//input[@type='radio']"
            )
            if opts:
                driver.execute_script("arguments[0].click();", random.choice(opts))
                clicked = True
        return clicked
    except:
        return False
    
def ai_fill_perfect_day() -> bool:
    try:
        xp = "//textarea[@id='survey__response' and @required]"
        el = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, xp)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        driver.execute_script("arguments[0].click();", el)

        answer = (
            "My perfect day starts with a slow morning—coffee and a good breakfast with my partner and close friends. "
            "We’d spend the day outdoors (a hike or a beach walk), grab lunch at a local spot, and take time to talk and laugh. "
            "In the evening we’d cook dinner together, play a board game or watch a movie, and end the night relaxing and grateful."
        )[:512]

        el.clear()
        el.send_keys(answer)
        logging.info("✅ Filled 'perfect day' textarea")
        return True
    except Exception as e:
        logging.debug(f"❌ ai_fill_perfect_day failed | {e}")
        return False

def ai_fill_favorite_song() -> bool:
    try:
        el = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//textarea[@id='survey__response' and @required]"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
        driver.execute_script("arguments[0].click();", el)

        answer = (
            "My favorite song is “Here Comes the Sun” by The Beatles. "
            "It’s my favorite because it always puts me in a better mood—it's simple, warm, and hopeful, "
            "and it reminds me that rough patches don’t last forever."
        )[:512]

        el.clear()
        el.send_keys(answer)
        logging.info("✅ Filled favorite song textarea")
        return True
    except Exception as e:
        logging.debug(f"❌ ai_fill_favorite_song failed | {e}")
        return False

def itraffic_radio_select_yes() -> bool:
    try:
        yes = driver.find_elements(
            By.XPATH,
            "//div[contains(@class,'form-group') and contains(@class,'required')]"
            "//label[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'yes')]"
            "//input[@type='radio']"
        )
        if not yes:
            return False
        driver.execute_script("arguments[0].click();", yes[0])
        return True
    except:
        return False
    
def itraffic_select_employed_full_time() -> bool:
    try:
        el = driver.find_element(
            By.XPATH,
            "//div[contains(@class,'form-group') and contains(@class,'required')]"
            "//label[contains(translate(normalize-space(.),"
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'employed full-time')]"
            "//input[@type='checkbox']"
        )
        driver.execute_script("arguments[0].click();", el)
        return True
    except:
        return False

def itraffic_maxdiff_random_valid() -> bool:
    try:
        rows = driver.find_elements(By.XPATH, "//table[@id='max-diff-selection']//tbody/tr")
        if len(rows) < 2:
            return False

        # clear previous checks (if any)
        for cb in driver.find_elements(By.XPATH, "//table[@id='max-diff-selection']//input[@type='checkbox']"):
            try:
                if cb.is_selected():
                    driver.execute_script("arguments[0].click();", cb)
            except:
                pass

        # pick 2 DIFFERENT rows so most != least
        least_row, most_row = random.sample(rows, 2)

        least_cb = least_row.find_element(By.XPATH, ".//input[contains(@class,'least')]")
        most_cb  = most_row.find_element(By.XPATH, ".//input[contains(@class,'most')]")

        driver.execute_script("arguments[0].click();", least_cb)
        driver.execute_script("arguments[0].click();", most_cb)
        return True
    except:
        return False

# cmix helper fns

def cmix_fill_info():
    if element_exists("//div[@normalize-space()='What is your gender?']"):
        clickWebElement("//select")
        clickWebElement("//*[@id='60346631']/option[2]")


# encuesta fns surveys

def encuesta_gender():
    if element_exists("//label[@for='input-75']"):
        clickWebElement("//label[@for='input-75']")

def encuesta_age():
    if element_exists("//label[@for='input-96']"):
        clickWebElement("//label[@for='input-96']")

def encuesta_residence():
    if element_exists("//label[@for='input-125']"):
        clickWebElement("//label[@for='input-125']")

def encuesta_race():
    if element_exists("//label[@for='input-486']"):
        clickWebElement("//label[@for='input-486']")

def encuresata_radio_pick_one_required(timeout=1, avoid_none_of_above=True) -> bool:
    """
    Encues/EE (Vuetify) required radio questions:
    - required questions have: <span class="required">*</span>
    - radio inputs look like: <input type="radio" id="input-336" ...>
    We click the LABEL (label[for='input-336']) using your clickWebElement().
    """
    try:
        clicked_any = False

        # Required question "cards"
        required_regions = driver.find_elements(
            By.XPATH, "//div[@role='region' and .//span[contains(@class,'required')]]"
        )

        for region in required_regions:

            # scope clicks to the question-section container (more stable)
            try:
                qs_id = region.find_element(
                    By.XPATH, "./ancestor::div[starts-with(@id,'question-section-')][1]"
                ).get_attribute("id")
            except:
                qs_id = None

            # map input-id -> label text
            label_map = {}
            for lab in region.find_elements(By.XPATH, ".//label[@for]"):
                label_map[lab.get_attribute("for")] = (lab.text or "").strip().lower()

            candidates = []
            for inp in region.find_elements(By.XPATH, ".//input[@type='radio' and @id]"):
                if inp.get_attribute("aria-checked") == "true":
                    continue

                iid = inp.get_attribute("id")
                txt = label_map.get(iid, "")

                if avoid_none_of_above and "none of the above" in txt:
                    continue

                candidates.append(iid)

            if not candidates:
                continue

            chosen_id = random.choice(candidates)

            # click the label (usually the clickable part in Vuetify)
            if qs_id:
                xp = f"//div[@id='{qs_id}']//label[@for='{chosen_id}']"
            else:
                xp = f"//label[@for='{chosen_id}']"

            if clickWebElement(xp, timeout=timeout):
                clicked_any = True

        return clicked_any
    except Exception as e:
        logging.debug(f"encuresata_radio_pick_one_required failed: {e}")
        return False


# innovationsurveys2 helper fns
# def innovationsurveys2_fill_info():


# focusvision helper fns

# Load variables from .env
load_dotenv()
username = os.getenv("branded_email")
password = os.getenv("branded_password")

# Initialize variables
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)

driver.get("https://surveys.gobranded.com/users/login/")
zoom_out()
move_window_to_topright()

# login
logging.info("🔐 Navigating to login page")
driver.get("https://surveys.gobranded.com/users/login/")
logging.info("🔑 Attempting login")
driver.find_element(By.ID, "UserEmail").send_keys(username)
driver.find_element(By.ID, "UserPassword").send_keys(password)
clickWebElement("//button[@id='_evidon-accept-button']")
driver.find_element(By.XPATH, '//input[@value="Sign in"]').click()
logging.info("✅ Login submitted")


# main loop

no_progress_count = 0
MAX_NO_PROGRESS = 5

logging.info("🔄 Entering main survey loop")

while True:
    acted = False
    url_before = driver.current_url.lower()

    # --- branded dashboard to surveys ---
    if element_exists("//div[@class='survey-card-action text-center']"):
        clickWebElement("//div[@class='survey-card-action text-center']//a")
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[-1])
        if element_exists("//a[@id='btn-continue']"):
            clickWebElement("//a[@id='btn-continue']")
            time.sleep(10)
            acted = True

    if element_exists("//a[@id='takesurveybtn']"):
        clickWebElement("//a[@id='takesurveybtn']")
        time.sleep(1)
        acted = True

    # --- exit/skip conditions ---
    if is_samplicio_survey():
        skip_samplicio_survey()
        driver.refresh()
        time.sleep(5)
        continue

    if element_exists("//div[@class='modal-body']//a"):
        clickWebElement("//div[@class='modal-body']//a")
        close_current_tab()
        time.sleep(1)
        driver.refresh()
        time.sleep(5)
        continue

    # --- iTraffic handler (all your survey logic in one place) ---
    if itraffic_handle_page():
        acted = True
        

    # --- always try continue last ---
    if click_continue():
        acted = True

    url_after = driver.current_url.lower()

    # --- progress watchdog ---     
    if acted:
        no_progress_count = 0
    else:
        no_progress_count += 1
        logging.info(f"⚠️ No progress made ({no_progress_count}/{MAX_NO_PROGRESS})")
        if no_progress_count >= MAX_NO_PROGRESS:
            logging.info("🛑 Max no-progress reached — breaking main loop")
            break

    # optional: if continue clicked but url didn’t change, don’t instantly break
    if url_after == url_before:
        time.sleep(0.5)
        
    