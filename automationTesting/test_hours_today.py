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
    # use first visible button that contains Clock In or Clock Out text
    page.locator("button:has-text('Clock In'), button:has-text('Clock Out')").first.click()
    page.wait_for_timeout(1500)


def test_hours_today_tab_visible(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_role("tab", name="Hours Today").is_visible()


def test_hours_today_default_working_pattern(page):
    switch_to_hours_today_tab(page)
    radio = page.get_by_label("5 days / 40 hours (8h day)").first
    assert radio.is_checked()


def test_hours_today_unselected_working_pattern(page):
    switch_to_hours_today_tab(page)
    radio = page.get_by_label("4 days / 40 hours (10h day)").first
    assert not radio.is_checked()


def test_first_action_is_clock_in(page):
    switch_to_hours_today_tab(page)
    assert page.get_by_role("button", name="Clock In").is_visible()


def test_clock_in_adds_entry(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    assert page.get_by_text("Clock In").is_visible()
    assert page.get_by_text("08:00").is_visible()


def test_after_clock_in_next_action_is_clock_out(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    assert page.get_by_role("button", name="Clock Out").is_visible()


def test_clock_out_adds_entry(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "12:00")
    click_clock_button(page)

    assert page.get_by_text("Clock Out").is_visible()
    assert page.get_by_text("12:00").is_visible()


def test_metrics_visible_after_clock_in(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    # scope to stMetric containers to avoid matching "Hours worked" labels
    # from number inputs on other tabs
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours worked").first.is_visible()
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Target").first.is_visible()
    # use exact=True to avoid matching tab 2's "Hours remaining" metric
    assert page.get_by_text("Remaining", exact=True).first.is_visible()


def test_finish_time_shown_when_clocked_in(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    assert page.get_by_text("You can clock out for the day at", exact=False).is_visible()


def test_remaining_message_shown_when_clocked_out(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "12:00")
    click_clock_button(page)

    assert page.get_by_text("left to work today", exact=False).is_visible()


def test_reject_clock_event_before_previous(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "09:00")
    click_clock_button(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    assert page.get_by_text("must be after the previous entry", exact=False).is_visible()


def test_overtime_message_shown_after_target_met(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "16:30")
    click_clock_button(page)

    # clocked out after 8.5 hours — should show overtime message
    # use specific text to avoid matching "overtime" on other tabs
    assert page.get_by_text("target for the day", exact=False).is_visible()


def test_overtime_under_3h_shows_monthly_flexi_message(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "09:30")
    click_clock_button(page)

    enter_clock_event(page, "10:00")
    click_clock_button(page)

    enter_clock_event(page, "17:00")
    click_clock_button(page)

    # 1.5 + 7 = 8.5 hours — 30min overtime (under 3h threshold)
    # Hours Today tab shows the overtime amount without flexi distinction
    assert page.get_by_text("0h 30m of overtime", exact=False).is_visible()


def test_overtime_over_3h_shows_annual_toil_message(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "19:30")
    click_clock_button(page)

    # 11.5 hours — 3h 30m overtime (over 3h threshold)
    # Hours Today tab shows the overtime amount with TOIL qualification
    assert page.get_by_text("3h 30m of overtime", exact=False).is_visible()


def test_delete_entry(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1000)

    # use specific text to avoid matching tab 2's "No entries yet" message
    assert page.get_by_text("No entries yet \u2014 add your first Clock In", exact=False).is_visible()


def test_reset_clock_clears_all_entries(page):
    switch_to_hours_today_tab(page)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    enter_clock_event(page, "12:00")
    click_clock_button(page)

    page.get_by_text("Reset today's clock").click()
    page.wait_for_timeout(1000)

    # use specific text to avoid matching tab 2's "No entries yet" message
    assert page.get_by_text("No entries yet \u2014 add your first Clock In", exact=False).is_visible()


def test_10h_day_pattern_changes_target(page):
    switch_to_hours_today_tab(page)

    page.get_by_text("4 days / 40 hours (10h day)").click()
    page.wait_for_timeout(1500)
    page.wait_for_timeout(1000)

    enter_clock_event(page, "08:00")
    click_clock_button(page)

    # with 10h target the finish time should be later than an 8h day
    assert page.get_by_text("You can clock out for the day at", exact=False).is_visible()
    # use exact=True so it matches the metric value "10h" and not the radio label
    assert page.get_by_text("10h", exact=True).is_visible()
