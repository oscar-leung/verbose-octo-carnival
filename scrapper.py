import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException
from selenium.webdriver.support.ui import Select

import logging
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException,TimeoutException, ElementNotInteractableException,NoSuchElementException
from selenium.webdriver.support.ui import Select

workday_career_pages = {
    "Intel": "https://intel.wd1.myworkdayjobs.com/en-US/External",
    "Maxar": "https://maxar.wd1.myworkdayjobs.com/Maxar",
    "NVIDIA": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    "Applied Materials": "https://amat.wd1.myworkdayjobs.com/External",
    "Adobe": "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced",
    "Zoom": "https://zoom.wd5.myworkdayjobs.com/Zoom/",
    "KLA": "https://kla.wd1.myworkdayjobs.com/en-US/Search/",
    "Rakuten": "https://rakuten.wd1.myworkdayjobs.com/en-US/RakutenRewards",
    "Dicks Sporting Goods": "https://dickssportinggoods.wd1.myworkdayjobs.com/en-US/DSG",
    "Open Lane": "https://kar.wd1.myworkdayjobs.com/en-US/OPENLANE_Careers",
    "Leidos": "https://leidos.wd5.myworkdayjobs.com/en-US/External",
    "Brambles": "https://brambles.wd5.myworkdayjobs.com/Brambles_Careers",
    "Public Consulting Group": "https://pcg.wd1.myworkdayjobs.com/en-US/PCG_External_Careers/",
    "Bonterra": "https://bonterra.wd1.myworkdayjobs.com/en-US/bonterratech/userHome",
    "Penn Mutual": "https://pennmutual.wd1.myworkdayjobs.com/en-US/_penn-careers/userHome",
    "Broadcom": "https://broadcom.wd1.myworkdayjobs.com/en-US/External_Career/userHome",
    "Adobe": "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced/jobs",
    "Ring Central": "https://ringcentral.wd1.myworkdayjobs.com/en-US/RingCentral_Careers/userHome",
    "Tinuiti": "https://tinuiti.wd12.myworkdayjobs.com/en-US/Tinuiti/userHome",
    "Root": "https://joinroot.wd1.myworkdayjobs.com/en-US/joinroot/userHome",
    "Ebay": "https://ebay.wd5.myworkdayjobs.com/en-US/apply/userHome",
    "Sailpoint": "https://sailpoint.wd1.myworkdayjobs.com/en-US/SailPoint/userHome",
    "Campbell Soup": "https://campbellsoup.wd5.myworkdayjobs.com/en-US/ExternalCareers_GlobalSite/userHome",
    "Disney": "https://disney.wd5.myworkdayjobs.com/en-US/disneycareer/userHome",
    "Wex": "https://wexinc.wd5.myworkdayjobs.com/en-US/WEXInc/userHome",
    "Twitter": "https://twitter.wd5.myworkdayjobs.com/en-US/X/userHome",
    "OutSystem": "https://outsystems.wd5.myworkdayjobs.com/en-US/OutSystems/userHome",
    "SnapChat": "https://wd1.myworkdaysite.com/en-US/recruiting/snapchat/snap/userHome",
    "Symbotic": "https://symbotic.wd1.myworkdayjobs.com/en-US/Symbotic",
    "Republic": "https://republic.wd5.myworkdayjobs.com/en-US/Republic/userHome",
    "Abbott": "https://abbott.wd5.myworkdayjobs.com/it-IT/abbottcareers/userHome",
    "Integer": "https://integer.wd1.myworkdayjobs.com/en-US/External/userHome",
    "cw": "https://cw.wd1.myworkdayjobs.com/en-US/External/userHome",
    "Credit Acceptance": "https://creditacceptance.wd5.myworkdayjobs.com/en-US/Credit_Acceptance",
    "General Motors": "https://generalmotors.wd5.myworkdayjobs.com/en-US/Careers_GM/userHome",
    "Humana": "https://humana.wd5.myworkdayjobs.com/en-US/Humana_External_Career_Site/userHome",
    "Key Bank": "https://keybank.wd5.myworkdayjobs.com/en-US/External_Career_Site/userHome",
    "National Indemnity": "https://nationalindemnity.wd5.myworkdayjobs.com/en-US/BHDIC/userHome",
    "Inmar": "https://inmar.wd1.myworkdayjobs.com/en-US/inmarcareers/userHome",
    "BMO": "https://bmo.wd3.myworkdayjobs.com/en-US/External/userHome",
    "Transunion": "https://transunion.wd5.myworkdayjobs.com/en-US/TransUnion/userHome",
    "Epiqsystems": "https://epiqsystems.wd5.myworkdayjobs.com/en-US/Epiq_Careers/userHome",
    "Dataminr": "https://dataminr.wd12.myworkdayjobs.com/en-US/Dataminr/userHome",
    "Fullsteam": "https://fullsteam.wd1.myworkdayjobs.com/en-US/External/jobTasks/completed/application",
    "Home Depot": "https://homedepot.wd5.myworkdayjobs.com/en-US/CareerDepot/userHome",
}

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

