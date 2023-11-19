from multiprocessing.connection import wait
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import ElementClickInterceptedException

import shutil
import time
import re

import pyautogui
import json
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# Global variable
wait = None
driver = webdriver.Chrome()
submit_button_clicked = False
review_button_clicked = False

def read_credentials_from_json(json_file_path):
    """
    Reads user credentials from a JSON file.

    Parameters:
    - json_file_path (str): The path to the JSON file containing user credentials.

    Returns:
    - tuple: A tuple containing (user_name, password) extracted from the JSON file.
    """
    with open(json_file_path, "r") as json_file:
        data = json.load(json_file)

    user_name = data["email"]
    password = data["password1"]

    return user_name, password

def main():
    """
    Your main script logic goes here.
    """
    # Example: Reading credentials from a JSON file
    json_file_path = "/Users/oscarleung/Selenium-Python/config/config.json"
    user_name, password = read_credentials_from_json(json_file_path)

    # Your script logic here
    driver.get("https://www.linkedin.com/home")
    print("Step 1: WebDriver initalized and website opened! Currently on Login Page")

    # Login Page 
    global wait
    wait = WebDriverWait(driver, 10)
    username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
    username_input.send_keys(user_name)
    password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="current-password"]')))
    password_input.send_keys(password)
    submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-tracking-control-name="homepage-basic_sign-in-submit-btn"]')))
    submit_button.click()
    print("Step 2: Successfully Logged In! Currently on Security Check Page")

    # Human Verification
    # home_page_url = driver.current_url()
    # if re.match(r'^https://www\.linkedin\.com/feed/', home_page_url):
    #     # Recommended Job Page
    driver.get("https://www.linkedin.com/jobs/collections/recommended/")
    print("Step 3: Successfully human verified. Currently on Recommended Job Page!")
        

    # Function to get a list of items in https://prnt.sc/M-YQgNYdTNnP
    ul_element = WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.scaffold-layout__list-container')))
    # Learning - https://prnt.sc/9KBp58duY-rO - You can select multiple attributes in the attached image | Milestone 002 - https://prnt.sc/bmUK_--qvZKZ
    list_items = ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')
    print("Number of list items:", len(list_items))
    counter = 0
    for item in list_items:
        item.click()
        item.click()
        counter += 1
        print(f"Clicked on Job Posting {counter}")
        # Clicking "Easy Apply" button | Learning on using substring within CSS Selector https://prnt.sc/0LbN5DZAiBMg
        try:

            job_title = item.find_element(By.CSS_SELECTOR, 'a.job-card-container__link.job-card-list__title').text
            company_name = item.find_element(By.CSS_SELECTOR, 'span.job-card-container__primary-description').text
            location = item.find_element(By.CSS_SELECTOR, 'li.job-card-container__metadata-item').text
            print(f"Job Title: {job_title}, Company Name: {company_name}, Location: {location}")

            easy_apply_button_locator = (By.CSS_SELECTOR, 'button.jobs-apply-button[aria-label*="Easy Apply"]')
            easy_apply_button = wait.until(EC.presence_of_element_located(easy_apply_button_locator))
            max_retries = 3
            for retry in range(max_retries):
                time.sleep(2)
                easy_apply_button.click()
                print("Easy Apply button clicked")
                # Wait for the modal to appear
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test-modal-id="easy-apply-modal"]'))  # Adjust the locator based on your modal structure
                    )
                    print("Modal appeared!")
                    navigate_application_process()
                    break # Break the loop is successful
                except Exception as e:
                    print("Error waiting for the modal: ", str(e))
                
        except TimeoutException:
            print("TimeoutException: Easy Apply button not found")
            continue
        except StaleElementReferenceException:
            print("StaleElementReferenceException: Retrying to click Easy Apply button")
            # Re-find the list items
            list_items = ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')
            time.sleep(2)
            easy_apply_button_locator = (By.CSS_SELECTOR, 'button.jobs-apply-button[aria-label*="Easy Apply"]')
            easy_apply_button = wait.until(EC.presence_of_element_located(easy_apply_button_locator))
            for retry in range(max_retries):
                time.sleep(2)
                easy_apply_button.click()
                print("Easy Apply button clicked")
                # Wait for the modal to appear
                try:
                    WebDriverWait(driver, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test-modal-id="easy-apply-modal"]'))  # Adjust the locator based on your modal structure
                    )
                    print("Modal appeared!")
                    navigate_application_process()
                    break # Break the loop is successful
                except Exception as e:
                    print("Error waiting for the modal: ", str(e))
            continue

    
    time.sleep(2)
    # ... (add more script logic)

