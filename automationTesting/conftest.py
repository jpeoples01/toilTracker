# conftest.py
import os
import time
import subprocess
import pytest
from playwright.sync_api import sync_playwright
import os
import sys

APP_URL = "http://localhost:8501"
LOG_FILE = "toil_log.json"

@pytest.fixture(scope="session", autouse=True)
def start_streamlit():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "toilTrackerUI.py", "--server.headless", "true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=root_dir  # run the command from the project root
    )
    time.sleep(5)
    yield
    process.terminate()
    process.wait()


@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=False,
        slow_mo=500
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
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    page = context.new_page()
    page.goto(APP_URL)
    page.wait_for_timeout(1500)
    yield page
    page.close()