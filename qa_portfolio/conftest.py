"""
pytest fixtures — driver setup and teardown for all tests.
Uses Page Object Model (POM) pattern.

Site under test: https://www.saucedemo.com
(Built specifically for QA automation practice)
"""

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def pytest_addoption(parser):
    parser.addoption(
        "--headless", action="store_true", default=False,
        help="Run tests in headless Chrome"
    )


@pytest.fixture(scope="function")
def driver(request):
    """Provide a configured Chrome WebDriver, quit after each test."""
    opts = Options()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    if request.config.getoption("--headless"):
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")

    d = webdriver.Chrome(options=opts)
    d.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"},
    )
    d.set_window_size(1440, 900)
    d.implicitly_wait(5)
    yield d
    d.quit()


@pytest.fixture(scope="function")
def logged_in_driver(driver):
    """Driver already logged in as standard_user."""
    from qa_portfolio.pages.login_page import LoginPage
    lp = LoginPage(driver)
    lp.open()
    lp.login("standard_user", "secret_sauce")
    yield driver
