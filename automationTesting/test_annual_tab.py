# test_annual_tab.py


def switch_to_annual_tab(page):
    page.get_by_text("TOIL MONTHLY TRACKER").wait_for(state="visible", timeout=5000)
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
    # Shared radio at top of page — full label text, no per-tab index needed
    page.get_by_text("4 days / 40 hours (10h day)", exact=True).first.click()
    page.wait_for_timeout(1500)


def confirm_delete(page):
    """Click the inline confirm button that appears after pressing ✕."""
    page.get_by_text("Confirm delete").click()
    page.wait_for_timeout(1500)


# ──────────────────────────────────────────────────────────────
# Tab visibility and initial state
# ──────────────────────────────────────────────────────────────

def test_annual_tab_metrics_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("Hours banked").wait_for(state="visible", timeout=5000)
    page.get_by_text("Hours used", exact=True).first.wait_for(state="visible", timeout=5000)
    page.get_by_text("Hours remaining").wait_for(state="visible", timeout=5000)


def test_annual_default_working_pattern(page):
    # Single shared radio at top of page — no per-tab nth index
    radio = page.get_by_label("5 days / 40 hours (8h day)").first
    assert radio.is_checked()


def test_annual_unselected_working_pattern(page):
    radio = page.get_by_label("4 days / 40 hours (10h day)").first
    assert not radio.is_checked()


def test_qualification_caption_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("Qualification for Annual TOIL", exact=False).wait_for(state="visible", timeout=5000)


def test_qualification_caption_shows_8h_threshold(page):
    switch_to_annual_tab(page)
    page.get_by_text("8h work day with 3h+ overtime", exact=False).wait_for(state="visible", timeout=5000)


def test_log_overtime_subheader_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("Log an overtime day", exact=True).wait_for(state="visible", timeout=5000)


def test_toil_hours_used_subheader_visible(page):
    switch_to_annual_tab(page)
    page.get_by_role("heading").filter(has_text="TOIL hours used").wait_for(state="visible", timeout=5000)


def test_log_subheader_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("Log", exact=True).first.wait_for(state="visible", timeout=5000)


def test_log_empty_message(page):
    switch_to_annual_tab(page)
    page.get_by_text("No entries yet - log an overtime day above.", exact=True).wait_for(state="visible", timeout=5000)


def test_initial_metrics_are_zero(page):
    switch_to_annual_tab(page)
    # Metrics now render with .2f precision (e.g. "0.00h" not "0.0h")
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours remaining").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)


def test_days_equivalent_captions_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("days banked", exact=False).wait_for(state="visible", timeout=5000)
    # Caption wording changed from "days left to take" → "days remaining to take"
    page.get_by_text("days remaining to take", exact=False).wait_for(state="visible", timeout=5000)


def test_clear_all_button_visible(page):
    switch_to_annual_tab(page)
    page.get_by_text("Clear all TOIL data", exact=False).wait_for(state="visible", timeout=5000)


# ──────────────────────────────────────────────────────────────
# Preview messages (before clicking Add)
# ──────────────────────────────────────────────────────────────

