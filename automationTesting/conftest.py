import pytest
import subprocess
import time
import os
import json
import sys
from playwright.sync_api import sync_playwright
import requests
import allure

APP_PATH = os.path.join(os.path.dirname(__file__), '..', 'toilTrackerUI.py')
APP_URL = 'http://localhost:8501'
LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'toil_log.json')
CLOCK_FILE = os.path.join(os.path.dirname(__file__), '..', 'clock_log.json')
CLEAN_LOG = {'entries': [], 'hours_used': 0.0, 'standard_day': 8}
CLEAN_CLOCK = {'date': '', 'events': [], 'work_pattern': '5 days / 40 hours (8h day)'}



def attach_screenshot(page, name="screenshot"):
    allure.attach(
        page.screenshot(),
        name=name,
        attachment_type=allure.attachment_type.PNG
    )

def wait_for_app(port, timeout=30):
    url = f"http://localhost:{port}"
    start = time.time()

    while time.time() - start < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200 and "TOIL Tracker" in r.text:
                return
        except:
            pass
        wait_for_app(port)

    raise RuntimeError(f"Streamlit app on port {port} did not fully render in time")

def reset_log():
    with open(LOG_FILE, 'w') as f:
        json.dump(CLEAN_LOG, f, indent=2)


def reset_clock():
    with open(CLOCK_FILE, 'w') as f:
        json.dump(CLEAN_CLOCK, f, indent=2)

def get_worker_id():
    return os.environ.get("PYTEST_XDIST_WORKER", "gw0")


WORKER_ID = get_worker_id()


LOG_FILE = f"toil_log_{WORKER_ID}.json"
CLOCK_FILE = f"clock_log_{WORKER_ID}.json"

@pytest.fixture(scope='session')
def streamlit_app():
    worker_id = get_worker_id()
    worker_num = int(worker_id.replace("gw", "")) if "gw" in worker_id else 0
    port = 8501 + worker_num

    reset_log()
    reset_clock()

    proc = subprocess.Popen(
        [sys.executable, '-m', 'streamlit', 'run', APP_PATH,
         '--server.headless', 'true',
         '--server.port', str(port),
         '--server.fileWatcherType', 'none'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(5)

    yield {
        "process": proc,
        "port": port
    }

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


# browser is session-scoped — launched once, shared across all tests
# this avoids the TargetClosedError from launching 60+ browsers in one session
@pytest.fixture(scope='session')
def browser(streamlit_app):
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture(scope='function')
def page(browser, streamlit_app):
    reset_log()
    reset_clock()

    port = streamlit_app["port"]
    url = f"http://localhost:{port}"

    context = browser.new_context()
    pg = context.new_page()
    pg.goto(url)
    pg.reload()
    pg.get_by_text("TOIL Tracker").wait_for()
    pg.get_by_text("Calculate").first.wait_for()


    yield pg
    context.close()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            attach_screenshot(page, item.name)