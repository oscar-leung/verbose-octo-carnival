from ast import For
import os
import shutil
import time
import requests
import pyautogui
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

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
    driver = webdriver.Chrome()
    driver.get("https://www.linkedin.com/home")
    print("Step 1: WebDriver initalized and website opened! Currently on Login Page")

    # Login Page 
    wait = WebDriverWait(driver, 60)
    username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
    username_input.send_keys(user_name)
    password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="current-password"]')))
    password_input.send_keys(password)
    submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-tracking-control-name="homepage-basic_sign-in-submit-btn"]')))
    submit_button.click()
    print("Step 2: Successfully Logged In! Currently on Home Page")

    # Job Page - Recommended 
    driver.get("https://www.linkedin.com/jobs/collections/recommended/")
    print("Step 3: Currently on Recommended Job Page!")

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


if __name__ == "__main__":
    # Start the timer
    start_time = start_timer()

    # Execute the main function
    main()

    # End the timer and print elapsed time
    end_timer(start_time)
