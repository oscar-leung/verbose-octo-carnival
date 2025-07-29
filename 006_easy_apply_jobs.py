import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import pyautogui
from dotenv import load_dotenv
import os

# Load variables from .env
load_dotenv()


username = os.getenv("LINKIN_USERNAME")
password = os.getenv("LINKIN_PASSWORD")



def print_element_info(element):
    """Print detailed information about a web element."""
    print(f"Tag Name: {element.tag_name}")
    print(f"Text: {element.text}")
    print(f"ID: {element.get_attribute('id')}")
    print(f"Class: {element.get_attribute('class')}")
    print(f"Name: {element.get_attribute('name')}")
    print(f"Type: {element.get_attribute('type')}")
    print(f"Value: {element.get_attribute('value')}")
    print(f"Href: {element.get_attribute('href')}")
    print(f"Src: {element.get_attribute('src')}")
    print(f"Is Displayed: {element.is_displayed()}")
    print(f"Is Enabled: {element.is_enabled()}")
    print(f"Is Selected: {element.is_selected()}")
    print(f"Location: {element.location}")
    print(f"Size: {element.size}")
    print(f"Rect: {element.rect}")

    # Additional attributes and properties
    print(f"Accessibility Role: {element.get_attribute('role')}")
    print(f"Placeholder: {element.get_attribute('placeholder')}")
    print(f"Aria-Label: {element.get_attribute('aria-label')}")
    print(f"Aria-Describedby: {element.get_attribute('aria-describedby')}")
    print(f"Aria-Checked: {element.get_attribute('aria-checked')}")
    print(f"Tab Index: {element.get_attribute('tabindex')}")
    print(f"Custom Attributes: {[attr for attr in element.get_attribute('outerHTML').split() if attr.startswith('data-')]}")
def click_button(xpath):
    """Helper function to scroll to and click a button by its XPath."""
    try:
        # Locate the button
        button = driver.find_element(By.XPATH, xpath)

        # Scroll to the button to ensure it's visible
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        # Click the button
        button.click()
        time.sleep(1)
        print(f"Clicked button with XPath: {xpath}")
    except NoSuchElementException:
        print(f"Button not found: {xpath}")
    except Exception as e:
        print(f"Error clicking button with XPath: {xpath}. Error: {e}")
