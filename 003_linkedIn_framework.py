from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LinkedInBot:
    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get("https://www.linkedin.com/home")
        self.wait = WebDriverWait(self.driver,10)
        print("LinkedIn bot 1.0 at your service! What would you like to do?")

    def login(self, username, password):
        username_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"]')))
        username_input.send_keys(username)
        password_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="current-password"]')))
        password_input.send_keys(password)
        submit_button = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-tracking-control-name="homepage-basic_sign-in-submit-btn"]')))
        submit_button.click()

    def navigate_to(self, url):
        self.driver.get(url)

    def get_job_list(self):
        ul_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.scaffold-layout__list-container')))
        return ul_element.find_elements(By.CSS_SELECTOR, 'li.jobs-search-results__list-item')

    def dismiss_modal(self, modal_selector):
        try:
            modal_element = self.wait.until(EC.visibility_of_element_located(By.CSS_SELECTOR,modal_selector))
            discard_btn = modal_element.find_element(By.CSS_SELECTOR, "button[data-test-dialog-secondary-btn]")
            discard_btn.click()
        except Exception as e:
            print(f"LinkedIn bot unable to dismiss the modal! \n Error: {e} ")
            self.driver.save_screenshot("error_screenshot.png")

    def apply(self, job_list):
        counter = 0
        for job in job_list:
            if 

if __name__ == "__main__":
    oscar_bot = LinkedInBot()
    oscar_bot.login("oscarleung1@gmail.com","Bumblebee5%2022")
    oscar_bot.navigate_to("https://www.linkedin.com/jobs/collections/recommended/")
    job_list = oscar_bot.get_job_list()
    