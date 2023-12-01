import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException

class LinkedInBot:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.linkedin.com/home")
        self.wait = WebDriverWait(self.driver,10)
        print("LinkedIn bot 1.0 at your service! What would you like to do?")

    def login(self, username:str, password:str):
        username_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        username_input.send_keys(username)
        password_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="current-password"]')))
        password_input.send_keys(password)
        submit_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-tracking-control-name="homepage-basic_sign-in-submit-btn"]')))
        submit_button.click()

    def navigate_to(self, url:str):
        self.driver.get(url)

    def get_job_list(self) -> list:
        ul_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.scaffold-layout__list-container')))
        return ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')

    def dismiss_modal(self, modal_selector:str):
        try:
            modal_element = self.wait.until(EC.visibility_of_element_located(By.CSS_SELECTOR,modal_selector))
            discard_btn = modal_element.find_element(By.CSS_SELECTOR, "button[data-test-dialog-secondary-btn]")
            discard_btn.click()
            # Wait for the modal to close (adjust the timeout accordingly)
            self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_selector)))

        except TimeoutException:
            logging.warning(f"Modal not found within the specified time: {modal_selector}")
        except NoSuchElementException:
            logging.warning(f"Discard button not found in the modal: {modal_selector}")
        except Exception as e:
            logging.error(f"Unable to dismiss the modal! \nError: {e}")
            self.driver.save_screenshot("error_screenshot.png")
    
    def apply(self, job_list:list):
        for counter,job in enumerate (job_list,start=1) :
            job_title = job.find_element(By.CSS_SELECTOR, 'a.job-card-container__link.job-card-list__title').text
            company_name = job.find_element(By.CSS_SELECTOR, 'span.job-card-container__primary-description').text
            location = job.find_element(By.CSS_SELECTOR, 'li.job-card-container__metadata-item').text
            print(f"Job {counter}: Job Title: {job_title}, Company Name: {company_name}, Location: {location}")
            try:
                job.click()
                print(f"Job Posting {counter} clicked!")
                self.retry_clicks('button.jobs-apply-button[aria-label*="Easy Apply"]',3)
                self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test-modal-id="easy-apply-modal"]')))
                self.easy_application_process()
            except TimeoutException as e:
                print(f"TimeoutException: Skipping Apple Button: {e}")
                continue
            except StaleElementReferenceException:
                print("StaleElementReferenceException: Retrying to click Easy Apply button")
                self.retry_clicks('button.jobs-apply-button[aria-label*="Easy Apply"]',3)
                self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-test-modal-id="easy-apply-modal"]')))
                self.easy_application_process()
                

    def easy_application_process(self, max_attempts=10):
        for _ in range(max_attempts):
            try:
                next_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Continue to next step"]')))
                next_btn.click()
                print("Next Button Clicked!")
                time.sleep(1)
            except TimeoutException:
                print("TimeoutException in easy_application_process. Looking for submit button now.")
                break  # Break out of the loop if the "Review your application" button is not found within the timeout

        try:
            review_btn = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Review your application"]')))
            review_btn.click()
            print("Review Button Clicked!")
            time.sleep(1)
        except TimeoutException:
            print("TimeoutException: Review button not found.")

        try:
            submit_btn = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="Submit application"]')))
            submit_btn.click()
            print("Submit Button Clicked!")
            time.sleep(1)
        except TimeoutException:
            print("TimeoutException: Submit button not found.")

        try:
            done_btn = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class*="artdeco-button--primary"]')))
            done_btn.click()
            print("Done Button Clicked!")
            time.sleep(1)
        except TimeoutException:
            print("TimeoutException: Done button not found.")

            
    def retry_clicks(self, btn_selector:str, tries:int):
        max_retries = tries
        try:
            btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, btn_selector)))
        except TimeoutException as te:
            logging.error(f"Timed out waiting for element: {te}")
            return

        for _ in range (max_retries):
            try:
                btn.click()
                print("Button Clicked!")
                break
            except (StaleElementReferenceException, ElementNotInteractableException) as e:
                logging.warning(f"Exception during button click: {e}")
            except Exception as e:
                logging.error(f"Unexpected exception during button click: {e}")
                break


if __name__ == "__main__":
    oscar_bot = LinkedInBot()
    oscar_bot.login("oscarleung1@gmail.com","Bumblebee5%2022")
    oscar_bot.navigate_to("https://www.linkedin.com/jobs/collections/recommended/")
    job_list = oscar_bot.get_job_list()
    oscar_bot.apply(job_list)
