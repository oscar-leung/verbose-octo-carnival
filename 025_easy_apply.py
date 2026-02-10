import logging
import random
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

def clickWebElement(xpath, pre_wait=(0.2, 0.9), post_wait=(0.2, 2.1)):
    try:
        # small "aim" delay before clicking
        human_wait(*pre_wait)

        element = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)

        # micro delay after scroll (feels more human)
        human_wait(0.15, 0.6)

        element.click()
        logging.info(f"Clicked element with xpath {xpath}")

        # small delay after clicking
        human_wait(*post_wait)

    except (TimeoutException, ElementClickInterceptedException, StaleElementReferenceException,
            NoSuchElementException, ElementNotInteractableException) as e:
        logging.error(f"Error clicking element with xpath {xpath}: {e}")

def element_exists(xpath):
    return len(driver.find_elements(By.XPATH, xpath)) > 0

def job_application_model_button_flow():
    if element_exists(REVIEW_BUTTON):
        clickWebElement(REVIEW_BUTTON)

        if element_exists(SUBMIT_BUTTON):
            clickWebElement(SUBMIT_BUTTON, pre_wait=(0.4, 1.2), post_wait=(1.0, 2.5))

        clickWebElement(DISMISS_BUTTON, pre_wait=(0.4, 1.2), post_wait=(0.8, 1.8))
        logging.info("Application submitted successfully.")

    elif element_exists(NEXT_BUTTON):
        clickWebElement(NEXT_BUTTON)

    elif element_exists(SUBMIT_BUTTON):
        clickWebElement(SUBMIT_BUTTON, pre_wait=(0.4, 1.2), post_wait=(2.0, 2.5))
        clickWebElement(DISMISS_BUTTON, pre_wait=(0.4, 1.2), post_wait=(0.8, 1.8))

    else:
        logging.warning("Neither Review nor Continue button found.")

def fill_work_authorization_questions():
    questions = [
        {
            "text": "Are you willing to take a drug test, in accordance with local law/regulations?",
            "answer": "Yes"
        },
        {
            "text": "Will you now, or in the future, require sponsorship for employment visa status",
            "answer": "No"
        },
        {
            "text": "Part of the interview process will be in-person in our San Francisco office. If you are not currently based in the SF/Bay Area, you will not be considered for this position. Are you currently residing in the SF/Bay Area?",
            "answer": "Yes"
        },
        {
            "text": "Do you have unrestricted right to work in the country in which this position is based?",
            "answer": "No"
        },
        {
            "text": "Excluding the transfer or extension of a currently valid H1B visa, will you now or in the future require sponsorship for employment authorization in the country in which this position is based?",
            "answer": "No"
        },
        {
            "text": "I am allowing Quantcast to contact me about future job opportunities for up to 1 year.",
            "answer": "Yes"
        },
        {
            "text": "Security Clearance",
            "answer": "None"
        },
        {
            "text": "What is your target salary range?",
            "answer": "100k-110k"
        },
        {
            "text": "Are you legally authorized to work in the United States WITHOUT employer sponsorship (i.e., C2C, H1B, EAD, OPT, F1 or TN) now or in the future?",
            "answer": "Yes"
        },
        {
            "text": "Are you comfortable commuting to this job's location?",
            "answer": "Yes"
        },
        {
            "text": "Are you comfortable working in a remote setting?",
            "answer": "Yes"
        },
        {
            "text": "Will you now or in the future require sponsorship for employment visa status?",
            "answer": "No"
        },
        {
            "text": "How did you hear about this job?",
            "answer": "LinkedIn"
        }
    ]

    for q in questions:
        filled = False

        # 1) Try RADIO (your existing behavior)
        try:
            radio_xpath = (
                "//fieldset[.//legend"
                f"[contains(normalize-space(.), {xpath_literal(q['text'])})]]"
                f"//label[@data-test-text-selectable-option__label={xpath_literal(q['answer'])}]"
            )
            el = driver.find_element(By.XPATH, radio_xpath)
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
            driver.execute_script("arguments[0].click();", el)
            filled = True
        except Exception:
            pass

        # 2) Try DROPDOWN <select> (for "How did you hear about this job?")
        if not filled:
            try:
                # Find the label by text, then grab its "for" attribute which equals the select's id
                label_xpath = (
                    f"//label[contains(normalize-space(.), {xpath_literal(q['text'])})]"
                )
                label_el = driver.find_element(By.XPATH, label_xpath)
                select_id = label_el.get_attribute("for")

                select_el = driver.find_element(By.ID, select_id)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", select_el)

                Select(select_el).select_by_visible_text(q["answer"])
                filled = True
            except Exception as e:
                logging.info(f"Dropdown not found or failed: {q['text']} → {e}")

        if not filled:
            logging.info(f"Question not found/filled: {q['text']}")
    
    # I agree checkbox
    if element_exists("//fieldset//input[@data-test-text-selectable-option__input='I agree']"):
        driver.find_element(By.XPATH, "//label[@data-test-text-selectable-option__label='I agree']").click()

    if element_exists(f"//label[normalize-space()='What is your expected W2 hourly rate for 100% remote role?']"):
        driver.find_element(By.XPATH, "//label[normalize-space()='What is your expected W2 hourly rate for 100% remote role?']").send_keys("100k")

