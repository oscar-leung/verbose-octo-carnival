"""
Test Suite: Login functionality — saucedemo.com
Tests positive login, negative login, and locked-out user flows.
"""

import pytest
from qa_portfolio.pages.login_page import LoginPage


class TestLogin:

    def test_valid_login_redirects_to_inventory(self, driver):
        """Standard user can log in and reaches inventory page."""
        lp = LoginPage(driver)
        lp.open()
        lp.login("standard_user", "secret_sauce")
        assert "inventory" in driver.current_url, \
            f"Expected inventory URL, got: {driver.current_url}"

    def test_invalid_password_shows_error(self, driver):
        """Wrong password shows error message."""
        lp = LoginPage(driver)
        lp.open()
        lp.login("standard_user", "wrong_password")
        assert lp.is_error_displayed(), "Error message should be visible"
        assert "Username and password do not match" in lp.get_error_message()

    def test_locked_out_user_shows_error(self, driver):
        """Locked-out user sees appropriate error."""
        lp = LoginPage(driver)
        lp.open()
        lp.login("locked_out_user", "secret_sauce")
        assert lp.is_error_displayed()
        assert "locked out" in lp.get_error_message().lower()

    def test_empty_username_shows_error(self, driver):
        """Empty username field shows validation error."""
        lp = LoginPage(driver)
        lp.open()
        lp.login("", "secret_sauce")
        assert lp.is_error_displayed()
        assert "Username is required" in lp.get_error_message()

    def test_empty_password_shows_error(self, driver):
        """Empty password field shows validation error."""
        lp = LoginPage(driver)
        lp.open()
        lp.login("standard_user", "")
        assert lp.is_error_displayed()
        assert "Password is required" in lp.get_error_message()

    def test_logout_returns_to_login(self, logged_in_driver):
        """Logged-in user can log out and return to login page."""
        from qa_portfolio.pages.inventory_page import InventoryPage
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait
        inv = InventoryPage(logged_in_driver)
        inv.logout()
        # Wait until URL no longer contains inventory
        WebDriverWait(logged_in_driver, 8).until(
            lambda d: "inventory" not in d.current_url
        )
        assert "inventory" not in logged_in_driver.current_url, \
            f"Should not be on inventory page after logout, got: {logged_in_driver.current_url}"