def test_preview_qualifies_annual_toil(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    page.get_by_text("qualifies for annual TOIL pot", exact=False).wait_for(state="visible", timeout=5000)


def test_preview_below_threshold_shows_flexi(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "10")
    page.get_by_text("below 3h threshold, counts toward monthly flexi only", exact=False).wait_for(state="visible", timeout=5000)


def test_preview_standard_day_shows_no_overtime(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "8")
    # Message changed from "No overtime on this day" → "Exactly a standard day — no overtime"
    page.get_by_text("Exactly a standard day", exact=False).wait_for(state="visible", timeout=5000)


def test_preview_zero_hours_no_message(page):
    switch_to_annual_tab(page)
    assert not page.get_by_text("qualifies for annual TOIL pot", exact=False).is_visible()
    assert not page.get_by_text("monthly flexi only", exact=False).is_visible()
    assert not page.get_by_text("Exactly a standard day", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Adding entries
# ──────────────────────────────────────────────────────────────

def test_add_valid_overtime_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    # Log entries now render with .2f precision
    page.get_by_text("12.00h worked", exact=False).wait_for(state="visible", timeout=5000)


def test_added_entry_shows_toil_hours(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("+4.00h TOIL", exact=False).wait_for(state="visible", timeout=5000)


def test_metrics_update_after_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="4.00h").first.wait_for(state="visible", timeout=8000)


def test_reject_below_threshold_overtime(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "9")
    click_add_to_log(page)
    page.get_by_text("does not meet the 3h overtime threshold", exact=False).wait_for(state="visible", timeout=5000)


def test_reject_exact_standard_day_hours(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "8")
    click_add_to_log(page)
    page.get_by_text("does not meet the 3h overtime threshold", exact=False).wait_for(state="visible", timeout=5000)


def test_entry_not_added_when_rejected(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "9")
    click_add_to_log(page)
    page.get_by_text("No entries yet - log an overtime day above.", exact=True).wait_for(state="visible", timeout=5000)


# ──────────────────────────────────────────────────────────────
# Hours used
# ──────────────────────────────────────────────────────────────

def test_hours_used_update(page):
    switch_to_annual_tab(page)
    page.get_by_label("Total TOIL hours used this year").fill("4")
    page.get_by_text("Update hours used").click()
    page.wait_for_timeout(1500)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="4.00h").first.wait_for(state="visible", timeout=8000)


def test_hours_remaining_after_usage(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_label("Total TOIL hours used this year").fill("2")
    page.get_by_text("Update hours used").click()
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours remaining").filter(has_text="2.00h").first.wait_for(state="visible", timeout=8000)


# ──────────────────────────────────────────────────────────────
# Delete entry  (now requires inline confirmation before deleting)
# ──────────────────────────────────────────────────────────────

def test_delete_entry_shows_confirmation(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1000)
    page.get_by_text("Confirm delete").wait_for(state="visible", timeout=5000)
    page.get_by_text("Cancel").first.wait_for(state="visible", timeout=5000)


def test_delete_entry_cancel_preserves_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1000)
    page.get_by_text("Cancel").first.click()
    page.wait_for_timeout(1000)
    page.get_by_text("12.00h worked", exact=False).wait_for(state="visible", timeout=5000)


def test_delete_entry(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("12.00h worked", exact=False).wait_for(state="visible", timeout=5000)
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1000)
    confirm_delete(page)
    page.get_by_text("No entries yet - log an overtime day above.", exact=True).wait_for(state="visible", timeout=5000)


def test_delete_entry_updates_metrics(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.locator("button", has_text="\u2715").first.click()
    page.wait_for_timeout(1000)
    confirm_delete(page)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)


# ──────────────────────────────────────────────────────────────
# Clear all data
# ──────────────────────────────────────────────────────────────

def test_clear_all_shows_confirmation(page):
    switch_to_annual_tab(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Are you sure?", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("Yes, clear everything", exact=False).wait_for(state="visible", timeout=5000)
    page.get_by_text("Cancel", exact=True).first.wait_for(state="visible", timeout=5000)


def test_clear_all_cancel_preserves_data(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Cancel", exact=True).first.click()
    page.wait_for_timeout(1500)
    page.get_by_text("12.00h worked", exact=False).wait_for(state="visible", timeout=5000)


def test_clear_all_confirm_resets_data(page):
    switch_to_annual_tab(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("Clear all TOIL data").click()
    page.wait_for_timeout(1000)
    page.get_by_text("Yes, clear everything").click()
    page.wait_for_timeout(1500)
    page.get_by_text("No entries yet - log an overtime day above.", exact=True).wait_for(state="visible", timeout=5000)


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
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours banked").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)
    page.locator('[data-testid="stMetric"]').filter(has_text="Hours used").filter(has_text="0.00h").first.wait_for(state="visible", timeout=8000)


# ──────────────────────────────────────────────────────────────
# Working pattern switch
# ──────────────────────────────────────────────────────────────

def test_switch_to_4_day_updates_caption(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    page.get_by_text("10h work day with 3h+ overtime", exact=False).wait_for(state="visible", timeout=5000)


def test_4_day_pattern_rejects_12h_as_below_threshold(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    enter_hours_worked(page, "12")
    click_add_to_log(page)
    page.get_by_text("does not meet the 3h overtime threshold", exact=False).wait_for(state="visible", timeout=5000)


def test_4_day_pattern_accepts_14h(page):
    switch_to_annual_tab(page)
    click_4_day_radio(page)
    enter_hours_worked(page, "14")
    click_add_to_log(page)
    page.get_by_text("14.00h worked", exact=False).wait_for(state="visible", timeout=5000)