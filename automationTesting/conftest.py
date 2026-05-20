import pytest
import subprocess
import time
import os
import json
import sys
import base64
from playwright.sync_api import sync_playwright
import requests
from pytest_html import extras

APP_PATH    = os.path.join(os.path.dirname(__file__), '..', 'toilTrackerUI.py')
CLEAN_LOG   = {'entries': [], 'hours_used': 0.0, 'standard_day': 8}
CLEAN_CLOCK = {'date': '', 'events': [], 'work_pattern': '5 days / 40 hours (8h day)'}

# Anchor output dirs to the project root (one level above this conftest)
# so they resolve consistently regardless of the working directory pytest
# is launched from.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_LOGS_DIR = os.path.join(_PROJECT_ROOT, 'dataLogs')
TEST_LOGS_DIR = os.path.join(_PROJECT_ROOT, 'testLogs')
os.makedirs(DATA_LOGS_DIR, exist_ok=True)
os.makedirs(TEST_LOGS_DIR, exist_ok=True)

# Processes started by the controller before xdist workers are spawned.
# Keyed by worker number (0, 1, 2, ...). Empty in single-worker mode.
_streamlit_procs: dict = {}


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def get_worker_id() -> str:
    return os.environ.get("PYTEST_XDIST_WORKER", "gw0")


def _log_path(worker_id: str)   -> str: return os.path.join(DATA_LOGS_DIR, f"toil_log_{worker_id}.json")
def _clock_path(worker_id: str) -> str: return os.path.join(DATA_LOGS_DIR, f"clock_log_{worker_id}.json")


def _write_clean_files(worker_id: str):
    with open(_log_path(worker_id),   'w') as f: json.dump(CLEAN_LOG,   f, indent=2)
    with open(_clock_path(worker_id), 'w') as f: json.dump(CLEAN_CLOCK, f, indent=2)


def reset_log():
    with open(_log_path(get_worker_id()), 'w') as f:
        json.dump(CLEAN_LOG, f, indent=2)


def reset_clock():
    with open(_clock_path(get_worker_id()), 'w') as f:
        json.dump(CLEAN_CLOCK, f, indent=2)


def _stderr_log_path(worker_id: str) -> str:
    return os.path.join(TEST_LOGS_DIR, f"streamlit_stderr_{worker_id}.log")


def _start_streamlit(port: int, worker_id: str) -> subprocess.Popen:
    """Launch a single Streamlit process on the given port.

    stderr goes to a file rather than a pipe — reading from a pipe blocks
    until the process exits (EOF), which would hang the test run.
    The file can be read at any time without blocking.
    """
    env        = {**os.environ, 'PYTEST_XDIST_WORKER': worker_id}
    stderr_log = open(_stderr_log_path(worker_id), 'w')
    return subprocess.Popen(
        [sys.executable, '-m', 'streamlit', 'run', APP_PATH,
         '--server.headless', 'true',
         '--server.port', str(port),
         '--server.fileWatcherType', 'none'],
        stdout=subprocess.DEVNULL,
        stderr=stderr_log,
        env=env,
    )


def _read_stderr_log(worker_id: str, max_bytes: int = 2000) -> str:
    path = _stderr_log_path(worker_id)
    try:
        with open(path) as f:
            return f.read(max_bytes)
    except Exception:
        return '(unreadable)'


def _poll_until_ready(port: int, worker_id: str, timeout: int = 90):
    """Block until the Streamlit HTTP server returns 200, or raise RuntimeError."""
    url   = f"http://localhost:{port}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            if requests.get(url, timeout=3).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)

    raise RuntimeError(
        f"Streamlit on port {port} did not respond within {timeout}s\n"
        f"stderr: {_read_stderr_log(worker_id)}"
    )


def attach_screenshot(report, page, name="screenshot"):
    png  = page.screenshot()
    b64  = base64.b64encode(png).decode("utf-8")
    html = (f'<div><strong>{name}</strong><br>'
            f'<img src="data:image/png;base64,{b64}" style="max-width:100%"/></div>')
    report.extras.append(extras.html(html))


# ─────────────────────────────────────────────
#  Controller-level hooks
#
#  pytest_configure runs once on the main (controller) process
#  BEFORE xdist worker subprocesses are ever created.
#
#  Sequence with xdist -n 4:
#    1. Controller runs pytest_configure  <- we start all 4 instances here
#    2. Controller collects tests
#    3. Controller spawns 4 worker subprocesses
#    4. Workers run tests (instances already warm)
#
#  All Popen calls happen simultaneously so startup runs in parallel.
#  We then do ONE shared wait, so the effective delay equals the
#  slowest single instance — not 4x that time.
# ─────────────────────────────────────────────

