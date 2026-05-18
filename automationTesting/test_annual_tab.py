# test_annual_tab.py


def switch_to_annual_tab(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()
    page.get_by_text("TOIL ANNUAL LEAVE ACCRUEMENT").click()
    page.wait_for_timeout(1000)


def enter_hours_worked(page, hours_str):
    input_hours = page.locator("input[aria-label='Hours worked'][max='24']")
    input_hours.click()
    input_hours.click(click_count=3)
    input_hours.press_sequentially(hours_str)
    input_hours.press("Tab")
    page.wait_for_timeout(1500)


def click_add_to_log(page):
    page.get_by_text("Add to log").click()
    page.wait_for_timeout(1500)


def click_4_day_radio(page):
    # Streamlit hides the <input> — click the visible label text instead
    page.get_by_text("4 days / 40 hours", exact=True).nth(1).click()
    page.wait_for_timeout(1500)


# ──────────────────────────────────────────────────────────────
# Tab visibility and initial state
# ──────────────────────────────────────────────────────────────

def test_annual_tab_metrics_visible(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("Hours banked").is_visible()
    assert page.get_by_text("Hours used", exact=True).first.is_visible()
    assert page.get_by_text("Hours remaining").is_visible()


def test_annual_default_working_pattern(page):
    switch_to_annual_tab(page)
    radio = page.get_by_label("5 days / 40 hours").nth(1)
    assert radio.is_checked()


def test_annual_unselected_working_pattern(page):
    switch_to_annual_tab(page)
    radio = page.get_by_label("4 days / 40 hours").nth(1)
    assert not radio.is_checked()


def test_qualification_caption_visible(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("Qualification for Annual TOIL", exact=False).is_visible()


def test_qualification_caption_shows_8h_threshold(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("8h work day with 3h+ overtime", exact=False).is_visible()


def test_log_overtime_subheader_visible(page):
    switch_to_annual_tab(page)
    # use exact=True to avoid matching the empty state message which also contains this text
    assert page.get_by_text("Log an overtime day", exact=True).is_visible()


def test_toil_hours_used_subheader_visible(page):
    switch_to_annual_tab(page)
    # scope to the subheader specifically, not the input label
    assert page.get_by_role("heading").filter(has_text="TOIL hours used").is_visible()


def test_log_subheader_visible(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("Log", exact=True).first.is_visible()


def test_log_empty_message(page):
    switch_to_annual_tab(page)
    # use the full specific string to avoid matching the Hours Today tab's empty message
    assert page.get_by_text("No entries yet — log an overtime day above.", exact=True).is_visible()


def test_initial_metrics_are_zero(page):
    switch_to_annual_tab(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.0h").first.is_visible()
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="0.0h").first.is_visible()
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours remaining").filter(has_text="0.0h").first.is_visible()


def test_days_equivalent_captions_visible(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("days banked", exact=False).is_visible()
    assert page.get_by_text("days left to take", exact=False).is_visible()


def test_clear_all_button_visible(page):
    switch_to_annual_tab(page)
    assert page.get_by_text("Clear all TOIL data", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Preview messages (before clicking Add)
# ──────────────────────────────────────────────────────────────

def test_preview_qualifies_annual_toil(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    assert page.get_by_text("qualifies for annual TOIL pot", exact=False).is_visible()


def test_preview_below_threshold_shows_flexi(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "10")
    assert page.get_by_text("below 3h threshold, counts toward monthly flexi only", exact=False).is_visible()


def test_preview_no_overtime_warning(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "8")
    assert page.get_by_text("No overtime on this day", exact=False).is_visible()


def test_preview_zero_hours_no_message(page):
    switch_to_annual_tab(page)
    assert not page.get_by_text("qualifies for annual TOIL pot", exact=False).is_visible()
    assert not page.get_by_text("monthly flexi only", exact=False).is_visible()
    assert not page.get_by_text("No overtime on this day", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Adding entries
# ──────────────────────────────────────────────────────────────

def test_add_valid_overtime_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    assert page.get_by_text("12.0h worked", exact=False).is_visible()


def test_added_entry_shows_toil_hours(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    assert page.get_by_text("+4.0h TOIL", exact=False).is_visible()


def test_metrics_update_after_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="4.0h").first.is_visible()


def test_reject_below_threshold_overtime(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "9")
    click_add_to_log(page)
    assert page.get_by_text("does not meet the 3h overtime threshold", exact=False).is_visible()


def test_reject_exact_standard_day_hours(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "8")
    click_add_to_log(page)
    assert page.get_by_text("does not meet the 3h overtime threshold", exact=False).is_visible()


def test_entry_not_added_when_rejected(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "9")
    click_add_to_log(page)
    # use full specific string to avoid matching Hours Today tab's empty message
    assert page.get_by_text("No entries yet — log an overtime day above.", exact=True).is_visible()


# ──────────────────────────────────────────────────────────────
# Hours used
# ──────────────────────────────────────────────────────────────

def test_hours_used_update(page):
    switch_to_annual_tab(page)
    page.get_by_label("Total TOIL hours used this year").fill("4")
    page.get_by_text("Update hours used").click()
    page.wait_for_timeout(1500)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="4.0h").first.is_visible()


def test_hours_remaining_after_usage(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_label("Total TOIL hours used this year").fill("2")
    page.get_by_text("Update hours used").click()
    page.wait_for_timeout(1500)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours remaining").filter(has_text="2.0h").first.is_visible()


# ──────────────────────────────────────────────────────────────
# Delete entry
# ──────────────────────────────────────────────────────────────

def test_delete_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    assert page.get_by_text("12.0h worked", exact=False).is_visible()
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1500)
    assert page.get_by_text("No entries yet — log an overtime day above.", exact=True).is_visible()


def test_delete_entry_updates_metrics(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1500)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.0h").first.is_visible()


# ──────────────────────────────────────────────────────────────
# Clear all data
# ──────────────────────────────────────────────────────────────

def test_clear_all_shows_confirmation(page):
    switch_to_annual_tab(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    assert page.get_by_text("Are you sure?", exact=False).is_visible()
    assert page.get_by_text("Yes, clear everything", exact=False).is_visible()
    assert page.get_by_text("Cancel", exact=True).first.is_visible()


def test_clear_all_cancel_preserves_data(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Cancel", exact=True).first.click()
    page.wait_for_timeout(1500)
    assert page.get_by_text("12.0h worked", exact=False).is_visible()


def test_clear_all_confirm_resets_data(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Yes, clear everything").click()
    page.wait_for_timeout(1500)
    assert page.get_by_text("No entries yet — log an overtime day above.", exact=True).is_visible()


def test_clear_all_resets_metrics(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_label("Total TOIL hours used this year").fill("2")
    page.get_by_text("Update hours used").click()
    page.wait_for_timeout(1500)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Yes, clear everything").click()
    page.wait_for_timeout(1500)
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.0h").first.is_visible()
    assert page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="0.0h").first.is_visible()


# ──────────────────────────────────────────────────────────────
# Working pattern switch
# ──────────────────────────────────────────────────────────────

def test_switch_to_4_day_updates_caption(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    assert page.get_by_text("10h work day with 3h+ overtime", exact=False).is_visible()


def test_4_day_pattern_rejects_12h_as_below_threshold(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    assert page.get_by_text("does not meet the 3h overtime threshold", exact=False).is_visible()


def test_4_day_pattern_accepts_14h(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    enter_hours_worked(page, "14")
    click_add_to_log(page)
    assert page.get_by_text("14.0h worked", exact=False).is_visible()