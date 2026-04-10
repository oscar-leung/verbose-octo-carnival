"""
Test Suite: Checkout flow — saucedemo.com
Tests end-to-end purchase flow and input validation.
"""

import pytest
from qa_portfolio.pages.inventory_page import InventoryPage
from qa_portfolio.pages.cart_page import CartPage, CheckoutPage


class TestCheckout:

    def test_full_checkout_flow_succeeds(self, logged_in_driver):
        """Complete purchase flow from inventory → order confirmation."""
        # Add item
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Backpack")
        inv.go_to_cart()

        # Cart has item
        cart = CartPage(logged_in_driver)
        assert "Sauce Labs Backpack" in cart.get_cart_item_names()
        cart.go_to_checkout()

        # Fill checkout info
        checkout = CheckoutPage(logged_in_driver)
        checkout.fill_info("Oscar", "Leung", "95050")
        checkout.continue_checkout()
        checkout.finish_checkout()

        # Confirm success
        msg = checkout.get_success_message()
        assert "Thank you" in msg, f"Expected Thank you message, got: {msg}"

    def test_checkout_empty_first_name_shows_error(self, logged_in_driver):
        """Missing first name in checkout shows validation error."""
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Backpack")
        inv.go_to_cart()

        cart = CartPage(logged_in_driver)
        cart.go_to_checkout()

        checkout = CheckoutPage(logged_in_driver)
        checkout.fill_info("", "Leung", "95050")
        checkout.continue_checkout()

        assert checkout.is_error_shown(), "Error should appear when first name is missing"

    def test_cart_item_persists_after_page_reload(self, logged_in_driver):
        """Items added to cart persist after navigating away and back."""
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Fleece Jacket")

        # Navigate away then back to cart
        inv.open()
        inv.go_to_cart()

        cart = CartPage(logged_in_driver)
        assert cart.get_cart_item_count() == 1, "Item should persist in cart after navigation"

    def test_cart_empty_after_successful_purchase(self, logged_in_driver):
        """Cart is empty after completing a purchase."""
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Onesie")
        inv.go_to_cart()

        cart = CartPage(logged_in_driver)
        cart.go_to_checkout()

        checkout = CheckoutPage(logged_in_driver)
        checkout.fill_info("Oscar", "Leung", "95050")
        checkout.continue_checkout()
        checkout.finish_checkout()

        # Go back to inventory — cart should be empty
        inv.open()
        assert inv.get_cart_count() == 0, "Cart should be empty after completed purchase"