def populate_additional_questions():

    try:
        # Locate the label for the dropdown
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), '3-6 years of experience in software testing with a strong focus on both manual and automated testing?')]")

        # Locate the select element
        experience_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4040026475-7524263970-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(experience_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")
        
        print("Selected 'Yes' for the question about 3-6 years of experience in software testing.")

    except NoSuchElementException:
        print("No such question: 3-6 years of experience in software testing with a strong focus on both manual and automated testing?")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to select an option for the experience question.")

    try:
        # Locate the label for the dropdown
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Proficiency in test automation tools and frameworks (e.g., Selenium, TestNG, Cucumber)?')]")

        # Locate the select element
        automation_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4040026475-7524263962-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(automation_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")
        
        print("Selected 'Yes' for the question about proficiency in test automation tools and frameworks.")

    except NoSuchElementException:
        print("No such question: Proficiency in test automation tools and frameworks (e.g., Selenium, TestNG, Cucumber)?")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to select an option for the automation proficiency question.")
    
    try:
        # Locate the label for the dropdown
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Experience with scripting languages such as Java, Python, or JavaScript for writing automated test scripts?')]")

        # Locate the select element
        scripting_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4040026475-7524264018-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(scripting_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")
        
        print("Selected 'Yes' for the question about experience with scripting languages.")

    except NoSuchElementException:
        print("No such question: Experience with scripting languages such as Java, Python, or JavaScript for writing automated test scripts?")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to select an option for the scripting languages question.")


    try:
        # Locate the fieldset by matching the question text within the legend
        fieldset = driver.find_element(By.XPATH, "//fieldset[.//span[contains(text(), 'Are you willing to take a drug test, in accordance with local law/regulations?')]]")
        
        # Click the label that is associated with the input radio button of the given value (Yes)
        label = fieldset.find_element(By.XPATH, ".//label[@for=//input[@value='Yes']/@id]")
        label.click()
        
        print("Selected the option 'Yes' for question 'Are you willing to take a drug test, in accordance with local law/regulations?'")

    except NoSuchElementException:
        print("Could not find the radio button with value 'Yes' for the specified question.")
    except ElementClickInterceptedException:
        print("Element click intercepted for 'Yes' on the specified question.")
    try:
        # Locate the label for the dropdown
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Familiarity with version control systems (e.g., Git, SVN) and CI/CD pipelines?')]")

        # Locate the select element
        version_control_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4040026475-7524264002-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(version_control_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")
        
        print("Selected 'Yes' for the question about familiarity with version control systems and CI/CD pipelines.")

    except NoSuchElementException:
        print("No such question: Familiarity with version control systems (e.g., Git, SVN) and CI/CD pipelines?")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to select an option for the version control question.")

    try:
        # Locate the label for the dropdown
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Experience with performance testing tools (e.g., JMeter)?')]")
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Experience with performance testing tools (e.g., JMeter)?')]")

        # Locate the select element
        performance_testing_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4040026475-7524264010-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(performance_testing_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")
        
        print("Selected 'Yes' for the question about experience with performance testing tools.")

    except NoSuchElementException:
        print("No such question: Experience with performance testing tools (e.g., JMeter)?")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to select an option for the performance testing question.")


    try:
        # Locate the label by its text
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Python')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        python_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        python_experience_input.clear()
        python_experience_input.send_keys("3")  # Enter your years of experience
    except NoSuchElementException:
        print("Python work experience label or input field not found")
    try:
        # Locate the label by its text
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with JavaScript?')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        javascript_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        javascript_experience_input.clear()
        javascript_experience_input.send_keys("3")  # Enter your years of experience

        print("Entered '3' years of experience for JavaScript.")

    except NoSuchElementException:
        print("JavaScript work experience label or input field not found.")
    except ElementClickInterceptedException:
        print("Element click intercepted while trying to enter JavaScript experience.")

    try:
        # Locate the label by its text
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Silicon Validation')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        silicon_validation_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        silicon_validation_input.clear()
        silicon_validation_input.send_keys("0")  # Enter your years of experience for Silicon Validation
    except NoSuchElementException:
        print("Silicon Validation label or input field not found")
    
    try:
        # Locate the label by its text for SerDes experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with SerDes')]")
        input_id = label.get_attribute("for")
        serdes_experience_input = driver.find_element(By.ID, input_id)
        serdes_experience_input.clear()
        serdes_experience_input.send_keys("0")  # Enter your years of experience with SerDes
    except NoSuchElementException:
        print("SerDes work experience label or input field not found")

    try:
        # Locate the label by its text for Hardware Bring-up experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Hardware Bring-up')]")
        input_id = label.get_attribute("for")
        hardware_bringup_input = driver.find_element(By.ID, input_id)
        hardware_bringup_input.clear()
        hardware_bringup_input.send_keys("0")  # Enter your years of experience with Hardware Bring-up
    except NoSuchElementException:
        print("Hardware Bring-up work experience label or input field not found")

    try:
        # Locate the label by its text for PCIe experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with PCIe')]")
        input_id = label.get_attribute("for")
        pcie_experience_input = driver.find_element(By.ID, input_id)
        pcie_experience_input.clear()
        pcie_experience_input.send_keys("0")  # Enter your years of experience with PCIe
    except NoSuchElementException:
        print("PCIe work experience label or input field not found")

    try:
        # Locate the label by its text for Information Technology experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of Information Technology experience do you currently have')]")
        input_id = label.get_attribute("for")
        it_experience_input = driver.find_element(By.ID, input_id)
        it_experience_input.clear()
        it_experience_input.send_keys("4")  # Enter your years of Information Technology experience
    except NoSuchElementException:
        print("Information Technology experience label or input field not found")

    try:
        # Locate the label by its text for Embedded Testing experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How Many years of experience do you have in Embedded Testing')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        embedded_testing_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        embedded_testing_input.clear()
        embedded_testing_input.send_keys("0")  # Enter your years of experience in Embedded Testing
    except NoSuchElementException:
        print("Embedded Testing experience label or input field not found")
    try:
        # Locate the label by its text for Site Reliability Engineering experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Site Reliability Engineering')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        sre_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        sre_experience_input.clear()
        sre_experience_input.send_keys("0")  # Enter your years of experience with Site Reliability Engineering
    except NoSuchElementException:
        print("Site Reliability Engineering experience label or input field not found")

    try:
        # Locate the label by its text for System Admin or Windows Admin experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of experience do you have as a System Admin or Windows Admin in an on prem environment')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        sysadmin_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        sysadmin_experience_input.clear()
        sysadmin_experience_input.send_keys("0")  # Enter your years of experience as a System/Windows Admin in on-prem environment
    except NoSuchElementException:
        print("System/Windows Admin experience label or input field not found")

    try:
        # Locate the label by its text for Hardware Testing experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Hardware Testing')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        hardware_testing_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        hardware_testing_input.clear()
        hardware_testing_input.send_keys("1")  # Enter your years of experience with Hardware Testing
    except NoSuchElementException:
        print("Hardware Testing experience label or input field not found")

    try:
        # Locate the label by its text for C Programming Language experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with C (Programming Language)')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        c_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        c_experience_input.clear()
        c_experience_input.send_keys("1")  # Enter your years of experience with C (Programming Language)
    except NoSuchElementException:
        print("C Programming Language experience label or input field not found")

    try:
        # Locate the label by its text for Firmware experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Firmware')]")

        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")

        # Locate the input field using the 'id' from the 'for' attribute of the label
        firmware_experience_input = driver.find_element(By.ID, input_id)

        # Clear the field and enter the number of years of experience
        firmware_experience_input.clear()
        firmware_experience_input.send_keys("0")  # Enter 0 years of experience with Firmware
    except NoSuchElementException:
        print("Firmware experience label or input field not found")
    try:
        # Locate the label by its text for WiFi experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with WiFi')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        wifi_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        wifi_experience_input.clear()
        wifi_experience_input.send_keys("0")  # Enter 0 years of experience with WiFi
    except NoSuchElementException:
        print("WiFi experience label or input field not found")

    try:
        # Locate the label by its text for Powershell experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Powershell')]")

        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")

        # Locate the input field using the 'id' from the 'for' attribute of the label
        powershell_experience_input = driver.find_element(By.ID, input_id)

        # Clear the field and enter the number of years of experience
        powershell_experience_input.clear()
        powershell_experience_input.send_keys("1")  # Enter 1 year of experience with Powershell
    except NoSuchElementException:
        print("Powershell experience label or input field not found")

    try:
        # Locate the label by its text
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with AutoCAD?')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        auto_cad_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        auto_cad_experience_input.clear()
        auto_cad_experience_input.send_keys("2")  # Enter your years of experience for AutoCAD
    except NoSuchElementException:
        print("AutoCAD experience label or input field not found.")
    

    try:
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Do you live in North Carolina or are you willing to relocate?')][1]")
        # Locate the select element
        relocation_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4033371245-10429370260-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(relocation_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("No")
    except NoSuchElementException:
        print("No such question: Do you live in North Carolina or are you willing to relocate?")
    try:

        # Locate the label for the question
        label = driver.find_element(By.XPATH, "//label//span[contains(text(), 'Do you have experience testing Web and Mobile Application?')][1]")

        # Locate the select element
        experience_select = driver.find_element(By.XPATH, '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4037506836-10672076556-multipleChoice"]')

        # Use the Select class to interact with the dropdown
        select = Select(experience_select)

        # Select the "Yes" option based on the text
        select.select_by_visible_text("Yes")

        print("Selected 'Yes' for the question.")

    except NoSuchElementException as e:
        print(f"An element was not found: {e}")

    try:
        # Locate the label for the question
        label_xpath = "//label//span[contains(text(), 'Do you have experience testing any Banking Product/Payment?')]"
        label = driver.find_element(By.XPATH, label_xpath)

        # Locate the select element for the answer
        experience_select_xpath = '//*[@id="text-entity-list-form-component-formElement-urn-li-jobs-applyformcommon-easyApplyFormElement-4037506836-10672076564-multipleChoice"]'
        experience_select = driver.find_element(By.XPATH, experience_select_xpath)

        # Interact with the dropdown using the Select class
        select = Select(experience_select)

        # Select the "No" option
        select.select_by_visible_text("No")

        print("Successfully selected 'No' for the question.")

    except NoSuchElementException as e:
        print(f"Error: Unable to find the specified element. Please check if the XPath is correct or if the element is present in the DOM. Details: {e}")


    try:
        # Locate the label by its text
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Appium?')]")
        
        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        appium_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        appium_experience_input.clear()
        appium_experience_input.send_keys("0")  # Enter 0 years of experience for Appium

        print("Successfully entered '0' years of experience for Appium.")

    except NoSuchElementException:
        print("Appium experience label or input field not found.")
    
    try:
        # Locate the label for Oscilloscope experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Oscilloscope')]")
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        oscilloscope_experience_input = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        oscilloscope_experience_input.clear()
        oscilloscope_experience_input.send_keys("0")  # Enter your years of experience
    except NoSuchElementException:
        print("Oscilloscope work experience label or input field not found")

    try:
        # Locate the label for Reliability experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with Reliability')]")
        input_id = label.get_attribute("for")

        # Locate the input field using the 'id' from the 'for' attribute of the label
        reliability_experience_input = driver.find_element(By.ID, input_id)

        # Clear the field and enter the number of years of experience
        reliability_experience_input.clear()
        reliability_experience_input.send_keys("0")  # Enter your years of experience
    except NoSuchElementException:
        print("Reliability work experience label or input field not found")

    try:
        # Locate the label for C++ experience
        label = driver.find_element(By.XPATH, "//label[contains(text(), 'How many years of work experience do you have with C++?')]")
        input_id = label.get_attribute("for")

        # Locate the input field using the 'id' from the 'for' attribute of the label
        cpp_experience_input = driver.find_element(By.ID, input_id)

        # Clear the field and enter the number of years of experience
        cpp_experience_input.clear()
        cpp_experience_input.send_keys("1")  # Entering 1 year of experience
        print("Entered 1 year of C++ experience.")

    except NoSuchElementException:
        print("C++ work experience label or input field not found")
def click_next_button(driver, max_clicks=5):
    """
    Click the 'Next' button a specified number of times.

    Args:
        driver: The Selenium WebDriver instance.
        max_clicks (int): The maximum number of clicks allowed on the 'Next' button.
    """
    click_count = 0  # Track the number of clicks

    while click_count < max_clicks:
        try:
            # Use WebDriverWait to wait until the 'Next' button is clickable
            next_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Next']"))
            )
            next_button.click()  # Click the 'Next' button
            click_count += 1  # Increment click count
            print(f"Clicked the 'Next' button. Click count: {click_count}")

            # Optional: Wait for a moment to allow the next page to load
            time.sleep(1)

        except NoSuchElementException:
            print("The 'Next' button is not found, exiting loop...")
            break  # Exit the loop if no more 'Next' buttons are found

        except ElementClickInterceptedException:
            print("Next button click was intercepted. Retrying...")
            time.sleep(1)  # Wait before retrying to click

    # If the max number of clicks is reached, print a message and proceed
    if click_count >= max_clicks:
        print(f"Max clicks ({max_clicks}) reached. Moving on...")
def enter_experience(driver, label_text, experience_years):
    """
    Function to enter the number of years of experience into the input field associated
    with the specified label text.

    :param driver: The Selenium WebDriver instance.
    :param label_text: The text of the label associated with the input field.
    :param experience_years: The number of years of experience to input.
    """
    try:
        # Locate the label by its text
        # label = driver.find_element(By.XPATH, f"//label[contains(text(), '{label_text}')]")
        label = driver.find_element(By.XPATH, f"//label[.//span[contains(normalize-space(), '{label_text}')]]")
        # label = driver.find_element(By.XPATH, f"//label[.//span[contains(normalize-space(), 'Location (city)')]]")


        # Get the 'for' attribute of the label, which matches the input field's 'id'
        input_id = label.get_attribute("for")
        
        # Locate the input field using the 'id' from the 'for' attribute of the label
        input_element = driver.find_element(By.ID, input_id)
        
        # Clear the field and enter the number of years of experience
        input_element.clear()
        input_element.send_keys(experience_years)  # Enter the specified years of experience
        print(f"Entered {experience_years} years of experience for '{label_text}'.")

    except NoSuchElementException:
        print(f"Input field not found for label: '{label_text}'.")
def select_radio_button(driver, question_text, option_value):
    """
    Function to select a radio button option for a given question in a form.

    :param driver: The WebDriver instance (e.g., Chrome, Firefox).
    :param question_text: The question text to locate the correct fieldset.
    :param option_value: The value of the radio button to select (e.g., 'Yes', 'No').
    :return: None
    """
    try:
        # Locate the fieldset by matching the question text within the legend or span
        fieldset = driver.find_element(By.XPATH, f"//fieldset[.//span[contains(text(), \"{question_text}\")]]")

        # Find the label with the option text (Yes/No)
        label = fieldset.find_element(By.XPATH, f".//label[normalize-space()='No']")
        

        # Click the label to select the radio button
        label.click()

        print(f"Selected the option '{option_value}' for question '{question_text}'.")

    except NoSuchElementException:
        print(f"Could not find the radio button with value '{option_value}' for the question '{question_text}'.")
    except ElementClickInterceptedException:
        print(f"Element click intercepted for '{option_value}' on the question '{question_text}'.")
def select_dropdown_option(driver, question_text, option_value):

    """
    Function to select an option from a dropdown based on the question text.

    :param driver: The WebDriver instance (e.g., Chrome, Firefox).
    :param question_text: The question text to locate the correct dropdown.
    :param option_value: The visible text of the option to select from the dropdown.
    :return: None
    """
    try:
        # Use double quotes in the XPath to handle apostrophes or special characters in the question_text
        label = driver.find_element(By.XPATH, f"//label[contains(., \"{question_text}\")]")

        # Get the 'for' attribute of the label, which links to the select element's id
        select_id = label.get_attribute("for")
        
        # Locate the select dropdown using the id from the label's 'for' attribute
        select_element = driver.find_element(By.ID, select_id)
        
        # Use Select class to interact with the dropdown
        select = Select(select_element)
        
        # Select the desired option by visible text
        select.select_by_visible_text(option_value)
        
        print(f"Successfully selected '{option_value}' for the question '{question_text}'.")

    except NoSuchElementException:
        print(f"Unable to locate the question or dropdown for '{question_text}'.")
    except TimeoutException:
        print("The page took too long to load or the dropdown did not appear in time.")
def fill_input_field(driver, locator_type, locator_value, text, timeout=1):
    """
    Function to fill an input field safely.

    :param driver: Selenium WebDriver instance
    :param locator_type: Locator type (By.ID, By.XPATH, By.NAME, etc.)
    :param locator_value: The actual locator string
    :param text: Text to input
    :param timeout: Max time to wait for element (default: 10 seconds)
    """
    try:
        # Wait until the input field is visible & enabled
        input_field = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((locator_type, locator_value))
        )
        input_field.clear()  # Clear existing text
        input_field.send_keys(text)  # Enter new text
        time.sleep(1)
        input_field.send_keys(Keys.RETURN)  # Press Enter
        print(f"Filled input field: {locator_value} with '{text}'")
    except Exception as e:
        print(f"Error filling input field {locator_value}: {e}")

def easy_apply():
    # Start the easy apply process
    click_button("//button[contains(@class, 'jobs-apply-button')]")

    # Job search safetly reminder
    click_button("//button[normalize-space()='Continue applying']")
    
    # Contact Info
    click_button("//button[@aria-label='Continue to next step']")
    enter_experience(driver, "City", "Santa Clara")
    enter_experience(driver, "State or Province", "California")
    enter_experience(driver, "Zip/Postal Code", "95050")
    enter_experience(driver, "Location (city)", "Santa Clara County, California, United States")
    select_dropdown_option(driver, "Country", "UNITED STATES")

    # Resume Info
    click_button("//button[@aria-label='Continue to next step']")

    # Additional Questions
    click_button("//button[@aria-label='Continue to next step']")

    # Diversity
    click_button("//button[@aria-label='Continue to next step']")

    # Work Auth
    select_radio_button(driver, "Will you now, or in the future, require sponsorship for employment visa status (e.g. H-1B visa status)?", "No")
    select_radio_button(driver, "Are you legally authorized to work in the US without restriction?", "No")
    select_radio_button(driver, "Will you now or in the future require visa sponsorship or a visa transfer?", "No")
    click_button("//button[@aria-label='Review your application']")



    # # populate_additional_questions() 
    # for i in range(4):
    #     click_button("//button[normalize-space()='Next']")
    #     print(f"Clicked Next button {i + 1} times.")

    # home address
    
    # try:
    #     input_element = driver.find_element(By.XPATH, "//input[contains(@id, 'HOME-CITY')]")
    #     input_element.send_keys("Alameda, California, United States")
    #     click_button("//h3[@class='t-16 t-bold']")
    #     for i in range(4):
    #         click_button("//button[normalize-space()='Next']")
    #         print(f"Clicked Next button {i + 1} times.")
    # except NoSuchElementException:
    #     print("Input field not found")
    

    # data consent (1)


    # addtional questions – input fields

    enter_experience(driver, "How many years of work experience do you have with Liquibase?", "1")
    enter_experience(driver, "How many years of work experience do you have with JavaScript Frameworks?", "2")
    enter_experience(driver, "How many years of work experience do you have with Vanilla JavaScript?", "2")
    enter_experience(driver, "How many years of Overall work experience do you have?", "5")
    enter_experience(driver, "How many years of work experience do you have with Load Testing?", "1")
    enter_experience(driver, "How many years of experience do you have creating Physical Design methodology flows?", "1")
    enter_experience(driver, "What is your expected hourly pay on W2 basis? (You will work with us as a direct employee, not c2c /1099)", "40")
    enter_experience(driver, "How many years of experience do you have with DevOps & CI/CD (Git, Jenkins, Docker)?", "1")
    enter_experience(driver, "How many years of experience do you have with AWS (Serverless/Lambda)?", "1")
    enter_experience(driver, "How many years of experience do you have with React/Angular.js?", "1")
    enter_experience(driver, "How many years of experience do you have in designing APIs with Node.js?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Driven Testing?", "1")
    enter_experience(driver, "How many years of Hospitals and Health Care experience do you currently have?", "1")
    enter_experience(driver, "How many years of work experience do you have with RCM?", "1")
    enter_experience(driver, "How many years of work experience do you have with Business-to-Business (B2B)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Product Management?", "1")
    enter_experience(driver, "How many years of work experience do you have with Marketo?", "1")
    enter_experience(driver, "How many years of Gen AI experience do you have?", "1")
    enter_experience(driver, "How many years of work experience do you have with IBM Db2?", "1")
    enter_experience(driver, "How many years of work experience do you have with GraphQL?", "1")
    enter_experience(driver, "How many years of work experience do you have with NumPy?", "2")
    enter_experience(driver, "How many years of work experience do you have with Vertex?", "1")
    enter_experience(driver, "Proficiency in software development languages such as Python, C++, Java ", "4")
    enter_experience(driver, "Knowledge of profilers like Perf, PyPerf, Gprofiler, Java Async Profiler, Dynalog , etc", "1")
    enter_experience(driver, "How many years of experience do you have working on image parsing?", "1")
    enter_experience(driver, "How many years of experience do you have working as Full Stack engineer?", "1")
    enter_experience(driver, "How many years of work experience do you have with Sarbanes-Oxley Act?", "0")
    enter_experience(driver, "How many years of work experience do you have with Finance?", "1")
    enter_experience(driver, "How many years of work experience do you have with Business Strategy?", "0")
    enter_experience(driver, "How many years of work experience do you have with White Box Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with Payment Gateways?", "0")
    enter_experience(driver, "How many years of work experience do you have with Android Framework?", "1")
    enter_experience(driver, "How many years of work experience do you have with Automated Software Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with CRM Software?", "2")
    enter_experience(driver, "How many years of work experience do you have with Network Troubleshooting?", "1")
    enter_experience(driver, "How many years of work experience do you have with CRM Integration?", "1")
    enter_experience(driver, "How many years of work experience do you have with Databricks Products?", "1")
    enter_experience(driver, "How many years of work experience do you have with Test Development?", "3")
    enter_experience(driver, "How many years of work experience do you have with Machine Tools?", "1")
    enter_experience(driver, "How many years of work experience do you have with Red Hat Linux?", "1")
    enter_experience(driver, "How many years of work experience do you have with Information Gathering?", "2")
    enter_experience(driver, "How many years of work experience do you have with Web 2.0?", "1")
    enter_experience(driver, "How many years of work experience do you have with AJAX?", "1")
    enter_experience(driver, "How many years of experience do you have in technology and IT customer support?", "2")
    enter_experience(driver, "How many years of work experience do you have with Software Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with React/React Native?", "1")
    enter_experience(driver, "How many years of work experience do you have with Django?", "1")
    enter_experience(driver, "How many years of work experience do you have with Jenkins?", "1")
    enter_experience(driver, "How many years of experience do you have with Android Automation Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with DevOps?", "1")
    enter_experience(driver, "How many years of work experience do you have with SAP Sales & Distribution?", "0")
    enter_experience(driver, "How many years of work experience do you have with SAP S/4HANA?", "2")
    enter_experience(driver, "How many years of work experience do you have with Android Development?", "1")
    enter_experience(driver, "How many years of work experience do you have with iOS Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Agile & Waterfall Methodologies?", "3")
    enter_experience(driver, "How many years of Analyst experience do you currently have?", "1")
    enter_experience(driver, "Do you have Healthcare experience?", "1")
    enter_experience(driver, "Experience with web technologies , middleware such as WebLogic/WebSphere and popular RDBMS systems?", "1")
    enter_experience(driver, "How many years of work experience do you have with Software as a Service (SaaS)?", "2")
    enter_experience(driver, "How many years of experience do you have with Android Device Testing?", "2")
    enter_experience(driver, "How many years of work experience do you have with ETL Testing?", "0")
    enter_experience(driver, "How many years of work experience do you have with Salesforce Marketing Cloud?", "0")
    enter_experience(driver, "How many years of work experience do you have with Java?", "6")
    enter_experience(driver, "How many years of work experience do you have with iOS Development?", "1")
    enter_experience(driver, "How many years of work experience do you have with Object-Oriented Programming (OOP)?", "3")
    enter_experience(driver, "How many years of work experience do you have with Data Engineering?", "1")
    enter_experience(driver, "How many years of work experience do you have with Amazon S3?", "1")
    enter_experience(driver, "How many years of work experience do you have with Apache Spark?", "0")
    enter_experience(driver, "How many years of work experience do you have with ETL Tools?", "0")
    enter_experience(driver, "How many years of work experience do you have with AWS Lambda?", "0")
    enter_experience(driver, "How many years of experience do you have working in Agile Team?", "3")
    enter_experience(driver, "How many years of experience do you have as a React Developer?", "1")
    enter_experience(driver, "How many years of work experience do you have with Azure DevOps Server?", "1")
    enter_experience(driver, "How many years of work experience do you have with Databases?", "1")
    enter_experience(driver, "How many years of work experience do you have with JavaServer Pages (JSP)?", "0")
    enter_experience(driver, "How many years of work experience do you have with Spring Framework?", "1")
    enter_experience(driver, "How many years of work experience do you have with Application Development?", "1")
    enter_experience(driver, "How many years of work experience do you have with Next.js?", "1")
    enter_experience(driver, "How many years of work experience do you have with Android Jetpack?", "0")
    enter_experience(driver, "How many years of work experience do you have with Quality Assurance?", "3")
    enter_experience(driver, "How many years of work experience do you have with Salesforce.com Consulting?", "1")
    enter_experience(driver, "How many years of Legal Services experience do you currently have?", "0")
    enter_experience(driver, "How many years of work experience do you have with Mechanical Testing?", "0")
    enter_experience(driver, "How many years of work experience do you have with Thermal Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Test Design?", "3")
    enter_experience(driver, "How many years of work experience do you have with Connectivity?", "1")
    enter_experience(driver, "How many years of work experience do you have with Mobile Security?", "1")
    enter_experience(driver, "How many years of work experience do you have with Regression Testing?", "4")
    enter_experience(driver, "How many years of work experience do you have with Benefits Negotiation?", "1")
    enter_experience(driver, "How many years of work experience do you have with Claims?", "1")
    enter_experience(driver, "How many years of work experience do you have with GPGPU?", "0")
    enter_experience(driver, "How much experience you have working with Java Full Stack Development?", "1")
    enter_experience(driver, "How many years of experience do you have in software programming?", "3")
    enter_experience(driver, "How many years of work experience do you have with Angular", "1")
    enter_experience(driver, "How many years of work experience do you have with Agile Software Development?", "3")
    enter_experience(driver, "How many years of work experience do you have with Oracle Enterprise Resource Planning (ERP) Cloud?", "0")
    enter_experience(driver, "How many years of work experience do you have with ADP Payroll?", "0")
    enter_experience(driver, "How many years of work experience do you have with Powershell?", "1")
    enter_experience(driver, "Rest assured experience (Years)", "1")
    enter_experience(driver, "Backend Testing years of experience", "0")
    enter_experience(driver, "How many years of work experience do you have with API Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Mechanical Engineering?", "0")
    enter_experience(driver, "How many years of work experience do you have with Windchill?", "0")
    enter_experience(driver, "How many years of work experience do you have with 3D Computer Aided Design (3D CAD)?", "0")
    enter_experience(driver, "How many years of work experience do you have with Systems Analysis?", "1")
    enter_experience(driver, "How many years of work experience do you have with ITIL Certified?", "0")
    enter_experience(driver, "How many years of work experience do you have with Incident Management?", "1")
    enter_experience(driver, "How many years of work experience do you have with Amazon Athena?", "0")
    enter_experience(driver, "How many years of work experience do you have with Amazon Redshift?", "0")
    enter_experience(driver, "How many years of work experience do you have with SQL?", "1")
    enter_experience(driver, "How many years of work experience do you have with ArcGIS Server?", "0")
    enter_experience(driver, "How many years of work experience do you have with ESRI?", "0")
    enter_experience(driver, "How many years of work experience do you have with Configuration Management?", "1")
    enter_experience(driver, "How many years of work experience do you have with Debugging Code?", "5")
    enter_experience(driver, "How many years of work experience do you have with Customer Facing Roles?", "2")
    enter_experience(driver, "How many years of work experience do you have with .NET Core?", "1")
    enter_experience(driver, "How many years of work experience do you have with PostgreSQL?", "1")
    enter_experience(driver, "How many years of work experience do you have with React Native?", "1")
    enter_experience(driver, "How many years of Defense and Space Manufacturing experience do you currently have?", "2")
    enter_experience(driver, "How many years of work experience do you have with MATLAB?", "1")
    enter_experience(driver, "How many years of work experience do you have with 3D Modeling?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Acquisition?", "1")
    enter_experience(driver, "How many years of work experience do you have with Git?", "5")
    enter_experience(driver, "How many years of work experience do you have with Objective-C?", "1")
    enter_experience(driver, "How many years of work experience do you have with Amazon Web Services (AWS)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Espresso?", "1")
    enter_experience(driver, "How many years of work experience do you have with Android Espresso ?", "1")
    enter_experience(driver, "How many years of work experience do you have with Linux?", "1")
    enter_experience(driver, "How many years of work experience do you have with Embedded Hardware and Software?", "1")
    enter_experience(driver, "How many years of work experience do you have with Programming?", "6")
    enter_experience(driver, "How many years of work experience do you have with Amazon EC2?", "1")
    enter_experience(driver, "How many years of Quality Assurance experience do you currently have?", "4")
    enter_experience(driver, "How many years of work experience do you have with Back-End Web Development?", "1")
    enter_experience(driver, "How many years of work experience do you have with gRPC", "0")
    enter_experience(driver, "How many years of work experience do you have with System Life Cycle", "1")
    enter_experience(driver, "How many years of work experience do you have with System Verification", "1")
    enter_experience(driver, "How many years of work experience do you have with E-Commerce?", "0")
    enter_experience(driver, "How many years of work experience do you have with Point of Sale (POS) Systems?", "0")
    enter_experience(driver, "Your over all IT Experience ?", "1")
    enter_experience(driver, "How many years of work experience do you have with Microservices?", "1")
    enter_experience(driver, "How much experience you are having in Mobile Testing", "1")
    enter_experience(driver, "How many years of work experience do you have with Web Applications?", "1")
    enter_experience(driver, "How many years of work experience do you have with Manual Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with Firmware?", "0")
    enter_experience(driver, "How many years of work experience do you have with Application-Specific Integrated Circuits (ASIC)?", "0")
    enter_experience(driver, "How many years of work experience do you have with NAND Flash?", "0")
    enter_experience(driver, "How many years of work experience do you have with NAND?", "0")
    enter_experience(driver, "How many years of work experience do you have with Interactive Voice Response (IVR)?", "0")
    enter_experience(driver, "How many years of work experience do you have with DDR?", "0")
    enter_experience(driver, "How many years of work experience do you have with Data Processing?", "1")
    enter_experience(driver, "How many years of work experience do you have with React.js?", "1")
    enter_experience(driver, "How many years of work experience do you have with Hydrogen?", "0")
    enter_experience(driver, "How many years of work experience do you have with Shopify?", "1")
    enter_experience(driver, "How many years of work experience do you have with Web Development?", "2")
    enter_experience(driver, "How many years of work experience do you have with Technical Documentation?", "0")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Power Apps?", "1")
    enter_experience(driver, "How many years of work experience do you have with C (Programming Language)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Kotlin?", "1")
    enter_experience(driver, "How many years of work experience do you have with Board Bring-up?", "0")
    enter_experience(driver, "How many years of work experience do you have with I2C?", "0")
    enter_experience(driver, "How many years of work experience do you have with Machine Learning?", "0")
    enter_experience(driver, "How many years of work experience do you have with Enterprise Search?", "1")
    enter_experience(driver, "How many years of work experience do you have with jQuery?", "2")
    enter_experience(driver, "How many years of work experience do you have with Tricentis qTest?", "0")
    enter_experience(driver, "How many years of work experience do you have with Autodesk Software?", "0")
    enter_experience(driver, "How many years of work experience do you have with Market Data?", "0")
    enter_experience(driver, "How many years of work experience do you have with Trading Systems?", "0")
    enter_experience(driver, "How many years of work experience do you have with PLC Programming?", "0")
    enter_experience(driver, "How many years of work experience do you have with TypeScript?", "1")
    enter_experience(driver, "How many years of work experience do you have with Flask?", "0")
    enter_experience(driver, "How many years of work experience do you have with Scripting?", "3")
    enter_experience(driver, "How many years of work experience do you have with Continuous Integration and Continuous Delivery (CI/CD)?", "3")
    enter_experience(driver, "How many years of work experience do you have with Testing Tools?", "3")
    enter_experience(driver, "Python/Powershell", "3")
    enter_experience(driver, "Security Context of Windows Software", "0")
    enter_experience(driver, "How many years of work experience do you have with Network Monitoring Tools?", "1")
    enter_experience(driver, "How many years of work experience do you have with C++?", "1")
    enter_experience(driver, "How many years of work experience do you have with CPU design?", "0")
    enter_experience(driver, "How many years of work experience do you have with Verilog?", "0")
    enter_experience(driver, "How many years of work experience do you have with Playwriting?", "0")
    enter_experience(driver, "How many years of work experience do you have with Test Automation?", "2")
    enter_experience(driver, "How many years of work experience do you have with Cypress?", "1")
    enter_experience(driver, "How many years of work experience do you have with Server?", "1")
    enter_experience(driver, "How many years of work experience do you have with PCIe?", "0")
    enter_experience(driver, "Full Tech Stack: Window Forms, C#, .NET (Classic), SQL, .NET Core, & Angular", "1")
    enter_experience(driver, "Must haves: C#, .NET (Classic), SQL", "1")
    enter_experience(driver, "How many years of work experience do you have with Software Development?", "1")
    enter_experience(driver, "How many years of work experience do you have with Informatica?", "1")
    enter_experience(driver, "How many years of work experience do you have with Apache?", "1")
    enter_experience(driver, "How many years of work experience do you have with Xcode?", "1")
    enter_experience(driver, "How many years of work experience do you have with iOS?", "1")
    enter_experience(driver, "How many years work experience do you have with CI/CD?", "1")
    enter_experience(driver, "How many years of work experience do you have with JavaScript?", "2")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Azure?", "1")
    enter_experience(driver, "How many years experience do you have with Battery Management Systems?", "1")
    enter_experience(driver, "How many years experience do you have with safety critical standards (DO 178/ISO 26262)", "0")
    enter_experience(driver, "How many years of work experience do you have with Xamarin Products?", "0")
    enter_experience(driver, "How many years of work experience do you have with Python (Programming Language)?", "3")
    enter_experience(driver, "How many years of Computer Hardware Manufacturing experience do you currently have?", "0")
    enter_experience(driver, "What is your current location/time zone? This role can be fully remote in the United States or Canada.", "PST")
    enter_experience(driver, "What is your primary mailing address?", "57 Mecartney Rd")
    enter_experience(driver, "How many years of performing manual Quality Assurance experience do you currently have?", "4")
    enter_experience(driver, "How many years of professional experience do you have as a Machine Learning Engineer?", "0")
    enter_experience(driver, "How many years of work experience do you have with Mobile Applications?", "3")
    enter_experience(driver, "Experience in Python/Bash?", "3")
    enter_experience(driver, "Please mention your work authorization status using the following codes: USC: 0 | GC: 1 | GC_EAD: 2 | H1B: 3 | H4: 4 | TN: 5 | OPT - 6 | Others: 7", "0")
    enter_experience(driver, "How many years of DevOps experience in large enterprise environments?", "1")
    enter_experience(driver, "How many years of experience do you have with Kubernetes, including resource definitions and their relationships?", "1")
    enter_experience(driver, "How many years of work experience do you have with Tableau?", "1")
    enter_experience(driver, "How many years of work experience do you have with Cellular Communications?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Structures?", "3")
    enter_experience(driver, "How many years of work experience do you have with Big Data?", "1")
    enter_experience(driver, "How many years of work experience do you have with Spark?", "1")
    enter_experience(driver, "How many years of work experience do you have with Terraform?", "1")
    enter_experience(driver, "How many years of experience have you worked with Lake Formation?", "1")
    enter_experience(driver, "How many years of experience do you have with Identity Access Management? ", "1")
    enter_experience(driver, "How many years of experience do you have doing AWS Data Lake Architecture? ", "1")
    enter_experience(driver, "How may years of experience do you have in setting up and managing AWS Data Lake infrastructure using Terraform?", "0")
    enter_experience(driver, "How many years of experience do you have designing, implementing, and maintaining Terraform configurations in an AWS Data Lake environment?", "0")
    enter_experience(driver, "How many years of work experience do you have with PeopleSoft?", "1")
    enter_experience(driver, "How many years of work experience do you have with PeopleSoft Financial Analytics?", "1")
    enter_experience(driver, "How many years of work experience do you have with Multithreading?", "3")
    enter_experience(driver, "How many years of work experience do you have with Data Storage Technologies?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Warehousing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Marts?", "1")
    enter_experience(driver, "How many years of engineering experience do you have with AWS Cloud Services?", "1")
    enter_experience(driver, "How many years of angular experience do you have?", "2")
    enter_experience(driver, "How many years of work experience do you have with Embedded Software?", "2")
    enter_experience(driver, "How many years of work experience do you have with Generative AI?", "1")
    enter_experience(driver, "How many years of work experience do you have with LangChain?", "1")
    enter_experience(driver, "How many years of work experience do you have with Natural Language Processing (NLP)?", "1")
    enter_experience(driver, "How many years of work experience do you have with CUDA?", "1")
    enter_experience(driver, "How many years of work experience do you have with Kernel Programming?", "1")
    enter_experience(driver, "How many years of work experience do you have with Video Processing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Validation?", "3")
    enter_experience(driver, "Ho many years of working experience do you have with Data Integration?", "1")
    enter_experience(driver, "How many years of experience do you have with testing Cellular technologies (4G/5G/LTE)? ", "1")
    enter_experience(driver, "How many years of work experience do you have with Apache Kafka?", "1")
    enter_experience(driver, "How many years of work experience do you have with Talend?", "1")
    enter_experience(driver, "How many years of work experience do you have with Technical Leadership?", "1")
    enter_experience(driver, "How many years of work experience do you have with Software Engineering Practices?", "3")
    enter_experience(driver, "How many years of work experience do you have with Knowledge Acquisition?", "1")
    enter_experience(driver, "How many years of work experience in L2/L3 OSI layer protocols?", "1")
    enter_experience(driver, "How many years of work experience in GoLang?", "1")
    enter_experience(driver, "How many years of work experience do you have with Okta/SSO ?", "1")
    enter_experience(driver, "How many years of work experience do you have with Network Function Virtualization?", "1")
    enter_experience(driver, "How many years of work experience do you have with Routing Protocols?", "1")
    enter_experience(driver, "How many years of work experience do you have as a QE/QA?", "1")
    enter_experience(driver, "How many years of work experience do you have with Tomcat?", "1")
    enter_experience(driver, "How many years of work experience do you have with Agile Environment?", "3")
    enter_experience(driver, "How many years of experience do you have with NetSuite ERP/CRM?", "1")
    enter_experience(driver, "How many years of work experience do you have with Jira?", "4")
    enter_experience(driver, "How many years of work experience do you have with Datadog?", "1")
    enter_experience(driver, "How many years of work experience do you have with Architecture Development?", "1")
    enter_experience(driver, "How many years of experience in SQL , Type script, Java script?", "1")
    enter_experience(driver, "How many years of work experience do you have with Core Java?", "1")
    enter_experience(driver, "How many years of experience do you have with Golang, Kotlin, No SQL", "1")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Copilot Studio?", "1")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Power Platform?", "1")
    enter_experience(driver, "How many years of work experience do you have with Power BI?", "1")
    enter_experience(driver, "How many years of work experience do you have with Technical Support?", "1")
    enter_experience(driver, "How many years of work experience do you have with Remote Desktop Protocol (RDP)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Intune?", "1")
    enter_experience(driver, "How many years of work experience do you have with QA Automation?", "4")
    enter_experience(driver, "How many years of work experience do you have with Mortgage Industry?", "1")
    enter_experience(driver, "How many years of work experience do you have with SAP Marketing Cloud?", "1")
    enter_experience(driver, "How many years of work experience do you have with Business Analysis?", "1")
    enter_experience(driver, "How many years of work experience do you have with Salesforce.com?", "3")
    enter_experience(driver, "How many years of work experience do you have with MLOps?", "1")
    enter_experience(driver, "How many years of work experience do you have with Representational State Transfer (REST)?", "1")
    enter_experience(driver, "How many years of Automated QA experience do you have?", "3")
    enter_experience(driver, "How many years of software industry experience do you have?", "3")
    enter_experience(driver, "How many years of work experience do you have with Gherkin?", "1")
    enter_experience(driver, "How many years of work experience do you have with Playwright for test automation?", "1")
    enter_experience(driver, "How many years of work experience do you have with Chatbot Testing?", "3")
    enter_experience(driver, "How many years of Pharmaceutical Manufacturing experience do you currently have?", "1")
    enter_experience(driver, "• Proficiency with test management tools such as XRAY, Zephyr, or equivalent tools.", "1")
    enter_experience(driver, "Appium", "1")
    enter_experience(driver, "Mobile Testing", "1")
    enter_experience(driver, "How many years of work experience do you have with Playwright", "1")
    enter_experience(driver, "How many years of work experience do you have with Postman", "1")
    enter_experience(driver, "How many years of Technology, Information and Internet experience do you currently have?", "1")
    enter_experience(driver, "How many years of Gatling experience do you have?", "1")
    enter_experience(driver, "How many years of automation testing do you have?", "3")
    enter_experience(driver, "How many years of experience do you have with VR (Virtual Reality) Platform?", "1")
    enter_experience(driver, "How many years of experience do you have with MR (Mixed Reality) Platform?", "1")
    enter_experience(driver, "How many years of experience do you have with Automation?", "3")
    enter_experience(driver, "How many years of work experience do you have with Maven?", "3")
    enter_experience(driver, "How many years of work experience do you have with COMSEC?", "1")
    enter_experience(driver, "How many years of work experience do you have with Test Planning?", "3")
    enter_experience(driver, "How many years of work experience do you have with Active Directory?", "1")
    enter_experience(driver, "How many years of work experience do you have with Google Analytics?", "1")
    enter_experience(driver, "How many years of work experience do you have with Adobe Lightroom?", "1")
    enter_experience(driver, "How many years of work experience do you have with Go (Programming Language)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Telemetry?", "2")
    enter_experience(driver, "How many years of work experience do you have with Oracle SQL Developer?", "1")
    enter_experience(driver, "How many years of work experience do you have with Jasper Reports?", "1")
    enter_experience(driver, "How many years of work experience do you have with Unit Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with OS X?", "1")
    enter_experience(driver, "How many years of work experience do you have with Front-End Development?", "2")
    enter_experience(driver, "How many years of work experience do you have with Content Management Systems (CMS)?", "2")
    enter_experience(driver, "How many years of work experience do you have with web technologies and frameworks, including Angular 2+/React/VueJS/Node/CSS ?", "3")
    enter_experience(driver, "How many years of work experience do you have with the NetworkExtension framework? ", "1")
    enter_experience(driver, "How many years of work experience do you have with User Interface Design?", "1")
    enter_experience(driver, "How Much exp do you have with Omnistudio ?", "1")
    enter_experience(driver, "How many years of work experience do you have with LoadRunner?", "1")
    enter_experience(driver, "How many years of work experience do you have with Front End Engineering Design (FEED)?", "1")
    enter_experience(driver, "How many years of work experience do you have with Vue.js?", "1")
    enter_experience(driver, "How many years of work experience do you have with Workday?", "1")
    enter_experience(driver, "How many years of work experience do you have with API?", "2")
    enter_experience(driver, "How many years of work experience do you have with Cloud performance Testing?", "1")
    enter_experience(driver, "How many years of work experience do you have with Tailwind CSS?", "1")
    enter_experience(driver, "How many years of work experience do you have with Verification and Validation (V&V)?", "1")
    enter_experience(driver, "How many years of work experience do you have with DO-178B?", "1")
    enter_experience(driver, "How many years of work experience do you have with Life Sciences?", "1")
    enter_experience(driver, "How many years do you have working at an early stage software startup?", "1")
    enter_experience(driver, "Years of experience using the MERN stack", "1")
    enter_experience(driver, "How many years of work experience do you have with Multimodal Prompting?", "1")
    enter_experience(driver, "How many years of work experience do you have with Dynatrace?", "1")
    enter_experience(driver, "What is your hourly expectation as a contractor?", "36")
    enter_experience(driver, "How many years of Management experience do you currently have?", "3")
    enter_experience(driver, "How many years of work experience do you have with pytest?", "1")
    enter_experience(driver, "How many years of work experience do you have with Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with Web Content Accessibility Guidelines (WCAG)?", "3")
    enter_experience(driver, "How many years of work experience do you have with UI Design and Development, with emphasis on web accessibility that supports WCAG 2.1 AA or higher?", "2")
    enter_experience(driver, "How many years of work experience do you have in using JAWS, VoiceOver (macOS and iOS), NVDA, Narrator, ZoomText, and other types of assistive technology software?", "3")
    enter_experience(driver, "How many years of experience do you have in Playwright?", "1")
    enter_experience(driver, "How many years of test automation experience do you currently have?", "3")
    enter_experience(driver, "How many years of Unreal Engine experience do you currently have?", "1")
    enter_experience(driver, "How many years of Unity experience do you currently have?", "1")
    enter_experience(driver, "How many years of work experience do you have with FastAPI?", "1")
    enter_experience(driver, "How many years of experience do you have with Terraform?", "1")
    enter_experience(driver, "How many years of work experience do you have with Embedded Systems?", "1")
    enter_experience(driver, "How many years of work experience do you have with Active DoD Secret Clearance?", "1")
    enter_experience(driver, "How many years of work experience do you have with Google Ads?", "1")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Excel?", "3")
    enter_experience(driver, "How many years of work experience do you have with Azure-based database services.?", "1")
    enter_experience(driver, "How many years of work experience do you have with Data Analytics?", "1")
    enter_experience(driver, "How many years of work experience do you have with PowerBI dashboards.?", "1")
    enter_experience(driver, "How many years of work experience do you have with Inventory Management, Warehouse, Hauling and Investment Recovery.?", "1")
    enter_experience(driver, "How many years have you worked in the healthcare/hospital industry? ", "1")
    enter_experience(driver, "How many years of experience do you have with SQL?", "1")
    enter_experience(driver, "How many years of work experience do you have with AWS SageMaker?", "1")
    enter_experience(driver, "How many years of work experience do you have with REST API development?", "1")
    enter_experience(driver, "How many years of work experience do you have with R?", "1")
    enter_experience(driver, "How many years of work experience do you have with Python?", "3")
    enter_experience(driver, "How many years of work experience do you have with SAS?", "1")
    enter_experience(driver, "How many years of work experience do you have with Domino Data Labs?", "1")
    enter_experience(driver, "How many years of work experience do you have with Acceptance Testing?", "2")
    enter_experience(driver, "How many years of work experience do you have with Agile Testing?", "3")
    enter_experience(driver, "How many years of work experience do you have with After Effects?", "1")
    enter_experience(driver, "How many years of work experience do you have with Kernel?", "1")
    enter_experience(driver, "How many years of work experience do you have with Financial Engineering?", "1")
    enter_experience(driver, "How many years of work experience do you have with Quantitative Analytics?", "1")
    enter_experience(driver, "How many years of work experience do you have with Database Management System (DBMS)?", "1")
    enter_experience(driver, "How many years of work experience do you have with JUnit?", "1")
    enter_experience(driver, "How many years of work experience do you have with GitHub Copilot?", "1")
    enter_experience(driver, "How many years of work experience do you have with Microsoft Copilot?", "1")
    enter_experience(driver, "How many years of work experience do you have with SAP ERP?", "1")
    enter_experience(driver, "How many years of work experience do you have with Micro Focus Quality Center?", "1")
    enter_experience(driver, "How many years of work experience do you have with Azure Kubernetes Service (AKS)?", "1")
    enter_experience(driver, "How long have you been working in software development?", "2")
    enter_experience(driver, "How many years of work experience do you have with Large Language Models (LLM)?", "1")
    enter_experience(driver, "How many years of work experience do you have with GitHub Models?", "1")
    enter_experience(driver, "How many years of work experience do you have with E-commerce SEO?", "1")

    # Additional questions – dropdown menu
    select_dropdown_option(driver, "Do you have knowledge of Shopify Hydrogen for headless e-commerce development.", "No")
    select_dropdown_option(driver, "Do you have any references from previous clients?", "Yes")
    select_dropdown_option(driver, "Are you comfortable working in Flutter?", "No")
    select_dropdown_option(driver, "Do you have a github profile?", "Yes")
    select_dropdown_option(driver, "Do you need Visa Sponsorship, now or in the future to work on our W2?", "No")
    select_dropdown_option(driver, "Do you currently reside in the San Francisco Bay Area?", "Yes")
    select_dropdown_option(driver, "Are you willing and able to work in Go/ Golang?", "Yes")
    select_dropdown_option(driver, "Did you complete your education in the United States?", "Yes")
    select_dropdown_option(driver, "Do you have experience with Playwright, Puppeteer, or Beautiful Soup?", "Yes")
    select_dropdown_option(driver, "Do you have experience with Core Data?", "Yes")
    select_dropdown_option(driver, "Are you available for hybrid work at the Mountain View office?", "Yes")
    select_dropdown_option(driver, "Are you comfortable working on Pacific Time? Are you comfortable working on Pacific Time?", "Yes")
    select_dropdown_option(driver, "Are you interested with this remote application ?Are you interested with this remote application ?", "Yes")
    select_dropdown_option(driver, "Have you developed network applications for IOS/MacOS?", "Yes")
    select_dropdown_option(driver, "Candidate should be comfortable to work on W2 Full time role.", "Yes")
    select_dropdown_option(driver, "Client is looking for Citizens and GC.", "Yes")
    select_dropdown_option(driver, "Candidate should have experience with PLG.", "Yes")
    select_dropdown_option(driver, "Do you currently reside in any of the California counties of Alameda, San Mateo or Santa Clara?", "Yes")
    select_dropdown_option(driver, "Are you familiar using the Applauser/uTest platform?", "Yes")
    select_dropdown_option(driver, "Can you work during Eastern time zone hours?", "Yes")
    select_dropdown_option(driver, "Are you comfortable working three days on-site in Scottsdale, Arizona?", "No")
    select_dropdown_option(driver, "Do you currently reside within 40 miles of Scottsdale, Arizona?", "No")
    select_dropdown_option(driver, "Do you have experience with Automation Anywhere?", "Yes")
    select_dropdown_option(driver, "Are you a US Citizen? (required for some sensitive data for this position)", "Yes")
    select_dropdown_option(driver, "Must have 3+ Years of experience with Gen AI & Chatbot Testing", "Yes")
    select_dropdown_option(driver, "Do you have eperience developing and maintaining a C# Test automation framework?", "Yes")
    select_dropdown_option(driver, "Are you comfortable working Pacific Time hours?", "Yes")
    select_dropdown_option(driver, "Do you have a Bachelor's degree in Computer Science, Computer Engineering, or related major?", "Yes")
    select_dropdown_option(driver, "Capturing and analyzing network logs (e.g., Wireshark traces) to identify and resolve issuesCapturing and analyzing network logs (e.g., Wireshark traces) to identify and resolve issues", "Yes")
    select_dropdown_option(driver, "Reviewing vendor-provided MOPs for compliance and accuracyReviewing vendor-provided MOPs for compliance and accuracy", "Yes")
    select_dropdown_option(driver, "Executing functional and performance tests using Spirent Landslide and other tools ?", "Yes")
    select_dropdown_option(driver, "Experience on Developing and managing Test Object Lists (TOL) ?", "Yes")
    select_dropdown_option(driver, "Do you have strong understanding of call flows for 4G LTE and 5G technologies ?", "Yes")
    select_dropdown_option(driver, "This is W2 contract position, are you ready to work ?", "Yes")
    select_dropdown_option(driver, "Are you local to Sunnyvale CA?Are you local to Sunnyvale CA?", "Yes")
    select_dropdown_option(driver, "Do you have experience with Product Pricing Engines (PPEs) for the Mortgage Industry?", "Yes")
    select_dropdown_option(driver, "Are you comfortable with data structures and algorithms?", "Yes")
    select_dropdown_option(driver, "This position does NOT use javascript frameworks. Are you comfortable with HTML, CSS and vanilla javascript?", "Yes")
    select_dropdown_option(driver, "Do you have experience in soap and rest API UI automation testing?", "Yes")
    select_dropdown_option(driver, "Do you have full-stack experience?", "Yes")
    select_dropdown_option(driver, "Do you have React and Javascript experience from a previous role?", "Yes")
    select_dropdown_option(driver, "Do you have experience as a QA tester or similar role?", "Yes")
    select_dropdown_option(driver, "While this opportunity is fully remote, it does require working in alignment with PST hours/time zone, is this something you are comfortable with?", "Yes")
    select_dropdown_option(driver, "Are you located in India", "No")
    select_dropdown_option(driver, "Do you live in the United States - Eastern Standard or Central Standard time zones? PST will NOT be considered.", "Yes")
    select_dropdown_option(driver, "Do you have a minimum of 3 years of experience with API testing using Postman?", "Yes")
    select_dropdown_option(driver, "Have you completed a 4-year degree from an accredited university in Computer Science, Information Technology or related IT distinction?", "Yes")
    select_dropdown_option(driver, "Do you require to work on C2C? Do you require to work on C2C?", "Yes")
    select_dropdown_option(driver, "Mandatory: We only accept w2 applicants, are you willing to work on W2?", "Yes")
    select_dropdown_option(driver, "Must local to Cupertino, CA or near by state ?", "Yes")
    select_dropdown_option(driver, "Do you have any experience wiht RabbitMQ or similar tools?", "Yes")
    select_dropdown_option(driver, "Have you ever worked with GraphQL or any similar tools?", "Yes")
    select_dropdown_option(driver, "Do you have any experience with CI/CD or IaC tools?", "Yes")
    select_dropdown_option(driver, "Do you have experience with microservice architecture?", "Yes")
    select_dropdown_option(driver, "HiveQLHiveQL", "Yes")
    select_dropdown_option(driver, "Unified Payment Platform (UPP)", "Yes")
    select_dropdown_option(driver, "Do you have 5 or more years of industry experience in software engineering, excluding internships?", "Yes")
    select_dropdown_option(driver, "Instabase is a hybrid workplace which requires in-office presence at least 2 times a week to one our US based hubs. Are you local to the San Francisco Bay Area or New York City? If not, would you be willing to relocate?", "Yes")
    select_dropdown_option(driver, "Do you currently hold an H1 visa or need an H1 sponsorship?Do you currently hold an H1 visa or need an H1 sponsorship?", "No")
    select_dropdown_option(driver, "Are you able AND interested in working directly on a W2 contract without requiring a Corp-to-Corp (C2C) employment or visa sponsorship?", "Yes")
    select_dropdown_option(driver, "Are you able to work core PST business hours (Monday - Friday)?Are you able to work core PST business hours (Monday - Friday)?", "Yes")
    select_dropdown_option(driver, "We can take applicants on W2 only, are comfortable working on W2?", "Yes")
    select_dropdown_option(driver, "Do you have hands on experience with YAML?", "Yes")
    select_dropdown_option(driver, "This role is not available for C2C, Visa Transfer, or Sponsorship. Are you a U.S. Citizen, Green Card Holder, or EAD Card Holder?", "No")
    select_dropdown_option(driver, "Experience in Aws/GCPCloud?Experience in Aws/GCPCloud?", "Yes")
    select_dropdown_option(driver, "Do y ou have experience with Terraform?", "Yes")
    select_dropdown_option(driver, "Do you have experience with Selenium?", "Yes")
    select_dropdown_option(driver, "Are you more of a specialist in Manual/Functional testing, than automation?", "Yes")
    select_dropdown_option(driver, "Are you based in EST time zone?", "No")
    select_dropdown_option(driver, "Will you be working on a 1099 or C2C for this position?", "Yes")
    select_dropdown_option(driver, "Are you available for direct W2 contract work without needing sponsorship?", "No")
    select_dropdown_option(driver, "Unfortunately, this position does not support TPV/C2C/Sponsorship. Are you willing/able to work directly on w2, without sponsorship, from day one for this opportunity?", "Yes")
    select_dropdown_option(driver, "Are you able to work on W2 in the US without any sponsorship now or in the future?", "Yes")
    select_dropdown_option(driver, "Have you deployed multiple models on kubernetes?", "Yes")
    select_dropdown_option(driver, "Experience with Automated Testing", "Yes")
    select_dropdown_option(driver, "Visa USC/GCVisa USC/GC", "No")
    select_dropdown_option(driver, "Are you a United States Citizen?", "Yes")
    select_dropdown_option(driver, "Do you have experience with C# and C++?", "Yes")
    select_dropdown_option(driver, "Are you comfortable with W2 position?", "Yes")
    select_dropdown_option(driver, "are you comfortable working on W2", "Yes")
    select_dropdown_option(driver, "Next.js, Nest.js, MariaDB Database Proficiency", "Yes")
    select_dropdown_option(driver, "English as primary language", "Yes")
    select_dropdown_option(driver, "United States Based", "Yes")
    select_dropdown_option(driver, "Are you located in California, US?", "Yes")
    select_dropdown_option(driver, "Do you have 2+ years of experience in the Autonomous Vehicle field preparing vehicles and system for data collection, collecting various types of data for DNN training?", "No")
    select_dropdown_option(driver, "Do you have 2+ years of hands-on experience with Linux and Windows operating systems?", "Yes")
    select_dropdown_option(driver, "Do you have 2+ years of experience working with Python, Bash, and C++?", "Yes")
    select_dropdown_option(driver, "Are you authorized to work in the US without sponsorship?", "Yes")
    select_dropdown_option(driver, "Do you currently reside a commutable distance from Santa Clara, Ca?", "Yes")
    select_dropdown_option(driver, "Is your permanent address in Texas?", "No")
    select_dropdown_option(driver, "Are you going to require sponsorship now or in the future?", "No")
    select_dropdown_option(driver, "Do you have payment lifecycle knowledge?", "Yes")
    select_dropdown_option(driver, "Are you currently living in Los Angeles?", "Yes")
    select_dropdown_option(driver, "Can you work W2 and not C2C or 1099?", "Yes")
    select_dropdown_option(driver, "Can you work on w2?Can you work on w2?", "Yes")
    select_dropdown_option(driver, "Do you have experience working at any Media Company such as HBO, NBC, Netflix, Paramount, Disney, etc.?Do you have experience working at any Media Company such as HBO, NBC, Netflix, Paramount, Disney, etc.?", "No")
    select_dropdown_option(driver, "What is your level of proficiency in English?", "Professional")
    select_dropdown_option(driver, "This is a W2 contract role and the C2C option is not available. Are you willing to work on a W2 basis?", "Yes")
    select_dropdown_option(driver, "Are you legally authorized to work in the country that this role is based?", "Yes")
    select_dropdown_option(driver, "Do you need, or will you need in the future, any immigration-related support or sponsorship from EarnIn in order to begin or continue employment with EarnIn?", "No")
    select_dropdown_option(driver, "What is your preferred pronoun?", "Prefer not to answer")
    select_dropdown_option(driver, "Have you previously applied to a role at EarnIn?", "No")
    select_dropdown_option(driver, "Do you have experience working with JVM?", "Yes")
    select_dropdown_option(driver, "Can you work on W2 without any sponsorship?", "Yes")
    select_dropdown_option(driver, "How did you hear about this job?How did you hear about this job?", "LinkedIn Job Post")
    select_dropdown_option(driver, "Will you now, or in the future require sponsorship to legally work in the country where this role is based?", "No")
    select_dropdown_option(driver, "Have you got any experience working on Robot arm programming languages?", "No")
    select_dropdown_option(driver, "Will you now, or in the future, require VISA sponsorship or transfer?", "No")
    select_dropdown_option(driver, "Do you have 3 years commercial experience (post-education) as a mobile software engineer?", "No")
    select_dropdown_option(driver, "Do you have strong experience in React Native?", "No")
    select_dropdown_option(driver, "Do you have experience within Options - specifically OPRA market data feed?", "No")
    select_dropdown_option(driver, "Have you built distributed systems with Ruby or Javascript/Typescript?", "No")
    select_dropdown_option(driver, "Are you currently working in a full time role?", "No")
    select_dropdown_option(driver, "Can you work onsite (HYBRID) in Sunnyvale, CA from Day 1?", "No")
    select_dropdown_option(driver, "Are you authorized to work in the United States?", "Yes")
    select_dropdown_option(driver, "Do you have 2 or more years of industry experience in software engineering, excluding internships?", "No")
    select_dropdown_option(driver, "Are you local to the San Francisco Bay Area or New York City? If not, would you be willing to relocate to one of these areas?", "Yes")
    select_dropdown_option(driver, "This role is based in Cupertino and requires in-office attendance a minimum of 4x per week. Are you able to come in-office to our Cupertino office 4x per week?", "Yes")
    select_dropdown_option(driver, "It's W2 role. Only GC and USC can apply", "Yes")
    select_dropdown_option(driver, "Do you have any active certifications", "No")
    select_dropdown_option(driver, "Do you have experience in performing hands-on evaluations of websites or products without relying heavily on technical testing methods?", "Yes")
    select_dropdown_option(driver, "Do you have experience in performing Quality Assurance for any advertising campaign to confirm that the ads are effective and error-free?", "No")
    select_dropdown_option(driver, "Have you collaborated with development teams to resolve quality issues during the web development lifecycle?", "Yes")
    select_dropdown_option(driver, "Have you ever had to present your testing findings to stakeholders or team members?", "Yes")
    select_dropdown_option(driver, "Do you have at least 3+ years of experience manual testing Salesforce application?", "Yes")
    select_dropdown_option(driver, "Do have experience in Java Full Stack Development?", "Yes")
    select_dropdown_option(driver, "Do you have experience within the healthcare industry?", "Yes")
    select_dropdown_option(driver, "Are you comfortable to work on W2 with Zonforce?", "Yes")
    select_dropdown_option(driver, "Have you created software automation scripts with python FROM SCRATCH?", "Yes")
    select_dropdown_option(driver, "Did you complete a 4-year Bachelor's degree in the United States?", "Yes")
    
    
    


    # Additonal question – radio buttons 
    select_radio_button(driver, "Are you comfortable working in a hybrid setting?", "Yes")
    select_radio_button(driver, "Are you authorized to work in the United States?", "Yes")
    select_radio_button(driver, "Have you completed the following level of education: Associate's Degree?", "Yes")
    select_radio_button(driver, "Do you have the following license or certification: Advisory Services?", "Yes")
    select_radio_button(driver, "Will you now, or in the future, require sponsorship for employment visa status (e.g. H-1B visa status)?", "No")
    select_radio_button(driver, "Are you willing to take a drug test, in accordance with local law/regulations?", "Yes")
    select_radio_button(driver, "Are you comfortable commuting to this job's location?", "Yes")
    select_radio_button(driver, "Are you comfortable working in a remote setting?", "Yes")
    select_radio_button(driver, "Will you now or in the future require sponsorship by the company?", "Yes")
    select_radio_button(driver, "Will you now, or in the future, require sponsorship for employment visa status (e.g. H-1B visa status)?", "No")
    
    click_button("//button[normalize-space()='Next']")
    select_radio_button(driver, "Will you now, or in the future, require sponsorship for employment visa status (e.g. H-1B visa status)?", "No")

    # Work Authoritzation – radio buttons 

    
    # for i in range(2):
    # click_button("//button[normalize-space()='Next']")
    # print(f"Clicked Next button {i + 1} times.")
    
    
    # # Voluntary self identification (1) 
    # try:
    #     driver.find_element(By.CSS_SELECTOR, '.fb-dash-form-element__error-field.artdeco-text-input--input').send_keys("Oscar Leung")
    # except:
    #     print("no volunteer")
    #     click_button("//div[@data-test-date-picker='']")
    #     click_button("//button[contains(@aria-label, 'This is today')]")

    
    
    click_button("//button[normalize-space()='Review']")
    click_button("//button[normalize-space()='Submit application']")
    click_button("//button[normalize-space()='Done']")
    click_button("//div[@role='dialog']//button[@aria-label='Dismiss']")


# ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  this python script does easy applys jobs for me ––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
driver = webdriver.Chrome()
driver.get("https://www.linkedin.com/login")
driver.find_element(By.ID,"username").send_keys(username)
driver.find_element(By.ID,"password").send_keys(password)
driver.find_element(By.XPATH, "//button[@type='submit']").click()
driver.find_element(By.XPATH, "//a//span[@title='Jobs']").click()
driver.get("https://www.linkedin.com/jobs/search/")

input_text = (
    '"QA Engineer" OR "Quality Assurance" OR "SQA" OR "Software Engineer" OR "Automation Engineer" OR "Software Tester" OR '
    '"Test Engineer" OR "QA Automation" OR "Test Automation" OR "Front-End Developer" OR "React Developer" OR '
    '"Angular Developer" OR "Web Developer" OR "Mobile Developer" OR "UI Developer" OR "UX Developer" OR '
    '"Full-Stack Developer" AND "Salesforce" OR "Jira" OR "Selenium" OR "Java" OR "Python" OR "TestRail" OR "Expresso" '
    'OR "SQL" OR "GitHub" OR "Jenkins" OR "TeamCity" OR "Automation Framework" OR "Regression Testing" OR "Unit Testing" '
    'OR "Smoke Testing" OR "Exploratory Testing" OR "Angular" OR "React" OR "Vue.js" OR "Node.js" OR "HTML" OR "CSS" '
    'OR "JavaScript" OR "TypeScript" OR "Swift" OR "Kotlin" OR "Android" OR "iOS" OR "Flutter" OR "Vue" OR "Redux" '
    'OR "Firebase"'
)

fill_input_field(driver, By.XPATH, "//input[@aria-label='Search by title, skill, or company']", input_text, 1)

job_list = driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")

# Iterate over the job listings
for index, job in enumerate(job_list):
    try:
        # Scroll to the element if necessary (ensures the element is in view)
        driver.execute_script("arguments[0].scrollIntoView();", job)
        # Click on the job posting
        job.click()
        time.sleep(2)
        print(f"Clicked on job posting {index + 1}")
        # Here you can add code to interact with the job posting, like applying, scraping info, etc.
        easy_apply()
        click_button("//div[@role='dialog']//button[@aria-label='Dismiss']")
        click_button("//button[normalize-space()='Discard']")
    except Exception as e:
        print(f"Failed to click on job {index + 1}: {e}")


