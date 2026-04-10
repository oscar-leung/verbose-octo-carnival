"""Cart page POM for saucedemo.com."""

from selenium.webdriver.common.by import By
from .base_page import BasePage


class CartPage(BasePage):
    CART_ITEMS      = (By.CLASS_NAME, "cart_item")
    ITEM_NAMES      = (By.CLASS_NAME, "inventory_item_name")
    CHECKOUT_BUTTON = (By.ID, "checkout")
    CONTINUE_BUTTON = (By.ID, "continue-shopping")
    REMOVE_BUTTONS  = (By.CSS_SELECTOR, "button[data-test^='remove']")

    def open(self):
        super().open("/cart.html")

    def get_cart_item_names(self) -> list[str]:
        return [el.text for el in self.driver.find_elements(*self.ITEM_NAMES)]

    def get_cart_item_count(self) -> int:
        return len(self.driver.find_elements(*self.CART_ITEMS))

    def go_to_checkout(self):
        self.click(*self.CHECKOUT_BUTTON)

    def continue_shopping(self):
        self.click(*self.CONTINUE_BUTTON)


class CheckoutPage(BasePage):
    FIRST_NAME   = (By.ID, "first-name")
    LAST_NAME    = (By.ID, "last-name")
    POSTAL_CODE  = (By.ID, "postal-code")
    CONTINUE_BTN = (By.ID, "continue")
    FINISH_BTN   = (By.ID, "finish")
    SUCCESS_MSG  = (By.CLASS_NAME, "complete-header")
    ERROR_MSG    = (By.CSS_SELECTOR, "[data-test='error']")

    def fill_info(self, first: str, last: str, zip_code: str):
        self.type_text(*self.FIRST_NAME, first)
        self.type_text(*self.LAST_NAME, last)
        self.type_text(*self.POSTAL_CODE, zip_code)

    def continue_checkout(self):
        self.click(*self.CONTINUE_BTN)

    def finish_checkout(self):
        self.click(*self.FINISH_BTN)

    def get_success_message(self) -> str:
        return self.get_text(*self.SUCCESS_MSG)

    def is_error_shown(self) -> bool:
        return self.is_visible(*self.ERROR_MSG)
