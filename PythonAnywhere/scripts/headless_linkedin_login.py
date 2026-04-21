from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

# Configure Chrome to run in headless mode
chrome_options = Options()
chrome_options.add_argument('--headless')               # Run in headless mode (no browser UI)
chrome_options.add_argument('--no-sandbox')             # Required for some systems
chrome_options.add_argument('--disable-dev-shm-usage')  # Prevents crashes due to limited resources

# Initialize WebDriver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Open LinkedIn login page
    driver.get("https://www.linkedin.com/login")
    print("Navigated to LinkedIn login page.")

    # Screenshot LinkedIn Page
    screenshot_path = "linkedin_login_page.png"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

    # Enter login credentials
    driver.find_element(By.ID, "username").send_keys("oscarleung1@gmail.com")
    driver.find_element(By.ID, "password").send_keys("Bumblebee5%2022")  # Replace with your password
    print("Entered credentials.")

    # Screenshot Entered Credentials
    screenshot_path = "linkedin_login_entered_credentials.png"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

    # Click the show button
    driver.find_element(By.XPATH, "//span[@id='password-visibility-toggle']").click()
    print("Clicked show button.")

    # Screenshot Show Credentials
    screenshot_path = "linkedin_login_show_entered_credentials.png"
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved to {screenshot_path}")

    # Click the login button
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    print("Clicked login button.")

    # Wait for the next page to load (you can fine-tune this or use explicit waits)
    time.sleep(5)

    # Check if login was successful by looking for the LinkedIn home URL or feed
    if "feed" in driver.current_url:  # Example: Check if redirected to the home feed
        print("Login successful!")
        # Take a screenshot
        screenshot_path = "linkedin_login_success.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
    else:
        print("Login failed. Check credentials or captcha.")
        screenshot_path = "linkedin_login_unsuccess.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
finally:
    # Close the browser
    driver.quit()
