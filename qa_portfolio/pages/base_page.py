"""Base page — shared driver helpers used by all page objects."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    BASE_URL = "https://www.saucedemo.com"
    DEFAULT_TIMEOUT = 10

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, self.DEFAULT_TIMEOUT)

    def open(self, path=""):
        self.driver.get(self.BASE_URL + path)

    def find(self, by, value):
        return self.wait.until(EC.presence_of_element_located((by, value)))

    def click(self, by, value):
        el = self.wait.until(EC.element_to_be_clickable((by, value)))
        el.click()
        return el

    def type_text(self, by, value, text):
        el = self.find(by, value)
        el.clear()
        el.send_keys(text)

    def get_text(self, by, value) -> str:
        return self.find(by, value).text.strip()

    def is_visible(self, by, value, timeout=3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            return True
        except Exception:
            return False

    @property
    def current_url(self) -> str:
        return self.driver.current_url
