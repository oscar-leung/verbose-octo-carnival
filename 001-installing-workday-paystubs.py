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

# Specify the path to your JSON file
json_file_path = "/Users/oscarleung/Selenium-Python/config/config.json"

# Open the file and load JSON data
with open(json_file_path, "r") as json_file:
    data = json.load(json_file)

# Accessing values
user_name = data["user_name"]
password = data["password"]

# Set the path to the Downloads folder
downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

# Start the timer
start_time = time.time()

# Step 1: Initialize the WebDriver (Chrome in this case)
driver = webdriver.Chrome()
driver.get("https://www.myworkday.com/maxar/login.flex?redirect=n")
print("Step 1: WebDriver initialized and website opened.")

# Step 2: Log in to the website
# Find and fill the username and password fields, then click the login button
wait = WebDriverWait(driver, 60)
username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Username"]')))
username_input.send_keys(user_name)

password_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Password"]')))
password_input.send_keys(password)

signin_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-automation-id="goButton"]')))
signin_button.click()
print("Step 2: Logged in.")

# Step 3: Handle the "Remember this device" checkbox
checkbox = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Remember this device"]')))
checkbox.click()
print("Step 3: 'Remember this device' checkbox handled.")

# Step 4: Click the submit button after handling the checkbox
submit_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-automation-id="button"]')))
submit_button.click()
print("Step 4: Submit button clicked.")

# Step 5: Navigate to the "My Payslips" section
my_payslip_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[aria-label="My Payslips"]'))).click()
print("Step 5: Navigated to 'My Payslips' section.")

# Step 6: Scroll to load additional content
scroll_wrapper = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="table"]')))
scroll_height = driver.execute_script("return arguments[0].scrollHeight;", scroll_wrapper)
client_height = driver.execute_script("return arguments[0].clientHeight;", scroll_wrapper)

print("Scroll Height:", scroll_height)
print("Client Height:", client_height)


if scroll_height > client_height:
    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", scroll_wrapper)
    time.sleep(5)
    print("Step 6: Scrolled to load additional content.")
else:
    print("Step 6: No more content to load.")

time.sleep(5)

# Find all rows in the table
rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[data-testid="row"]')))

# Counter for the number of paystubs downloaded
paystub_counter = 0

print(f"Step 7: Extract and print data from the table")

# Step 7: Extract and print data from the table
rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[data-testid="row"]')))
for _ in range(len(rows)):
    # Re-locate rows inside the loop to avoid StaleElementReferenceException
    rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'tr[data-testid="row"]')))

    date = rows[_].find_element(By.CSS_SELECTOR, 'th[data-automation-id="cell"]').text
    start_date = rows[_].find_element(By.CSS_SELECTOR, 'td[data-automation-id="cell"]').text
    end_date = rows[_].find_elements(By.CSS_SELECTOR, 'td[data-automation-id="cell"]')[1].text
    company = rows[_].find_element(By.CSS_SELECTOR, 'div[data-automation-id="promptOption"]').text
    amount = rows[_].find_elements(By.CSS_SELECTOR, 'div[data-automation-id="numericText"]')[0].text
    print(f"Date: {date}, Start Date: {start_date}, End Date: {end_date}, Company: {company}, Amount: {amount}")

    # Find and click the "Print" button
    print_button = rows[_].find_element(By.CSS_SELECTOR, 'button[title="Print"]')
    print_button.click()

    # Wait for the "Download PDF" button to appear
    download_pdf_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-automation-id="pdfDownloadButton"]')))
    download_pdf_button.click()

    time.sleep(2)

    # Click on the current window to focus it
    pyautogui.click()
    print("Clicked on the current window to focus it")

    # Simulate Command (or Control) + S keypress
    # Use Keys.CONTROL for Windows/Linux or Keys.COMMAND for macOS
    pyautogui.hotkey("command", "s")   # Simulate Command + S
    print("Simulated Command + S")

    # Wait for the Save dialog to appear (you may need to adjust the delay)
    time.sleep(2)
    print("Waited for 2 seconds")

    # Simulate Enter keypress to confirm the Save action
    pyautogui.press("enter")
    print("Simulated Enter keypress")




    # print("Download PDF button clicked")

    # time.sleep(30)

    # # Use the browser current URL to get the PDF URL
    # pdf_url = driver.current_url

    # # Use requests library to download the PDF
    # response = requests.get(pdf_url)

    # print(response.content)
    # print(f"Content Type: {response.headers.get('Content-Type')}")
    # print(f"File Size: {len(response.content)} bytes")
    # print(f"PDF URL: {pdf_url}")
    # print(f"Response Status: {response.status_code}")
    # print(f"Response Headers: {response.headers}")
    # print(f"Response Text: {response.text}")

    # Based on the provided debug prints, it seems like your code is encountering a redirect to a login page instead of the expected PDF content. The script clicks the "Download PDF" button, and the response contains HTML with a script for redirecting to the login page.
    # Basically I am stuck on re-directs when trying to fetch the response code. 
    # And I am stuck using keypress outside of selenium since there's no more html elements
    # In short, workday is pretty good at preventing users from downloading alot infomation from their sites
    # But I was able to get alot of screenshots that were enough and learned to write to pdfs from them
    # And getting alist of dates where pretty helpful
    # Check the response status
    # print(f"Response Status: {response.status_code}")

    # Add a delay before saving the PDF
    # time.sleep(5)  # Adjust the delay as needed 

    # Check if the PDF URL starts with the expected prefix
    # expected_prefix = 'https://www.myworkday.com/maxar/repository-doc/'
    # if pdf_url.startswith(expected_prefix):
    #     # Use requests library to download the PDF
    #     response = requests.get(pdf_url, stream=True)

        # # Save the PDF to the Downloads folder
        # pdf_filename = f"Paystub_{paystub_counter}.pdf"
        # pdf_filepath = os.path.join(downloads_path, pdf_filename)
        # with open(pdf_filepath, 'wb') as pdf_file:
        #     pdf_file.write(response.content)

        # Increment the paystub counter
    #     paystub_counter += 1
    #     print(f"Paystub {paystub_counter} downloaded and saved at {pdf_filepath}")
    # else:
    #     print(f"PDF URL does not match the expected prefix: {pdf_url}")
    #     print(f"Expected Prefix: {expected_prefix}")
    #     print(f"Current URL: {pdf_url}")

    # Go back to the previous page to continue the loop
    driver.back()

# Step 8: Add additional actions or close the driver
time.sleep(5000)
time.sleep(5)  # Additional delay
print("Step 8: Additional actions completed.")

# Step 9: Stop the timer and calculate total time
end_time = time.time()
total_time = end_time - start_time
print(f"Step 9: Total time taken: {total_time:.2f} seconds")

# Step 10: Close the WebDriver
driver.quit()
print("Step 10: WebDriver closed.")
