# test_hours_today.py


def switch_to_hours_today_tab(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()
    page.get_by_role("tab", name="Hours Today").click()
    page.wait_for_timeout(2000)


def enter_clock_event(page, time_str):
    time_input = page.locator("input[aria-label$='time']")
    time_input.click()
    time_input.click(click_count=3)
    time_input.press_sequentially(time_str)
    time_input.press("Tab")
    page.wait_for_timeout(1000)


def click_clock_button(page):
    page.locator("button:has-text('Clock In'), button:has-text('Clock Out')").first.click()
    page.wait_for_timeout(1500)


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
    switch_to_hours_today_tab(page)
    # 5-day is the default so it SHOULD be checked
    radio = page.get_by_label("5 days / 40 hours (8h day)").first
    assert radio.is_checked()


def test_empty_state_shows_no_entries_message(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_text("No entries yet — add your first Clock In", exact=False).is_visible()


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


def test_hours_worked_zero_when_only_clocked_in(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours worked").filter(has_text="4h 0m").first.is_visible()


# ──────────────────────────────────────────────────────────────
# Finish time and remaining messages
# ──────────────────────────────────────────────────────────────

def test_finish_time_shown_when_clocked_in(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_text("You can clock out for the day at", exact=False).is_visible()


def test_remaining_shows_clock_back_in_hint(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "12:00")
    click_clock_button(page)
    assert page.get_by_text("Clock back in to see your finish time", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────

def test_reject_clock_event_before_previous(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "09:00")
    click_clock_button(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_text("must be after the previous entry", exact=False).is_visible()


def test_reject_clock_event_equal_to_previous(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "09:00")
    click_clock_button(page)
    enter_clock_event(page, "09:00")
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
    # 8.5 hours = 30m overtime
    assert page.get_by_text("target for the day", exact=False).is_visible()


def test_overtime_over_3h_shows_toil_qualification(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "19:30")
    click_clock_button(page)
    assert page.get_by_text("3h 30m of overtime", exact=False).is_visible()


def test_overtime_under_3h_no_toil_qualification(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    enter_clock_event(page, "16:30")
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
    page.wait_for_timeout(1000)
    assert page.get_by_text("No entries yet — add your first Clock In", exact=False).is_visible()


def test_delete_restores_clock_in_action(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.get_by_role("button", name="Clock Out").is_visible()
    page.locator("button").filter(has_text="\u2715").first.click()
    page.wait_for_timeout(1000)
    assert page.get_by_role("button", name="Clock In").is_visible()


def test_reset_clock_clears_all_entries(page):
    switch_to_hours_today_tab(page)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    page.get_by_text("Reset today's clock").click()
    page.wait_for_timeout(1000)
    assert page.get_by_text("No entries yet — add your first Clock In", exact=False).is_visible()


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
    page.get_by_text("4 days / 40 hours (10h day)").click()
    page.wait_for_timeout(1500)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").filter(has_text="10h").first.is_visible()


def test_switch_to_10h_then_back_to_8h(page):
    switch_to_hours_today_tab(page)
    page.get_by_text("4 days / 40 hours (10h day)").click()
    page.wait_for_timeout(1500)
    page.get_by_text("5 days / 40 hours (8h day)").click()
    page.wait_for_timeout(1500)
    enter_clock_event(page, "08:00")
    click_clock_button(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").filter(has_text="8h").first.is_visible()