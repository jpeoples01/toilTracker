# test_hours_today.py


from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _now_hhmm(offset_minutes=0):
    """Current London time offset by the given number of minutes."""
    t = datetime.now(ZoneInfo('Europe/London')) + timedelta(minutes=offset_minutes)
    return t.strftime('%H:%M')


def switch_to_hours_today_tab(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()
    page.get_by_role("tab", name="Hours Today").click()
    # Wait for actual tab content rather than a fixed sleep
    page.locator("input[aria-label$='time']").wait_for(state="visible", timeout=5000)


def enter_clock_event(page, time_str):
    time_input = page.locator("input[aria-label$='time']")
    time_input.click()
    time_input.click(click_count=3)
    time_input.press_sequentially(time_str)
    time_input.press("Tab")
    page.wait_for_timeout(1000)


def click_clock_button(page):
    page.locator("button:has-text('Clock In'), button:has-text('Clock Out')").first.click()
    page.wait_for_timeout(3000)


# ──────────────────────────────────────────────────────────────
# Tab visibility and initial state
# ──────────────────────────────────────────────────────────────

def test_hours_today_tab_visible(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_role("tab", name="Hours Today").is_visible()


def test_hours_today_subheader_visible(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_text("Hours Today", exact=True).first.is_visible()


def test_hours_today_default_working_pattern(page):
    # Shared radio at top of page — single instance, no tab-specific index
    radio = page.get_by_label("5 days / 40 hours (8h day)").first
    assert radio.is_checked()


def test_empty_state_shows_no_entries_message(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_text("No entries yet - add your first Clock In", exact=False).is_visible()


def test_first_action_is_clock_in(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_role("button", name="Clock In").is_visible()


def test_reset_button_visible(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_text("Reset today's clock").is_visible()


def test_time_input_visible(page):
    switch_to_hours_today_tab(page)
    assert page.locator("input[aria-label$='time']").is_visible()


# ──────────────────────────────────────────────────────────────
# Clock in / out basic flow
# ──────────────────────────────────────────────────────────────

def test_clock_in_adds_entry(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_text("08:00").is_visible()


def test_todays_entries_header_shown_after_clock_in(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_text("Today's entries", exact=False).is_visible()


def test_after_clock_in_next_action_is_clock_out(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_role("button", name="Clock Out").is_visible()


def test_after_clock_out_next_action_is_clock_in(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    assert page.get_by_role("button", name="Clock In").is_visible()


# ──────────────────────────────────────────────────────────────
# Multiple clock cycles
# ──────────────────────────────────────────────────────────────

def test_multiple_clock_cycles(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    enter_clock_event(page, "13:00")
    click_clock_button(page)
    enter_clock_event(page, "17:00")
    click_clock_button(page)
    assert page.get_by_text("08:00").is_visible()
    assert page.get_by_text("12:00").is_visible()
    assert page.get_by_text("13:00").is_visible()
    assert page.get_by_text("17:00").is_visible()


def test_multiple_cycles_hours_worked_correct(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    enter_clock_event(page, "13:00")
    click_clock_button(page)
    enter_clock_event(page, "17:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours worked").filter(has_text="8h 0m").first.is_visible()


# ──────────────────────────────────────────────────────────────
# Metrics
# ──────────────────────────────────────────────────────────────

def test_metrics_visible_after_clock_in(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours worked").first.is_visible()
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").first.is_visible()
    assert page.get_by_text("Remaining", exact=True).is_visible()


def test_target_shows_8h_for_default_pattern(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").filter(has_text="8h").first.is_visible()


def test_hours_worked_after_clock_out(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours worked").filter(has_text="4h 0m").first.wait_for(state="visible", timeout=8000)


# ──────────────────────────────────────────────────────────────
# Finish time and remaining messages
# ──────────────────────────────────────────────────────────────

def test_finish_time_shown_when_clocked_in(page):
    switch_to_hours_today_tab(page)
    # Use a time 30 minutes ago so live_minutes_remaining is always positive
    # regardless of when the test runs. Hardcoding "08:00" breaks in the
    # afternoon because the app calculates live_elapsed = now - cin_time,
    # and once that exceeds the 8h target it shows overtime instead.
    enter_clock_event(page, _now_hhmm(-30))
    click_clock_button(page)
    page.get_by_text("Finish time:", exact=False).wait_for(state="visible", timeout=10000)


def test_clocked_out_shows_projected_finish(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    page.get_by_text("If you clock back in now", exact=False).wait_for(state="visible", timeout=8000)


# ──────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────

def test_reject_clock_event_before_previous(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, _now_hhmm(-60))
    click_clock_button(page)
    enter_clock_event(page, _now_hhmm(-90))
    click_clock_button(page)
    assert page.get_by_text("must be after the previous entry", exact=False).is_visible()


def test_reject_clock_event_equal_to_previous(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, _now_hhmm(-60))
    click_clock_button(page)
    enter_clock_event(page, _now_hhmm(-60))
    click_clock_button(page)
    assert page.get_by_text("must be after the previous entry", exact=False).is_visible()


def test_invalid_time_format_shows_error(page):
    switch_to_hours_today_tab(page)
    time_input = page.locator("input[aria-label$='time']")
    time_input.click()
    time_input.click(click_count=3)
    time_input.press_sequentially("abc")
    time_input.press("Tab")
    page.wait_for_timeout(1000)
    click_clock_button(page)
    assert page.get_by_text("valid time in HH:MM format", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Overtime messages
# ──────────────────────────────────────────────────────────────

def test_overtime_message_shown_after_target_met(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "16:30")
    click_clock_button(page)
    # 8h 30m worked = 30m overtime
    page.get_by_text("target for the day", exact=False).wait_for(state="visible", timeout=8000)


def test_overtime_amount_shown_correctly(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "19:30")
    click_clock_button(page)
    # 11h 30m worked = 3h 30m overtime
    page.get_by_text("3h 30m of overtime", exact=False).wait_for(state="visible", timeout=8000)


def test_no_toil_qualification_message_in_hours_today(page):
    # Hours Today tab never shows TOIL qualification - that lives in the annual tab
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "19:30")
    click_clock_button(page)
    assert not page.get_by_text("qualifies for annual TOIL pot", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Delete and reset
# ──────────────────────────────────────────────────────────────

def test_delete_entry(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_text("08:00").is_visible()
    page.locator("button").filter(has_text="\u2715").first.click()
    page.get_by_text("No entries yet - add your first Clock In", exact=False).wait_for(state="visible", timeout=5000)


def test_delete_restores_clock_in_action(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    page.get_by_role("button", name="Clock Out").wait_for(state="visible", timeout=8000)
    page.locator("button").filter(has_text="\u2715").first.click()
    page.get_by_role("button", name="Clock In").wait_for(state="visible", timeout=5000)


def test_reset_clock_clears_all_entries(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    page.get_by_text("Reset today's clock").click()
    page.get_by_text("No entries yet - add your first Clock In", exact=False).wait_for(state="visible", timeout=5000)


def test_reset_restores_clock_in_action(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_role("button", name="Clock Out").is_visible()
    page.get_by_text("Reset today's clock").click()
    page.wait_for_timeout(1000)
    assert page.get_by_role("button", name="Clock In").is_visible()


# ──────────────────────────────────────────────────────────────
# Working pattern changes
# ──────────────────────────────────────────────────────────────

def test_10h_day_pattern_changes_target(page):
    switch_to_hours_today_tab(page)
    page.get_by_text("4 days / 40 hours (10h day)", exact=True).first.click()
    page.wait_for_timeout(1500)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").filter(has_text="10h").first.is_visible()


def test_switch_to_10h_then_back_to_8h(page):
    switch_to_hours_today_tab(page)
    page.get_by_text("4 days / 40 hours (10h day)", exact=True).first.click()
    page.wait_for_timeout(1500)
    page.get_by_text("5 days / 40 hours (8h day)", exact=True).first.click()
    page.wait_for_timeout(1500)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").filter(has_text="8h").first.is_visible()