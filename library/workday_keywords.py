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
import time
from selenium.webdriver.common.by import By

def highlight_buttons_with_automation_id(driver):
    """
    Highlights <button> or [role='button'] elements that have a data-automation-id.
    Applies blue border and floating label with the automation ID.
    Clears any previous highlights or labels.
    """
    # Clear previously injected labels and highlights
    driver.execute_script('''
        document.querySelectorAll(".interactable-label").forEach(e => e.remove());
        document.querySelectorAll(".interactable-highlight").forEach(e => {
            e.style.border = "";
            e.classList.remove("interactable-highlight");
        });
    ''')

    # Select all <button> and elements with role='button'
    buttons = driver.find_elements(By.CSS_SELECTOR, "button, [role='button']")

    count = 0
    for elem in buttons:
        automation_id = elem.get_attribute("data-automation-id")
        if not automation_id:
            continue  # Skip if no data-automation-id

        count += 1
        label_text = f"{count}. {automation_id}"

        # Highlight the element with a blue border
        driver.execute_script('''
            arguments[0].style.border = "2px solid blue";
            arguments[0].classList.add("interactable-highlight");
        ''', elem)

        # Add a floating label
        driver.execute_script('''
            var label = document.createElement("div");
            label.className = "interactable-label";
            label.innerText = arguments[1];
            label.style.position = "absolute";
            label.style.background = "#007bff";
            label.style.color = "white";
            label.style.fontSize = "12px";
            label.style.padding = "2px 5px";
            label.style.borderRadius = "4px";
            label.style.zIndex = "99999";
            label.style.fontFamily = "monospace";

            var rect = arguments[0].getBoundingClientRect();
            label.style.left = (rect.left + window.scrollX) + "px";
            label.style.top = (rect.top + window.scrollY - 20) + "px";

            document.body.appendChild(label);
        ''', elem, label_text)

def monitor_buttons(driver, interval=5):
    """
    Continuously checks and highlights buttons with automation ID every `interval` seconds.
    """
    try:
        while True:
            print("Refreshing buttons with data-automation-id...")
            highlight_buttons_with_automation_id(driver)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("Stopped by user.")

driver = webdriver.Chrome()
driver.get("https://intel.wd1.myworkdayjobs.com/en-US/External")
monitor_buttons(driver)