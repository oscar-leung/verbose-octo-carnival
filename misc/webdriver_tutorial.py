"""
Complete Selenium WebDriver Tutorial
===================================

This tutorial covers everything you need to know about:
from selenium import webdriver

Topics covered:
1. Basic WebDriver setup
2. Different browser drivers
3. WebDriver options and configurations
4. Navigation methods
5. Element interaction
6. Wait strategies
7. Error handling
8. Best practices
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    WebDriverException,
    ElementClickInterceptedException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

def section_1_basic_webdriver():
    """
    SECTION 1: Basic WebDriver Setup
    ================================
    
    The most basic way to create a WebDriver instance.
    """
    print("=" * 60)
    print("SECTION 1: Basic WebDriver Setup")
    print("=" * 60)
    
    # Method 1: Basic Chrome WebDriver (requires ChromeDriver in PATH)
    print("\n1. Basic Chrome WebDriver:")
    try:
        driver = webdriver.Chrome()
        print("✅ Chrome WebDriver created successfully")
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        time.sleep(2)
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Note: This requires ChromeDriver to be in your system PATH")

def section_2_webdriver_manager():
    """
    SECTION 2: WebDriver Manager (Recommended)
    ==========================================
    
    Using webdriver-manager to automatically download and manage drivers.
    """
    print("\n" + "=" * 60)
    print("SECTION 2: WebDriver Manager (Recommended)")
    print("=" * 60)
    
    # Method 2: Using webdriver-manager (automatically downloads driver)
    print("\n2. WebDriver with automatic driver management:")
    try:
        # Automatically download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        print("✅ Chrome WebDriver created with automatic driver management")
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        time.sleep(2)
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_3_different_browsers():
    """
    SECTION 3: Different Browser Drivers
    ====================================
    
    How to use different browsers with WebDriver.
    """
    print("\n" + "=" * 60)
    print("SECTION 3: Different Browser Drivers")
    print("=" * 60)
    
    browsers = [
        ("Chrome", webdriver.Chrome, ChromeDriverManager().install()),
        # ("Firefox", webdriver.Firefox, GeckoDriverManager().install()),  # Uncomment if Firefox installed
        # ("Edge", webdriver.Edge, EdgeChromiumDriverManager().install()),  # Uncomment if Edge installed
    ]
    
    for browser_name, browser_class, driver_path in browsers:
        print(f"\n3. {browser_name} WebDriver:")
        try:
            service = Service(driver_path)
            driver = browser_class(service=service)
            print(f"✅ {browser_name} WebDriver created successfully")
            driver.get("https://www.google.com")
            print(f"✅ Navigated to Google using {browser_name}")
            time.sleep(2)
            driver.quit()
            print(f"✅ {browser_name} browser closed")
        except Exception as e:
            print(f"❌ Error with {browser_name}: {e}")

def section_4_webdriver_options():
    """
    SECTION 4: WebDriver Options and Configuration
    ==============================================
    
    How to configure WebDriver with various options.
    """
    print("\n" + "=" * 60)
    print("SECTION 4: WebDriver Options and Configuration")
    print("=" * 60)
    
    print("\n4. WebDriver with custom options:")
    try:
        # Create Chrome options
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
        chrome_options.add_argument("--window-size=1920,1080")  # Set window size
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Custom user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        
        # Headless mode (uncomment to run without browser window)
        # chrome_options.add_argument("--headless")
        
        # Create WebDriver with options
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Remove webdriver property to avoid detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome WebDriver created with custom options")
        driver.get("https://www.google.com")
        print("✅ Navigated to Google with custom configuration")
        time.sleep(2)
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_5_navigation_methods():
    """
    SECTION 5: Navigation Methods
    =============================
    
    Different ways to navigate with WebDriver.
    """
    print("\n" + "=" * 60)
    print("SECTION 5: Navigation Methods")
    print("=" * 60)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        print("\n5. Navigation methods:")
        
        # Method 1: get() - Navigate to a URL
        driver.get("https://www.google.com")
        print("✅ driver.get() - Navigated to Google")
        time.sleep(1)
        
        # Method 2: back() - Go back in browser history
        driver.get("https://www.python.org")
        print("✅ Navigated to Python.org")
        time.sleep(1)
        driver.back()
        print("✅ driver.back() - Went back to Google")
        time.sleep(1)
        
        # Method 3: forward() - Go forward in browser history
        driver.forward()
        print("✅ driver.forward() - Went forward to Python.org")
        time.sleep(1)
        
        # Method 4: refresh() - Refresh the current page
        driver.refresh()
        print("✅ driver.refresh() - Refreshed the page")
        time.sleep(1)
        
        # Method 5: current_url - Get current URL
        current_url = driver.current_url
        print(f"✅ driver.current_url - Current URL: {current_url}")
        
        # Method 6: title - Get page title
        page_title = driver.title
        print(f"✅ driver.title - Page title: {page_title}")
        
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_6_element_interaction():
    """
    SECTION 6: Element Interaction
    ==============================
    
    How to find and interact with web elements.
    """
    print("\n" + "=" * 60)
    print("SECTION 6: Element Interaction")
    print("=" * 60)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        print("\n6. Element interaction methods:")
        
        # Navigate to a page with forms
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        time.sleep(2)
        
        # Find element by different selectors
        search_box = driver.find_element(By.NAME, "q")
        print("✅ driver.find_element() - Found search box by name")
        
        # Clear existing text
        search_box.clear()
        print("✅ element.clear() - Cleared search box")
        
        # Send keys (type text)
        search_box.send_keys("Selenium WebDriver tutorial")
        print("✅ element.send_keys() - Typed search query")
        time.sleep(1)
        
        # Submit form
        search_box.submit()
        print("✅ element.submit() - Submitted search form")
        time.sleep(2)
        
        # Click on element
        try:
            first_result = driver.find_element(By.CSS_SELECTOR, "h3")
            first_result.click()
            print("✅ element.click() - Clicked on first result")
            time.sleep(2)
        except:
            print("⚠️ Could not click on first result")
        
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_7_wait_strategies():
    """
    SECTION 7: Wait Strategies
    ==========================
    
    How to wait for elements to load and be interactive.
    """
    print("\n" + "=" * 60)
    print("SECTION 7: Wait Strategies")
    print("=" * 60)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        print("\n7. Wait strategies:")
        
        # Create WebDriverWait instance
        wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds
        print("✅ WebDriverWait created with 10-second timeout")
        
        # Navigate to a page
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        
        # Wait for element to be present
        search_box = wait.until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        print("✅ wait.until(presence_of_element_located) - Search box is present")
        
        # Wait for element to be clickable
        search_box = wait.until(
            EC.element_to_be_clickable((By.NAME, "q"))
        )
        print("✅ wait.until(element_to_be_clickable) - Search box is clickable")
        
        # Wait for element to be visible
        search_box = wait.until(
            EC.visibility_of_element_located((By.NAME, "q"))
        )
        print("✅ wait.until(visibility_of_element_located) - Search box is visible")
        
        # Interact with the element
        search_box.clear()
        search_box.send_keys("Selenium waits")
        search_box.submit()
        print("✅ Submitted search")
        
        # Wait for page to load (URL to change)
        wait.until(lambda driver: "search" in driver.current_url)
        print("✅ wait.until(lambda) - Page loaded after search")
        
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_8_error_handling():
    """
    SECTION 8: Error Handling
    =========================
    
    How to handle common WebDriver errors and exceptions.
    """
    print("\n" + "=" * 60)
    print("SECTION 8: Error Handling")
    print("=" * 60)
    
    print("\n8. Error handling examples:")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        # Example 1: Handle NoSuchElementException
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        
        try:
            # Try to find an element that doesn't exist
            non_existent = driver.find_element(By.ID, "this-element-does-not-exist")
        except NoSuchElementException:
            print("✅ NoSuchElementException handled - Element not found")
        
        # Example 2: Handle TimeoutException
        wait = WebDriverWait(driver, 2)  # Short timeout for demo
        try:
            wait.until(EC.presence_of_element_located((By.ID, "non-existent")))
        except TimeoutException:
            print("✅ TimeoutException handled - Element didn't appear in time")
        
        # Example 3: Handle ElementClickInterceptedException
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("test")
        
        try:
            # Try to click on an element that might be intercepted
            search_box.click()
        except ElementClickInterceptedException:
            print("✅ ElementClickInterceptedException handled - Element click was intercepted")
        
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def section_9_best_practices():
    """
    SECTION 9: Best Practices
    =========================
    
    Best practices for using WebDriver effectively.
    """
    print("\n" + "=" * 60)
    print("SECTION 9: Best Practices")
    print("=" * 60)
    
    print("\n9. Best practices:")
    
    # Best Practice 1: Always use try-finally to ensure browser cleanup
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        print("✅ Best Practice 1: WebDriver created in try block")
        
        driver.get("https://www.google.com")
        print("✅ Navigated to Google")
        
        # Best Practice 2: Use explicit waits instead of time.sleep()
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
        print("✅ Best Practice 2: Used explicit wait instead of time.sleep()")
        
        # Best Practice 3: Use meaningful variable names
        search_input_field = driver.find_element(By.NAME, "q")
        print("✅ Best Practice 3: Used meaningful variable name")
        
        # Best Practice 4: Handle exceptions gracefully
        try:
            search_input_field.send_keys("Selenium best practices")
            search_input_field.submit()
            print("✅ Best Practice 4: Graceful exception handling")
        except Exception as e:
            print(f"⚠️ Search failed: {e}")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
    finally:
        # Best Practice 5: Always close the browser
        if driver:
            driver.quit()
            print("✅ Best Practice 5: Browser closed in finally block")

def section_10_advanced_features():
    """
    SECTION 10: Advanced Features
    =============================
    
    Advanced WebDriver features and capabilities.
    """
    print("\n" + "=" * 60)
    print("SECTION 10: Advanced Features")
    print("=" * 60)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        
        print("\n10. Advanced features:")
        
        # Feature 1: Execute JavaScript
        driver.get("https://www.google.com")
        driver.execute_script("alert('Hello from Selenium!');")
        print("✅ driver.execute_script() - Executed JavaScript alert")
        time.sleep(2)
        
        # Close alert
        alert = driver.switch_to.alert
        alert.accept()
        print("✅ driver.switch_to.alert.accept() - Closed alert")
        
        # Feature 2: Take screenshot
        driver.save_screenshot("webdriver_tutorial_screenshot.png")
        print("✅ driver.save_screenshot() - Screenshot saved")
        
        # Feature 3: Get page source
        page_source = driver.page_source
        print(f"✅ driver.page_source - Page source length: {len(page_source)} characters")
        
        # Feature 4: Get window size and position
        window_size = driver.get_window_size()
        print(f"✅ driver.get_window_size() - Window size: {window_size}")
        
        window_position = driver.get_window_position()
        print(f"✅ driver.get_window_position() - Window position: {window_position}")
        
        # Feature 5: Manage cookies
        cookies = driver.get_cookies()
        print(f"✅ driver.get_cookies() - Found {len(cookies)} cookies")
        
        # Feature 6: Switch to different windows/frames
        driver.execute_script("window.open('https://www.python.org');")
        print("✅ driver.execute_script() - Opened new window")
        
        # Switch to new window
        driver.switch_to.window(driver.window_handles[-1])
        print("✅ driver.switch_to.window() - Switched to new window")
        
        # Close new window and switch back
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        print("✅ driver.close() and switch back - Closed new window")
        
        driver.quit()
        print("✅ Browser closed")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """
    Main function to run all tutorial sections
    """
    print("🚀 COMPLETE SELENIUM WEBDRIVER TUTORIAL")
    print("=" * 60)
    print("This tutorial covers everything about: from selenium import webdriver")
    print("=" * 60)
    
    # Run all sections
    sections = [
        section_1_basic_webdriver,
        section_2_webdriver_manager,
        section_3_different_browsers,
        section_4_webdriver_options,
        section_5_navigation_methods,
        section_6_element_interaction,
        section_7_wait_strategies,
        section_8_error_handling,
        section_9_best_practices,
        section_10_advanced_features
    ]
    
    for section in sections:
        try:
            section()
            time.sleep(1)  # Brief pause between sections
        except KeyboardInterrupt:
            print("\n\n⚠️ Tutorial interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Error in section: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 TUTORIAL COMPLETED!")
    print("=" * 60)
    print("You now know everything about Selenium WebDriver!")
    print("Key takeaways:")
    print("1. Always use webdriver-manager for automatic driver management")
    print("2. Use explicit waits instead of time.sleep()")
    print("3. Always close the browser in a finally block")
    print("4. Handle exceptions gracefully")
    print("5. Use meaningful variable names and comments")

if __name__ == "__main__":
    main() 