def click_button_by_automation_id(driver, automation_id):
    """
    Clicks a button with the specified data-automation-id. 
    Tries to find both button and div elements.
    """
    # Try to find and click the actual button
    time.sleep(1)
    try:
        button = driver.find_element(By.XPATH, f"//button[@data-automation-id='{automation_id}']")
        button.click()
        print(f"Clicked button with automation ID: '{automation_id}'")
        return  # Exit after clicking

    except NoSuchElementException:
        print(f"Button with automation ID '{automation_id}' not found.")
    
    # Try to find and click the div element if the button is not found
    try:
        div_button = driver.find_element(By.XPATH, f"//div[@data-automation-id='{automation_id}']")
        div_button.click()
        print(f"Clicked div button with automation ID: '{automation_id}'")
        
    except NoSuchElementException:
        print(f"Div button with automation ID '{automation_id}' not found.")

def send_keys_by_automation_id(automation_id, text):
    time.sleep(1)
    try:
        button = driver.find_element(By.XPATH, f"//input[@data-automation-id='{automation_id}']")
        button.send_keys({text})
    except NoSuchElementException:
        print(f"Input Field with automation ID '{automation_id}' not found.")

# rakuten script 
driver = webdriver.Chrome()
driver.get(workday_career_pages["Rakuten"])
click_button_by_automation_id(driver, "utilityButtonSignIn")
send_keys_by_automation_id(driver, "email", "oscarleung1@gmail.com")
send_keys_by_automation_id(driver, "password", "Bumblebee4$2024")
click_button_by_automation_id(driver, "click_filter")
click_button_by_automation_id(driver, "distanceLocation")
click_button("//label[contains(text(),'San Francisco')]")
click_button("//label[contains(text(),'San Mateo')]")
click_button_by_automation_id(driver, "viewAllJobsButton")
time.sleep(2)
lst = driver.find_elements(By.XPATH, "//a[@data-automation-id='jobTitle']")
for job in lst:
    print(job.text)


# maxar
driver = webdriver.Chrome()
driver.get("https://maxar.wd1.myworkdayjobs.com/Maxar")
click_button_by_automation_id(driver, "utilityButtonSignIn")
send_keys_by_automation_id(driver, "email", "oscarleung1@gmail.com")
send_keys_by_automation_id(driver, "password", "Bumblebee4$2024")
click_button_by_automation_id(driver, "click_filter")
click_button_by_automation_id(driver, "distanceLocation")
click_button("//label[contains(text(),'California')]")
click_button_by_automation_id(driver, "keywordSearchButton")
time.sleep(2)
lst = driver.find_elements(By.XPATH, "//a[@data-automation-id='jobTitle']")
for job in lst:
    print(job.text)

# intel
driver = webdriver.Chrome()
driver.get("https://intel.wd1.myworkdayjobs.com/en-US/External")
click_button_by_automation_id(driver, "utilityButtonSignIn")
send_keys_by_automation_id(driver, "email", "oscarleung1@gmail.com")
send_keys_by_automation_id(driver, "password", "Bumblebee4$2024")
click_button_by_automation_id(driver, "click_filter")
click_button_by_automation_id(driver, "distanceLocation")
click_button("//label[contains(text(),'US, California, San Jose')]")
click_button("//label[contains(text(),'US, California, Santa Clara')]")
click_button_by_automation_id(driver, "keywordSearchButton")
time.sleep(2)

# nvidia
driver = webdriver.Chrome()
driver.get(workday_career_pages["NVIDIA"])
click_button_by_automation_id(driver, "utilityButtonSignIn")
send_keys_by_automation_id(driver, "email", "oscarleung1@gmail.com")
send_keys_by_automation_id(driver, "password", "Bumblebee4$2024")
click_button_by_automation_id(driver, "click_filter")

non_workday_career_pages = {
    "AMD": "https://www.amd.com/en/corporate/careers",
    "Snowflake": "https://careers.snowflake.com/us/en/search-results",
    "Cisco": "https://jobs.cisco.com/jobs/Home",
    "Tesla": "https://www.tesla.com/careers/search/?site=US",
    "Apple": "https://jobs.apple.com/en-us/search",
    "Google": "https://www.google.com/about/careers/applications/jobs/results/",
    "ServiceNow": "https://www.servicenow.com/careers.html",
    "Oracle": "https://www.oracle.com/corporate/careers/",
    "Palo Alto Networks": "https://jobs.paloaltonetworks.com/search-jobs",
    "Silicon Valley Bank": "https://jobs.firstcitizens.com/",
    "Fortinet": "https://edel.fa.us2.oraclecloud.com/hcmUI/CandidateExperience",
    "Pure Storage": "https://www.purestorage.com/company/careers/opportunities.html",
    "Arista Networks": "https://www.arista.com/en/careers"
}