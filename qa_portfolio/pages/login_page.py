"""Login page POM for saucedemo.com."""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class LoginPage(BasePage):
    # Locators
    USERNAME_INPUT  = (By.ID, "user-name")
    PASSWORD_INPUT  = (By.ID, "password")
    LOGIN_BUTTON    = (By.ID, "login-button")
    ERROR_MESSAGE   = (By.CSS_SELECTOR, "[data-test='error']")

    def open(self):
        super().open("/")

    def login(self, username: str, password: str):
        self.type_text(*self.USERNAME_INPUT, username)
        self.type_text(*self.PASSWORD_INPUT, password)
        self.click(*self.LOGIN_BUTTON)

    def get_error_message(self) -> str:
        return self.get_text(*self.ERROR_MESSAGE)

    def is_error_displayed(self) -> bool:
        return self.is_visible(*self.ERROR_MESSAGE)
