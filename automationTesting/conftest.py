# conftest.py
import os
import pytest
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8501"
LOG_FILE = "toil_log.json"


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=False
    )
    yield browser
    browser.close()


@pytest.fixture(scope="session")
def context(browser):
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    # Clean slate per test
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    page = context.new_page()
    page.goto(APP_URL)
    page.wait_for_timeout(1500)  # Streamlit hydration
    yield page
    page.close()