def start_timer():
    """
    Starts a timer.
    
    Returns:
    - float: The starting time.
    """
    return time.time()

def end_timer(start_time):
    """
    Ends the timer and prints the elapsed time.

    Parameters:
    - start_time (float): The starting time returned by start_timer().
    """
    end_time = time.time()
    elapsed_time = end_time - start_time

    print(f"Script execution time: {elapsed_time:.2f} seconds")

def navigate_application_process():
    # Now, navigate through the application process based on https://miro.com/app/board/uXjVNOGrDgA=/ or https://prnt.sc/Goyrr_c_92tB
    navigation_functions = [
        navigate_to_contact_info_page,
        navigate_to_home_address_page,
        navigate_to_resume_page,
        navigate_to_photo_page,
        navigate_to_work_experience_page,
        navigate_to_education_page,
        navigate_to_additional_questions_page,
        navigate_to_work_authorization_page,
        navigate_to_review_application_page,
        navigate_to_applied_page
    ]

   # Flag to check if "Submit application" is clicked
    submit_button_clicked = False
    review_button_clicked = False

    if submit_button_clicked:
        navigate_to_applied_page()
        submit_button_clicked = False
    if review_button_clicked:
        navigate_to_review_application_page()
        navigate_to_applied_page()
        review_button_clicked = False

    for navigation_function in navigation_functions:
        try:
            navigation_function()
        except TimeoutException:
            print(f"TimeoutException: Timeout while navigating to {navigation_function.__name__}")
        except Exception as e:
            print(f"Error navigating to {navigation_function.__name__}: \n{e}")

# Implement functions for navigating to each page
def navigate_to_contact_info_page():
    # Implementation for navigating to Contact Info Page
    global submit_button_clicked
    contact_info_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if contact_info_text == "Contact info":
        print(f"Actual Text: \"{contact_info_text}\" Expected: \"Contact info\". Navigating through Contact info's page")
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
            print("Just click \"Next\" on Contact Info Page")
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Submit application"]'))).click()
            print("Just click \"Submit application\" on \"Contact Info Page\" Page")
            submit_button_clicked = True
    else:
        print(f"Actual Text: \"{contact_info_text}\" Expected: \"Contact info\". Skipped Contact info's page")

def navigate_to_home_address_page():
    # Implementation for navigating to Home Address Page
    home_address_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if home_address_text == "Home address":
        print(f"Actual Text: \"{home_address_text}\" Expected: \"Home address\". Navigating through Home address's page")
        input_element = driver.find_element(By.CSS_SELECTOR, '[id$="-city-HOME-CITY"]')
        input_element.send_keys("Alameda County, California, United States")
        pyautogui.press("enter")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on Home Address Page")
    else:
        print(f"Actual Text: \"{home_address_text}\" Expected: \"Home address\". Skipped Home address's page")


def navigate_to_photo_page():
    # Implementation for navigating to Photo Page
    photo_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if photo_text == "Photo":
        print(f"Actual Text: \"{photo_text}\" Expected: \"Photo\". Navigating through Photo's page")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on Photo Page")
    else:
        print(f"Actual Text: \"{photo_text}\" Expected: \"Photo\". Skipped through Photo's page")