def fill_voluntary_self_identification(
    driver: webdriver.Chrome,
    full_name: str,
    race_text: str = "I prefer not to specify",
    today_str: str = None,
    timeout: int = 15
):
    """
    Fills the Voluntary self identification section in LinkedIn Easy Apply:
    - Gender: Male
    - Race/Ethnicity: race_text (default: I prefer not to specify)
    - Veteran status: I am not a protected veteran
    - Disability: No, I do not have a disability...
    - Your Name: full_name
    - Today's Date: today_str (defaults to today's date)
    - Click both Confirmed checkboxes
    """
    wait = WebDriverWait(driver, timeout)

    if today_str is None:
        today_str = date.today().strftime("%m/%d/%Y")  # adjust if needed

    # Ensure modal + section exists
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//div[@data-test-modal and @role='dialog']")
    ))
    wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h3[contains(normalize-space(),'Voluntary self identification')]")
    ))

    # Gender
    gender_select = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//label[.//strong[normalize-space()='Gender']]/following::select[1]"
    )))
    Select(gender_select).select_by_visible_text("Male")

    # Race/Ethnicity
    race_select = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//label[.//strong[normalize-space()='Race/Ethnicity']]/following::select[1]"
    )))
    Select(race_select).select_by_visible_text(race_text)

    # Veteran status
    vet_select = wait.until(EC.element_to_be_clickable((
        By.XPATH, "(//select[.//option[normalize-space()='I am not a protected veteran']])[1]"
    )))
    Select(vet_select).select_by_visible_text("I am not a protected veteran")

    # Disability
    disability_select = wait.until(EC.element_to_be_clickable((
        By.XPATH,
        "(//select[.//option[normalize-space()='No, I do not have a disability and have not had one in the past']])[1]"
    )))
    Select(disability_select).select_by_visible_text(
        "No, I do not have a disability and have not had one in the past"
    )

    # Your Name
    name_input = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//label[normalize-space()='Your Name']/following::input[1]"
    )))
    name_input.clear()
    name_input.send_keys(full_name)

    # Today's Date
    date_input = wait.until(EC.element_to_be_clickable((
        By.XPATH, "//label[normalize-space()=\"Today's Date\"]/following::input[1]"
    )))
    date_input.clear()
    date_input.send_keys(today_str)

    # Confirmed checkboxes (first two)
    confirmed_boxes = wait.until(lambda d: d.find_elements(
        By.XPATH, "//input[@data-test-text-selectable-option__input='Confirmed' and @type='checkbox']"
    ))
    for cb in confirmed_boxes[:2]:
        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", cb)
        if not cb.is_selected():
            driver.execute_script("arguments[0].click();", cb)

    return True

def xpath_literal(s: str) -> str:
    """Safely escape strings for XPath (handles apostrophes)."""
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'
    parts = s.split("'")
    return "concat(" + ", ".join(
        f"'{p}'" if i == len(parts)-1 else f"'{p}',\"'\","
        for i, p in enumerate(parts)
    )[:-1] + ")"

def reset_easy_apply_and_continue():
    
    """
    Emergency reset when Easy Apply gets stuck.
    Closes the modal and moves on to the next job.
    """
    try:
        # Try Dismiss button
        if element_exists(DISMISS_BUTTON):
            clickWebElement(DISMISS_BUTTON)
            if element_exists("//div[@role='alertdialog']//button[@data-control-name='discard_application_confirm_btn']"):
                clickWebElement("//div[@role='alertdialog']//button[@data-control-name='discard_application_confirm_btn']") # Discard Button
                time.sleep(1)
                return
    except Exception as e:
        logging.error(f"Reset failed: {e}")

# --- Human-like delays ---
HUMAN_DELAY_ENABLED = True

def human_wait(min_s=0.4, max_s=2.3, long_pause_chance=0.08, long_min=2.0, long_max=4.5):
    """
    Randomized delay to reduce bot-like timing.
    - min_s/max_s: normal jitter range
    - long_pause_chance: occasionally add a longer "thinking" pause
    """
    if not HUMAN_DELAY_ENABLED:
        return

    t = random.uniform(min_s, max_s)
    time.sleep(t)

    # occasional longer pause
    if random.random() < long_pause_chance:
        time.sleep(random.uniform(long_min, long_max))

