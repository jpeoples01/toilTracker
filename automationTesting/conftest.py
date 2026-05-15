import pytest
import subprocess
import time
import os
import json
import signal
from playwright.sync_api import sync_playwright, Page

APP_PATH = os.path.join(os.path.dirname(__file__), '..', 'toilTrackerUI.py')
APP_URL = 'http://localhost:8501'
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'toil_log.json')
CLOCK_FILE = os.path.join(os.path.dirname(__file__), '..', 'clock_log.json')
CLEAN_LOG = {'entries': [], 'hours_used': 0.0, 'standard_day': 8}


def reset_log():
    with open(LOG_FILE, 'w') as f:
        json.dump(CLEAN_LOG, f, indent=2)


def reset_clock():
    if os.path.exists(CLOCK_FILE):
        os.remove(CLOCK_FILE)


@pytest.fixture(scope='session')
def streamlit_app():
    reset_log()
    reset_clock()
    proc = subprocess.Popen(
        ['python', '-m', 'streamlit', 'run', APP_PATH,
         '--server.headless', 'true',
         '--server.port', '8501',
         '--server.fileWatcherType', 'none'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    # wait for app to be ready
    time.sleep(5)
    yield proc
    proc.send_signal(signal.SIGTERM)
    proc.wait()


@pytest.fixture(scope='function')
def page(streamlit_app):
    reset_log()
    reset_clock()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        pg = context.new_page()
        pg.goto(APP_URL)
        pg.wait_for_load_state('networkidle')
        # wait for Streamlit to finish rendering
        time.sleep(2)
        yield pg
        context.close()
        browser.close()


def go_to_tab(page: Page, tab_name: str):
    page.get_by_role('tab', name=tab_name).click()
    time.sleep(1)