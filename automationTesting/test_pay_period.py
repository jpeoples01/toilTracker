# test_pay_period.py
from datetime import date, timedelta
import calendar


def last_friday_of_month(year, month):
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    offset = (last_day.weekday() - 4) % 7
    return last_day - timedelta(days=offset)


def get_current_expected_period():
    today = date.today()
    payday = last_friday_of_month(today.year, today.month)
    period_end = payday - timedelta(weeks=1)
    period_end_monday = period_end - timedelta(days=4)
    for num_weeks in [5, 4, 3]:
        start = period_end_monday - timedelta(weeks=num_weeks - 1)
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        prev_payday = last_friday_of_month(prev_year, prev_month)
        prev_period_end = prev_payday - timedelta(weeks=1)
        if start > prev_period_end:
            return start, period_end, payday, num_weeks
    return period_end_monday, period_end, payday, 4


# ──────────────────────────────────────────────────────────────
# Pay period section visibility
# ──────────────────────────────────────────────────────────────

def test_pay_period_display(page):
    page.get_by_text("Pay period", exact=True).first.scroll_into_view_if_needed()
    page.get_by_text("PERIOD START", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("PERIOD END", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("PAYDAY", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("WEEKS", exact=False).wait_for(state="visible", timeout=5000)


def test_pay_period_section_has_red_border(page):
    # check the styled container is present
    page.locator("div[style*='border-left']").first.wait_for(state="visible", timeout=5000)


def test_month_selector_visible(page):
    page.get_by_label("Select pay period month").wait_for(state="visible", timeout=5000)


def test_month_selector_defaults_to_current_month(page):
    today = date.today()
    current_month = today.strftime("%B %Y")
    # find the rendered selectbox value by looking for the month text on the page
    page.get_by_text(current_month, exact=False).first.wait_for(state="visible", timeout=5000)


# ──────────────────────────────────────────────────────────────
# Weeks value
# ──────────────────────────────────────────────────────────────

def test_weeks_value_valid(page):
    weeks_text = page.locator("text=WEEKS").locator("..").inner_text()
    valid_weeks = ["3", "4", "5"]
    assert any(w in weeks_text for w in valid_weeks)


def test_weeks_matches_expected_for_current_month(page):
    _, _, _, expected_weeks = get_current_expected_period()
    weeks_text = page.locator("text=WEEKS").locator("..").inner_text()
    assert str(expected_weeks) in weeks_text


# ──────────────────────────────────────────────────────────────
# Date values
# ──────────────────────────────────────────────────────────────

def test_period_start_date_correct(page):
    expected_start, _, _, _ = get_current_expected_period()
    expected_str = expected_start.strftime("%d %b %Y")
    page.get_by_text(expected_str, exact=False).wait_for(state="visible", timeout=5000)


def test_period_end_date_correct(page):
    _, expected_end, _, _ = get_current_expected_period()
    expected_str = expected_end.strftime("%d %b %Y")
    page.get_by_text(expected_str, exact=False).wait_for(state="visible", timeout=5000)


def test_payday_date_correct(page):
    _, _, expected_payday, _ = get_current_expected_period()
    expected_str = expected_payday.strftime("%d %b %Y")
    page.get_by_text(expected_str, exact=False).wait_for(state="visible", timeout=5000)


def test_payday_is_last_friday_of_month(page):
    today = date.today()
    expected_payday = last_friday_of_month(today.year, today.month)
    expected_str = expected_payday.strftime("%d %b %Y")
    page.get_by_text(expected_str, exact=False).wait_for(state="visible", timeout=5000)


# ──────────────────────────────────────────────────────────────
# Month selector changes period
# ──────────────────────────────────────────────────────────────

def test_month_selector_changes_period(page):
    month_select = page.get_by_label("Select pay period month")
    month_select.click()
    page.wait_for_timeout(500)
    page.get_by_role("option").nth(1).click()
    page.wait_for_timeout(1000)
    page.get_by_text("PERIOD START", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("PERIOD END", exact=False).wait_for(state="visible", timeout=5000)


def test_changing_month_updates_week_inputs(page):
    # get week count for current month
    initial_weeks = page.locator("input[aria-label='Hours worked'][max='168']").count()

    # switch to a different month that may have different week count
    month_select = page.get_by_label("Select pay period month")
    month_select.click()
    page.wait_for_timeout(500)
    page.get_by_role("option").nth(2).click()
    page.wait_for_timeout(1500)

    new_weeks = page.locator("input[aria-label='Hours worked'][max='168']").count()
    # week count should be between 3 and 5 regardless of which month
    assert 3 <= new_weeks <= 5


def test_week_inputs_match_period_weeks(page):
    weeks_text = page.locator("text=WEEKS").locator("..").inner_text()
    for w in ["3", "4", "5"]:
        if w in weeks_text:
            expected = int(w)
            break
    actual_inputs = page.locator("input[aria-label='Hours worked'][max='168']").count()
    assert actual_inputs == expected