# Load variables from .env
load_dotenv()
username = os.getenv("LINKIN_USERNAME")
password = os.getenv("LINKIN_PASSWORD")

# Initialize variables
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)

# XPath selectors
EASY_BUTTON = "//button[@id='jobs-apply-button-id']"
NEXT_BUTTON = "//button[@aria-label='Continue to next step']"
REVIEW_BUTTON = "//button[@aria-label='Review your application']"
SUBMIT_BUTTON = "//button[@aria-label='Submit application']"
DISMISS_BUTTON = "//button[@aria-label='Dismiss']"


driver.get("https://www.linkedin.com/login")
zoom_out()
move_window_to_topright()

# login to linkedin
driver.find_element(By.ID,"username").send_keys(username)
driver.find_element(By.ID,"password").send_keys(password)
clickWebElement("//button[@type='submit']")

# nav to job postings page
driver.get("https://www.linkedin.com/jobs/collections/easy-apply/")

# get list of job postings – should be 25 per page by default or less
job_list = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")
logging.info(f"Found {len(job_list)} job postings")

# todo loop through all job posting

for index, job in enumerate(job_list):
    try:
        time.sleep(2)
        driver.execute_script("arguments[0].scrollIntoView();", job)
        job.click()
        logging.info(f"Clicked job #{index + 1}")

        human_wait(1.0, 2.8, long_pause_chance=0.10, long_min=3.0, long_max=7.0)


        if not element_exists(EASY_BUTTON):
            logging.info(f"Job #{index + 1} has no Easy Apply. Skipping.")
            continue

        clickWebElement(EASY_BUTTON)    

        # contact info 
        if element_exists("//h3[normalize-space()='Contact info']"):
            job_application_model_button_flow()

        # home address
        if element_exists("//input[contains(@id,'city-HOME-CITY')]"):
            driver.find_element(By.XPATH, "//input[contains(@id,'city-HOME-CITY')]").send_keys("Santa Clara")
            os.system("osascript -e 'tell application \"Google Chrome\" to activate'")
            time.sleep(1)
            pyautogui.press('down')
            pyautogui.press('enter')
            job_application_model_button_flow()

        # resume 
        if element_exists("//h3[normalize-space()='Resume']"):
            if element_exists("//label[normalize-space()='LinkedIn']"):
                driver.find_element(By.XPATH,"//div[@data-test-single-line-text-form-component][.//label[normalize-space()='LinkedIn']]//input").send_keys("https://www.linkedin.com/in/oscar-leung/")
        job_application_model_button_flow()

        # work experience
        if element_exists("//h3[normalize-space()='Work experience']"):
            job_application_model_button_flow()

        # education
        if element_exists("//h3[normalize-space()='Education']"):
            job_application_model_button_flow()
        
        # Voluntary self identification
        if element_exists("//h3[normalize-space()='Voluntary self identification']"):
            fill_voluntary_self_identification(driver,full_name="Oscar Leung", race_text="Asian (Not Hispanic or Latino)")
            job_application_model_button_flow()
        

        # screening questions
        if element_exists("//h3[normalize-space()='Screening questions']"):
            job_application_model_button_flow()

        # Privacy policy
        if element_exists("//h3[normalize-space()='Privacy policy']"):
            clickWebElement("//label[@data-test-text-selectable-option__label='I Agree Terms & Conditions']")
            job_application_model_button_flow()

        # additional questions
        if element_exists("//h3[normalize-space()='Additional Questions']"): 
            containers = driver.find_elements(By.XPATH, "//div[@class='ph5']/div[1]/div") # question containers
            for index, box in enumerate(containers):
                try:
                    box.find_element(By.XPATH, ".//input").clear()                    
                    box.find_element(By.XPATH, ".//input").send_keys("1")                    
                except:
                    logging.info(f"No input box in container {index}, skipping.")
                try:
                    Select(box.find_element(By.XPATH, ".//select")).select_by_visible_text("Yes")
                except:
                    logging.info(f"No select dropdown in container {index}, skipping.")
                fill_work_authorization_questions()
            job_application_model_button_flow()

        # 2nd additional questions
        if element_exists("//h3[normalize-space()='Additional Questions']"): 
            fill_work_authorization_questions()
            job_application_model_button_flow()

        # 3rd additional questions
        if element_exists("//h3[normalize-space()='Additional Questions']"): 
            fill_work_authorization_questions()
            job_application_model_button_flow()

        # 4th additional questions
        if element_exists("//h3[normalize-space()='Additional Questions']"): 
            fill_work_authorization_questions()
            job_application_model_button_flow()


        # work authrization 
        if element_exists("//h3[normalize-space()='Work authorization']"):
            fill_work_authorization_questions()
            job_application_model_button_flow()

    except Exception as e:
        logging.error(f"Application stuck on job #{index + 1}: {e}")
        reset_easy_apply_and_continue()
        continue
