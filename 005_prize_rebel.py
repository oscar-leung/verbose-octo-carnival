import logging
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException



driver = webdriver.Chrome()
driver.get("https://www.prizerebel.com/login")


wait = WebDriverWait(driver, 60)
username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="email"]')))
username_input.send_keys("oscarleung1@gmail.com")

password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="password"]')))
password_input.send_keys("Bumblebee4$2024")

# Manaully enter CAPTCHA
reCAPTCHA = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span#recaptcha-anchor')))
reCAPTCHA.click()

signin_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[id="loginSubmit"]')))
signin_button.click()


# for Samp Survey
driver.get("https://www.prizerebel.com/sampsurveys.php")
go_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f'//a[text()="GO"]')))
go_link.click()

print(driver.current_url)
driver.switch_to.window(driver.window_handles[-1])
print(driver.current_url)

agree_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[id="option-0"]')))
agree_btn.click()

continue_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[value="Continue"]')))
continue_btn.click()


# for radio options 
random.choice(driver.find_elements(By.CSS_SELECTOR, 'input[type="radio"]')).click()

continue_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[value="Continue →"]')))
continue_btn.click()

# for checkbox options
random.choice(driver.find_elements(By.CSS_SELECTOR, 'input[type="checkbox"]')).click()

continue_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[value="Continue →"]')))
continue_btn.click()

continue_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[id="btn_continue"]')))
continue_btn.click()

# Behaviorally Red Herring Example for 3 * 2

# Find the question element
question_element = driver.find_element(By.CSS_SELECTOR, 'h1.question-text')

# Extract the equation text from the question element
equation_text = question_element.text

# Extract the equation from the text using regular expression
equation_match = re.search(r'(\d+)\s*[xX*]\s*(\d+)', equation_text)
    

if equation_match:
    operand1 = int(equation_match.group(1))
    operand2 = int(equation_match.group(2))
    
    # Calculate the answer
    answer = operand1 * operand2
    
    # Find the input element for the answer
    answer_input = driver.find_element(By.CSS_SELECTOR, 'input[type="text"]')
    
    # Enter the answer into the input field
    answer_input.send_keys(str(answer))
    
    # Find and click the continue button
    continue_btn = driver.find_element(By.ID, 'btn_continue')
    continue_btn.click()

random.choice(driver.find_elements(By.CSS_SELECTOR, 'ul.sq-atm1d-buttons li.sq-atm1d-button')[:-1]).click()

continue_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[id="btn_continue"]')))
continue_btn.click()

# Unfortunately, you did not qualify for this survey. Would you like to try to qualify for another survey?
submit_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,'input[type="submit"]')))
submit_btn.click()

# for Cherries Survey
driver.get("https://www.prizerebel.com/cherries.php")

print(driver.current_url)
driver.switch_to.window(driver.window_handles[-1])

go_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f'//a[text()="GO"]')))
go_link.click()