def navigate_to_work_experience_page():
    # Implementation for navigating to Work Experience Page
    work_experience_text = driver.find_element(By.CSS_SELECTOR, 'h3.t-16.mb2 span.t-bold').text
    if work_experience_text == "Work experience":
        print(f"Actual Text: \"{work_experience_text}\" Expected: \"Work experience\". Navigating through Work experience's page")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on Work Experience Page")
    else:
        print(f"Actual Text: \"{work_experience_text}\" Expected: \"Work experience\". Skipped Work experience's page")

def navigate_to_education_page():
    # Implementation for navigating to Work Experience Page
    global review_button_clicked
    education_text = driver.find_element(By.CSS_SELECTOR, 'h3.t-16.mb2 span.t-bold').text
    if education_text == "Education":
        print(f"Actual Text: \"{education_text}\" Expected: \"Education\". Navigating through Education's page")
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
            print("Just click \"Next\" on Education Page")
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
            print("Just click \"Review\" on \"Education\" Page")
            review_button_clicked = True
    else:
        print(f"Actual Text: \"{education_text}\" Expected: \"Education\". Skipped Education's page")
def navigate_to_resume_page():
    # Implementation for navigating to Resume Page
    global review_button_clicked
    resume_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if resume_text == "Resume":
        print(f"Actual Text: \"{resume_text}\" Expected: \"Resume\". Navigating through Resume's page")
        try:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
            print("Just click \"Next\" on \"Resume\" Page")
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
            print("Just click \"Review\" on \"Resume\" Page")
            review_button_clicked = True
    else:
        print(f"Actual Text: \"{resume_text}\" Expected: \"Resume\". Skipping Resume's page")


def navigate_to_additional_questions_page():
    # Implementation for navigating to Additional Questions Page
    global review_button_clicked
    additional_questions_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if additional_questions_text == "Additional Questions":
        print(f"Actual Text: \"{additional_questions_text}\" Expected: \"Additional Questions\". Navigating through Additional Questions' page")
        try:
            WebDriverWait(driver,30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
            print("Just click \"Next\" on \"Addition Questions\" Page")
        except TimeoutException:
            wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
            print("Just click \"Review\" on \"Addition Questions\" Page")
            review_button_clicked = True
    else:
        print(f"Actual Text: \"{additional_questions_text}\" Expected: \"Additional Questions\". Skipped Additional Questions' page")

def navigate_to_work_authorization_page():
    # Implementation for navigating to Work Authorization Page
    work_authorization_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > div.pb4 > h3.t-16.t-bold').text
    if work_authorization_text == "Work authorization":
        print(f"Actual Text: \"{work_authorization_text}\" Expected: \"Work authorization\". Navigating thought Work authorization's page")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
        print("Just click \"Next\" on \"Work Authorization\" Page")
    else:
        print(f"Actual Text: \"{work_authorization_text}\" Expected: \"Work authorization\". Skipped Work authorization's page")


def navigate_to_review_application_page():
    # Implementation for navigating to Review Your Application Page
    review_application_text = driver.find_element(By.CSS_SELECTOR, 'div.ph5 > h3.t-18').text
    global submit_button_clicked
    if review_application_text == "Review your application":
        print(f"Actual Text: \"{review_application_text}\" Expected: \"Review your application\". Navigating thought Review your application's page")
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Submit application"]'))).click()
        print("Just click \"Submit application\" on \"Review your application\" Page")
        time.sleep(5)
        submit_button_clicked = True
    else:
        print(f"Actual Text: \"{review_application_text}\" Expected: \"Review your application\". Skipped Review your application's page")
def navigate_to_applied_page():
    # Implementation for navigating to Applied Page
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Dismiss"]'))).click()
    print("Just click \"X\" button on Applied Page")


if __name__ == "__main__":
    # Start the timer
    start_time = start_timer()

    # Execute the main function
    main()

    # End the timer and print elapsed time
    end_timer(start_time)