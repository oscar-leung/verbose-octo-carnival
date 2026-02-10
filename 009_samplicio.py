import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException
)


# --- FUNCTION DEFINITIONS for Samlicio ---
def select_random_checkbox(driver):
    """Selects a random checkbox from any question_ element and presses Enter."""
    try:
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox' and contains(@name, 'question_')]")
        if not checkboxes:
            raise NoSuchElementException("❌ No checkboxes found!")

        random_checkbox = random.choice(checkboxes)
        driver.execute_script("arguments[0].scrollIntoView(true);", random_checkbox)
        random_checkbox.click()
        time.sleep(0.5)
        random_checkbox.send_keys(Keys.ENTER)
        print("✅ Random checkbox selected and Enter pressed.")

    except (NoSuchElementException, ElementClickInterceptedException,
            ElementNotInteractableException, StaleElementReferenceException,
            TimeoutException) as e:
        print(f"⚠️ Checkbox selection failed: {type(e).__name__} - {e}")

def select_random_radio(driver):
    """Selects a random radio button from any question_ element and presses Enter."""
    try:
        radio_buttons = driver.find_elements(By.XPATH, "//input[@type='radio' and contains(@name, 'question_')]")
        if not radio_buttons:
            raise NoSuchElementException("❌ No radio buttons found!")

        random_radio = random.choice(radio_buttons)
        driver.execute_script("arguments[0].scrollIntoView(true);", random_radio)
        random_radio.click()
        time.sleep(0.5)
        random_radio.send_keys(Keys.ENTER)
        print("✅ Random radio button selected and Enter pressed.")

    except (NoSuchElementException, ElementClickInterceptedException,
            ElementNotInteractableException, StaleElementReferenceException,
            TimeoutException) as e:
        print(f"⚠️ Radio selection failed: {type(e).__name__} - {e}")



# --- MAIN EXECUTION ---
if __name__ == "__main__":
    driver = webdriver.Chrome()
    driver.get("https://www.samplicio.us/s/Profiler.aspx?SSID=68fb064b-b94e-41ab-5612-b4248b32707d&SuID=7eec869302067&zToken=1298abc6-7df2-40a3-87eb-a06812638b93")

    time.sleep(2)  # Wait for page to load

    # Try both functions safely
    select_random_checkbox(driver)
    select_random_radio(driver)

    # driver.quit()


################################## https://m.survey.bz/idec/survey/selfserve/1582/251000?list=113&smt=1&RID=68fb0ef9-872d-b39b-a0e1-abca05cb95a6&session_id=ISA-2ef31059-19c1-4b62-86f7-8d5ca791c070



def enter_random_age(driver, min_age=18, max_age=65):
    """Finds a numeric text field for age and enters a random number."""
    try:
        # Look for input fields that take numbers
        age_inputs = driver.find_elements(By.XPATH, "//input[@type='text' and contains(@name, 'ans') and @inputmode='numeric']")
        if not age_inputs:
            raise Exception("❌ No numeric input fields found.")

        # Pick the first or random numeric input
        age_input = random.choice(age_inputs)
        driver.execute_script("arguments[0].scrollIntoView(true);", age_input)

        # Generate a random age
        random_age = random.randint(min_age, max_age)

        # Enter it
        age_input.clear()
        age_input.send_keys(str(random_age))
        time.sleep(0.3)
        # age_input.send_keys(Keys.ENTER)
        print(f"✅ Entered random age: {random_age}")

    except Exception as e:
        print(f"⚠️ Failed to enter random age: {e}")

driver.get("https://m.survey.bz/idec/survey/selfserve/1582/251000?list=113&smt=1&RID=68fb0ef9-872d-b39b-a0e1-abca05cb95a6&session_id=ISA-2ef31059-19c1-4b62-86f7-8d5ca791c070")
driver.find_element(By.XPATH, "//label[contains(., 'I understand')]").click()
driver.find_element(By.XPATH, "//button[@id='submitOk']").click()
Select(driver.find_element(By.XPATH, "//select[contains(@name,'ans') and contains(@class,'dropdown')]")).select_by_visible_text("California")
driver.find_element(By.XPATH, "//input[@id='btn_continue']").click()


enter_random_age(driver, min_age=18, max_age=65)

################################## https://m.survey.bz/idec/survey/selfserve/1582/251000?list=113&smt=1&RID=68fb0ef9-872d-b39b-a0e1-abca05cb95a6&session_id=ISA-2ef31059-19c1-4b62-86f7-8d5ca791c070
driver.get("https://www.surveymeasure.com/surveys/693bd6b00357818c0ac6de4317d6dfd0/")



# Example list of "human-like" text answers
TEXT_ANSWERS = [
    "I don't have a strong preference.",
    "I lean towards the first option.",
    "I usually decide based on context.",
    "Not sure, but I try to stay informed.",
    "I tend to follow general consensus."
]

def answer_random_question(driver):
    """
    Handles both radio and text input questions and clicks Next.
    
    :param driver: Selenium WebDriver instance
    """
    wait = WebDriverWait(driver, 10)
    
    # Wait until the question form is visible
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "form#question_form")))
    
    # Check for radio buttons
    radio_inputs = driver.find_elements(By.CSS_SELECTOR, "input.radio__input")
    if radio_inputs:
        choice = random.choice(radio_inputs)
        choice.click()
        print(f"Selected radio option: {choice.get_attribute('value')}")
    
    # Otherwise check for text input
    textareas = driver.find_elements(By.CSS_SELECTOR, "textarea")
    if textareas:
        answer = random.choice(TEXT_ANSWERS)
        textareas[0].send_keys(answer)
        print(f"Entered text answer: {answer}")
    
    # Click Next button
    next_button = driver.find_element(By.ID, "next")
    next_button.click()
    time.sleep(1)  # wait a bit for next question to load


# Answer a question
answer_and_next(driver, "White")  # selects "White" and clicks Next

# Can repeat for next questions
answer_and_next(driver, "Asian")
answer_and_next(driver, "Other")
answer_and_next(driver, "Advanced degree (such as Master's, Professional, or Doctorate degree)")