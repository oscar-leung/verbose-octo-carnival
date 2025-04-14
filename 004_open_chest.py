import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException



driver = webdriver.Chrome()
driver.get("https://habitica.com/login?redirectTo=%2Fparty")


wait = WebDriverWait(driver, 60)
username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id="usernameInput"]')))
username_input.send_keys("oscarleung1@gmail.com")

password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id="passwordInput"]')))
password_input.send_keys("Bumblebee6^2023")

signin_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[class="btn btn-info"]')))
signin_button.click()

driver.get("https://habitica.com/shops/market")

# Define the number of attempts
num_attempts = 36

for _ in range(34):

        # Wait for the chest button to be present
        chest_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.shop_armoire')))
        chest_btn.click()

        # Wait for the buy button to be present
        buy_btn = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[tabindex="0"]')))
        buy_btn.click()

        # You may want to add some additional logic here to handle what happens after clicking the buy button
        time.sleep(1)
