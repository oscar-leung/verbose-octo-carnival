"""
Test Suite: Inventory / Product listing — saucedemo.com
Tests sorting, add-to-cart, and cart badge count.
"""

import pytest
from qa_portfolio.pages.inventory_page import InventoryPage


class TestInventory:

    def test_inventory_page_loads_six_products(self, logged_in_driver):
        """Inventory page should show 6 products by default."""
        inv = InventoryPage(logged_in_driver)
        names = inv.get_item_names()
        assert len(names) == 6, f"Expected 6 products, got {len(names)}"

    def test_sort_by_name_az(self, logged_in_driver):
        """Products sort A→Z correctly."""
        inv = InventoryPage(logged_in_driver)
        inv.sort_by("az")
        names = inv.get_item_names()
        assert names == sorted(names), "Products should be sorted A→Z"

    def test_sort_by_name_za(self, logged_in_driver):
        """Products sort Z→A correctly."""
        inv = InventoryPage(logged_in_driver)
        inv.sort_by("za")
        names = inv.get_item_names()
        assert names == sorted(names, reverse=True), "Products should be sorted Z→A"

    def test_sort_by_price_low_to_high(self, logged_in_driver):
        """Products sort by price ascending correctly."""
        inv = InventoryPage(logged_in_driver)
        inv.sort_by("lohi")
        prices = inv.get_item_prices()
        assert prices == sorted(prices), "Prices should be sorted low → high"

    def test_sort_by_price_high_to_low(self, logged_in_driver):
        """Products sort by price descending correctly."""
        inv = InventoryPage(logged_in_driver)
        inv.sort_by("hilo")
        prices = inv.get_item_prices()
        assert prices == sorted(prices, reverse=True), "Prices should be sorted high → low"

    def test_add_single_item_button_changes_to_remove(self, logged_in_driver):
        """After adding an item, its button changes to 'Remove'."""
        from selenium.webdriver.common.by import By
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Backpack")
        # Button text should change to "Remove" after adding
        items = logged_in_driver.find_elements(By.CLASS_NAME, "inventory_item")
        for item in items:
            if item.find_element(By.CLASS_NAME, "inventory_item_name").text == "Sauce Labs Backpack":
                btn = item.find_element(By.XPATH, ".//button[contains(@class,'btn_inventory')]")
                assert btn.text == "Remove", f"Expected 'Remove' button, got: '{btn.text}'"
                return

    def test_add_multiple_items_updates_cart_badge(self, logged_in_driver):
        """Adding two items shows badge count of 2."""
        inv = InventoryPage(logged_in_driver)
        inv.add_item_to_cart("Sauce Labs Backpack")
        inv.add_item_to_cart("Sauce Labs Bike Light")
        assert inv.get_cart_count() == 2, "Cart badge should show 2 after adding two items"
