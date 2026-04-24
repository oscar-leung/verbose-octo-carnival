"""
Outlier AI Contractor Task — Perception Label Annotation (Nov 2025)
────────────────────────────────────────────────────────────────────
Labels AI model outputs with perception quality tags for Outlier.ai
training data. Evaluates visual or audio outputs on perceptual dimensions
and submits structured label data.

Usage: python 014_outlier_script_251119-add-perception-labels.py
"""
import os
import time
import random
from contextlib import suppress
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
    TimeoutException
)
from selenium.webdriver.support import expected_conditions as EC

# load_dotenv()
load_dotenv()
username = os.getenv("outlier_email")
password = os.getenv("outlier_password")

search_queries = [
    "labeled animal cell structure diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "labeled plant cell anatomy diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "bacterial cell structure labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "labeled neuron structure diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human eye anatomy labeled parts -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human ear cross section labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human heart blood flow diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "digestive system organs labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "respiratory system labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human skeletal system labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "DNA double helix structure labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "photosynthesis process diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "parts of a flower diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "nitrogen cycle diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "carbon cycle labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "food web diagram labeled producers consumers -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "mitosis stages labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "meiosis phases labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "virus structure labeled bacteriophage -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human skin layers labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "microscope parts and functions labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "kidney cross section labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "human brain lobes labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "leaf cross section labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "simple electric circuit labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "series and parallel circuits labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "ray diagram concave mirror labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "ray diagram convex lens labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "transverse wave parts labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "longitudinal wave parts labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "electromagnetic spectrum labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "free body diagram inclined plane labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "simple pendulum forces labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "pulley system labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "lever classes 1 2 3 labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "projectile motion trajectory labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "magnetic field lines bar magnet labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "electric motor parts labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "ac generator diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "cathode ray tube diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "rutherford atomic model labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "bohr model atom labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "periodic table labeled groups periods -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "covalent bonding diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "ionic bonding diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "lab distillation apparatus labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "titration setup labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "bunsen burner parts labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "filtration process lab diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "electrolytic cell diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "galvanic cell diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "phase change diagram water labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "ph scale chart labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "molecular geometry shapes labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "paper chromatography setup labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "blast furnace diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "fractional distillation crude oil labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "lewis dot structure examples labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "parts of a car engine labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "four stroke engine cycle labeled diagram -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "manual transmission gearbox parts labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "centrifugal pump components labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "hydraulic system schematic labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "pneumatic system diagram labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    "refrigeration cycle diagram labeled components -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com",
    ]

# Initialize WebDriver and login to Multimango
driver = webdriver.Chrome()
wait = WebDriverWait(driver, 5)
driver.get("https://www.multimango.com/")
wait.until(EC.presence_of_element_located((By.ID, "identifier-field"))).send_keys(username)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
time.sleep(2)
wait.until(EC.presence_of_element_located((By.ID, "password-field"))).send_keys(password)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-localization-key='formButtonPrimary']"))).click()
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-sidebar='menu-button']"))).click()
time.sleep(30)
wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@href='/tasks/251119-add-perception-labels']//button"))).click()
time.sleep(90)
wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Continue to Task']"))).click()

# Start the timed loop
duration = 600 * 60 # 540 minutes = 10 hours
start = time.time()
end = start + duration
run = 1

while time.time() < end:
    elapsed = int(time.time() - start)
    remaining = int(end - time.time())
    mins_p, secs_p = divmod(elapsed, 60)
    mins_r, secs_r = divmod(remaining, 60)
    print(f"\n---- cycle {run} ----\n"f"Elapsed: {mins_p:02d}:{secs_p:02d} | Remaining: {mins_r:02d}:{secs_r:02d}")

    for search in search_queries:
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search for images...']"))).send_keys(search)
            # wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search for images...']"))).send_keys("labeled animal cell diagram white background")
            wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search for images...']"))).send_keys("manual transmission gearbox parts labeled -site:shutterstock.com -site:gettyimages.com -site:istockphoto.com -site:alamy.com -site:dreamstime.com -site:123rf.com -site:freepik.com -site:pinterest.com -site:youtube.com -site:reddit.com -site:giphy.com")
            wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='flex gap-2 ']//button"))).click()
            driver.switch_to.window(driver.window_handles[-1])
            valid_urls = []
            # Scroll to the bottom to load all images
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    print("Reached the bottom of the page.")
                    break
                last_height = new_height
                
            src_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@jsname='dTDiAc']//h3//a//img")))
            # //div[@data-sci="1"]
            for element in src_elements:
                element.click()
                src = element.get_attribute("src")
                if src and src.startswith("http"):
                    valid_urls.append(src)
                    print(f"Stored: {src}")
            print(f"Total valid images found: {len(valid_urls)}")
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

            # Process each valid URL
            for i, url in enumerate(valid_urls):
                print(f"Processing Image {i + 1} of {len(valid_urls)}")
    
                try:
                    input_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='https://example.com/image.jpg']")))
                    input_field.clear()
                    input_field.send_keys(url)
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Process Image']"))).click()
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Detect Labels']"))).click()
                    time.sleep(5) 
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Submit']"))).click()
                    time.sleep(2)
                    
                except Exception :
                    print(f"Error processing image {i + 1}")
                    # If an error happens (e.g., image invalid), the loop continues to the next URL
                    continue
        except Exception as e:
            print(f"Error with search query '{search}': {e}")

    run += 1

print("\n⏱️ Timer finished!")