def pytest_configure(config):
    # Workers carry workerinput — nothing to do there
    if hasattr(config, 'workerinput'):
        return

    try:
        n = config.option.numprocesses
    except AttributeError:
        return  # xdist not installed

    if not n or n == 'auto':
        return  # count unknown at this point

    n = int(n)
    if n < 2:
        return

    # ── 1. Fire up all instances simultaneously ──
    for i in range(n):
        wid  = f"gw{i}"
        port = 8501 + i
        _write_clean_files(wid)
        _streamlit_procs[i] = (_start_streamlit(port, wid), port)

    # ── 2. Short pause so the OS can bind all ports before polling ──
    time.sleep(5)

    # ── 3. Poll each instance. Because they all started at the same
    #       time, later ones are usually already up by the time we
    #       reach them, so this loop is typically very fast. ──
    failures = []
    for i, (proc, port) in _streamlit_procs.items():
        try:
            _poll_until_ready(port, f"gw{i}", timeout=90)
        except RuntimeError as exc:
            failures.append(str(exc))

    if failures:
        pytest_unconfigure(config)
        raise RuntimeError(
            "One or more Streamlit instances failed to start:\n" +
            "\n".join(failures)
        )


def pytest_unconfigure(config):
    """Terminate all controller-managed Streamlit processes."""
    if hasattr(config, 'workerinput'):
        return
    for proc, _port in list(_streamlit_procs.values()):
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    _streamlit_procs.clear()


# ─────────────────────────────────────────────
#  Session fixture
#  Multi-worker  → instances already running; just reset state
#  Single-worker → start and own the instance here
# ─────────────────────────────────────────────

@pytest.fixture(scope='session')
def streamlit_app():
    worker_id  = get_worker_id()
    worker_num = int(worker_id.replace("gw", "")) if "gw" in worker_id else 0
    port       = 8501 + worker_num

    if _streamlit_procs:
        # Controller started and verified this instance already —
        # workers just reset state files and hand off the port
        reset_log()
        reset_clock()
        yield {"port": port}
        # No process teardown: pytest_unconfigure owns the lifecycle

    else:
        # Single-worker / plain pytest (no -n) — manage lifecycle here
        reset_log()
        reset_clock()
        proc = _start_streamlit(port, worker_id)
        time.sleep(3)
        try:
            _poll_until_ready(port, worker_id, timeout=90)
        except RuntimeError:
            proc.terminate()
            raise

        yield {"port": port, "process": proc}

        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def pytest_addoption(parser):
    parser.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser tests in headed (visible) mode",
    )


# ─────────────────────────────────────────────
#  Browser and page fixtures
# ─────────────────────────────────────────────

@pytest.fixture(scope='session')
def browser(streamlit_app, request):
    headed = request.config.getoption("--headed", default=False)
    with sync_playwright() as p:
        b = p.chromium.launch(headless=not headed)
        yield b
        b.close()


@pytest.fixture(scope='function')
def page(browser, streamlit_app, request):
    reset_log()
    reset_clock()

    url = f"http://localhost:{streamlit_app['port']}"

    context = browser.new_context()

    # Start tracing every test — screenshots and DOM snapshots at each step.
    # On failure the trace is saved to testLogs/ so you can open it with:
    #   playwright show-trace testLogs/trace_<test_name>.zip
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    pg = context.new_page()
    pg.goto(url)
    pg.reload()
    pg.get_by_text("TOIL Tracker").wait_for()
    pg.get_by_text("Calculate").first.wait_for()

    yield pg

    # Save the trace only when the test failed; discard it otherwise
    # to avoid filling testLogs/ with traces for passing tests.
    failed = getattr(request.node, "rep_call", None) and request.node.rep_call.failed
    if failed:
        trace_path = os.path.join(TEST_LOGS_DIR, f"trace_{request.node.name}.zip")
        context.tracing.stop(path=trace_path)
    else:
        context.tracing.stop()

    context.close()


# tryfirst=True ensures rep_call is stored on the node BEFORE fixture
# teardown runs, so the page fixture can read it to decide on trace saving.
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep     = outcome.get_result()

    # Store each phase result on the node so fixtures can check them
    setattr(item, f"rep_{call.when}", rep)

    rep.extras = getattr(rep, "extras", [])
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            attach_screenshot(rep, page, item.name)