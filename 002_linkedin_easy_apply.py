from ast import For

from multiprocessing.connection import wait
from selenium.common.exceptions import StaleElementReferenceException
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
    wait = WebDriverWait(driver, 60)
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
    ul_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.scaffold-layout__list-container')))
    # Learning - https://prnt.sc/9KBp58duY-rO - You can select multiple attributes in the attached image | Milestone 002 - https://prnt.sc/bmUK_--qvZKZ
    list_items = ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')
    print("Number of list items:", len(list_items))
    counter = 0
    for item in list_items:
        item.click()
        counter += 1
        print(f"Clicked on Job Posting {counter}")
        time.sleep(2)
        # Clicking "Easy Apply" button | Learning on using substring within CSS Selector https://prnt.sc/0LbN5DZAiBMg
        try:

            job_title = item.find_element(By.CSS_SELECTOR, 'a.job-card-container__link.job-card-list__title').text
            company_name = item.find_element(By.CSS_SELECTOR, 'span.job-card-container__primary-description').text
            location = item.find_element(By.CSS_SELECTOR, 'li.job-card-container__metadata-item').text
            print(f"Job Title: {job_title}, Company Name: {company_name}, Location: {location}")

            easy_apply_button_locator = (By.CSS_SELECTOR, 'button.jobs-apply-button[aria-label*="Easy Apply"]')
            easy_apply_button = WebDriverWait(driver, 5).until(EC.presence_of_element_located(easy_apply_button_locator))
            easy_apply_button.click()
            print("Easy Apply button clicked")
            navigate_application_process()
        except TimeoutException:
            print("TimeoutException: Easy Apply button not found")
            continue
        except StaleElementReferenceException:
            print("StaleElementReferenceException: Retrying to click Easy Apply button")
            # Re-find the list items
            list_items = ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')
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
    try:
        navigate_to_contact_info_page()
    except Exception as e:
        print(f"Error navigating to Contact Info Page: {e}")

    try:
        navigate_to_home_address_page()
    except Exception as e:
        print(f"Error navigating to Home Address Page: {e}")

    try:
        navigate_to_resume_page()
    except Exception as e:
        print(f"Error navigating to Resume Page: {e}")

    try:
        navigate_to_additional_questions_page()
    except Exception as e:
        print(f"Error navigating to Additional Questions Page: {e}")

    try:
        navigate_to_work_authorization_page()
    except Exception as e:
        print(f"Error navigating to Work Authorization Page: {e}")

    try:
        navigate_to_review_application_page()
    except Exception as e:
        print(f"Error navigating to Review Your Application Page: {e}")

    try:
        navigate_to_applied_page()
    except Exception as e:
        print(f"Error navigating to Applied Page: {e}")


# Implement functions for navigating to each page
def navigate_to_contact_info_page():
    # Implementation for navigating to Contact Info Page
    try:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on Contact Info Page")
    except TimeoutException:
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Submit application"]'))).click()
        print("Just click \"Submit application\" on \"Contact Info Page\" Page")

def navigate_to_home_address_page():
    # Implementation for navigating to Home Address Page
    time.sleep(2)

def navigate_to_resume_page():
    # Implementation for navigating to Resume Page
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on \"Resume\" Page")
    except TimeoutException:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
        print("Just click \"Review\" on \"Addition Questions\" Page")


def navigate_to_additional_questions_page():
    # Implementation for navigating to Additional Questions Page
    try:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]'))).click()
        print("Just click \"Next\" on \"Addition Questions\" Page")
    except TimeoutException:
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
        print("Just click \"Review\" on \"Addition Questions\" Page")

def navigate_to_work_authorization_page():
    # Implementation for navigating to Work Authorization Page
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Review your application"]'))).click()
    print("Just click \"Next\" on \"Work Authorization\" Page")


def navigate_to_review_application_page():
    # Implementation for navigating to Review Your Application Page
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Submit application"]'))).click()
    print("Just click \"Submit application\" on \"Review your application\" Page")

def navigate_to_applied_page():
    # Implementation for navigating to Applied Page 1
    time.sleep(2)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Dismiss"]'))).click()
    print("Just click \"X\" button on Applied Page")

if __name__ == "__main__":
    # Start the timer
    start_time = start_timer()

    # Execute the main function
    main()

    # End the timer and print elapsed time
    end_timer(start_time)
