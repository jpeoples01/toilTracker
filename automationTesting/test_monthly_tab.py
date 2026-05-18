# test_monthly_tab.py


def fill_week_hours(page, week_index, hours_str):
    # scope to max=168 to avoid matching the tab 2 "Hours worked" input (max=24)
    inputs = page.locator("input[aria-label='Hours worked'][max='168']")
    inputs.nth(week_index).click()
    inputs.nth(week_index).click(click_count=3)
    inputs.nth(week_index).press_sequentially(hours_str)
    inputs.nth(week_index).press("Tab")
    page.wait_for_timeout(500)


def fill_holiday_days(page, week_index, days_str):
    inputs = page.get_by_label("Holiday days")
    inputs.nth(week_index).click()
    inputs.nth(week_index).click(click_count=3)
    inputs.nth(week_index).press_sequentially(days_str)
    inputs.nth(week_index).press("Tab")
    page.wait_for_timeout(500)


def click_calculate(page):
    page.get_by_text("Calculate").click()
    page.wait_for_timeout(1500)


def get_num_weeks(page):
    return page.locator("input[aria-label='Hours worked'][max='168']").count()


def click_4_day_radio(page):
    # Streamlit hides the <input> — click the visible label text instead
    page.get_by_text("4 days / 40 hours", exact=True).first.click()
    page.wait_for_timeout(1500)


# ──────────────────────────────────────────────────────────────
# Tab visibility and initial state
# ──────────────────────────────────────────────────────────────

def test_monthly_tab_visible(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()


def test_monthly_tab_is_default(page):
    assert page.get_by_role("tab", name="TOIL Monthly Tracker").get_attribute("aria-selected") == "true"


def test_monthly_default_working_pattern(page):
    radio = page.get_by_label("5 days / 40 hours").first
    assert radio.is_checked()


def test_monthly_unselected_working_pattern(page):
    radio = page.get_by_label("4 days / 40 hours").first
    assert not radio.is_checked()


def test_pay_period_subheader_visible(page):
    assert page.get_by_text("Pay period", exact=True).first.is_visible()


def test_calculate_button_visible(page):
    assert page.get_by_text("Calculate", exact=True).is_visible()


def test_month_selector_visible(page):
    assert page.get_by_label("Select pay period month").is_visible()


def test_week_labels_visible(page):
    assert page.get_by_text("Week 1", exact=False).is_visible()


def test_hours_worked_inputs_present(page):
    num_weeks = get_num_weeks(page)
    assert 3 <= num_weeks <= 5


def test_holiday_days_inputs_present(page):
    inputs = page.get_by_label("Holiday days")
    num_weeks = inputs.count()
    assert 3 <= num_weeks <= 5


def test_hours_and_holiday_inputs_count_match(page):
    hours_count = get_num_weeks(page)
    holiday_count = page.get_by_label("Holiday days").count()
    assert hours_count == holiday_count


# ──────────────────────────────────────────────────────────────
# Basic calculation
# ──────────────────────────────────────────────────────────────

def test_enter_hours_and_calculate(page):
    page.locator("input[aria-label='Hours worked'][max='168']").first.fill("40")
    click_calculate(page)
    assert page.get_by_text("Total hours this month", exact=False).is_visible()


def test_exact_hours_shows_success(page):
    num_weeks = get_num_weeks(page)
    for i in range(num_weeks):
        fill_week_hours(page, i, "40")
    click_calculate(page)
    assert page.get_by_text("You have worked exactly your full hours this month", exact=False).is_visible()


def test_under_hours_shows_deficit(page):
    fill_week_hours(page, 0, "30")
    click_calculate(page)
    assert page.get_by_text("left to work to get full pay", exact=False).is_visible()


def test_monthly_overtime_message(page):
    num_weeks = get_num_weeks(page)
    for i in range(num_weeks):
        fill_week_hours(page, i, "50")
    click_calculate(page)
    assert page.get_by_text("overtime this month", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Specific calculation values
# ──────────────────────────────────────────────────────────────

def test_single_week_40h_shows_deficit(page):
    num_weeks = get_num_weeks(page)
    fill_week_hours(page, 0, "40")
    click_calculate(page)
    if num_weeks > 1:
        assert page.get_by_text("left to work to get full pay", exact=False).is_visible()
    else:
        assert page.get_by_text("You have worked exactly your full hours", exact=False).is_visible()


def test_zero_hours_shows_full_deficit(page):
    click_calculate(page)
    assert page.get_by_text("left to work to get full pay", exact=False).is_visible()


def test_total_hours_displayed_correctly(page):
    fill_week_hours(page, 0, "35")
    click_calculate(page)
    assert page.get_by_text("35 hours and 0 minutes", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Decimal hours
# ──────────────────────────────────────────────────────────────

def test_decimal_hours_calculated_correctly(page):
    fill_week_hours(page, 0, "37.30")
    click_calculate(page)
    assert page.get_by_text("37 hours and 30 minutes", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Holiday days
# ──────────────────────────────────────────────────────────────

def test_holiday_days_info_message(page):
    fill_holiday_days(page, 0, "1")
    click_calculate(page)
    assert page.get_by_text("Holiday hours added", exact=False).is_visible()


def test_holiday_days_add_to_total(page):
    fill_week_hours(page, 0, "32")
    fill_holiday_days(page, 0, "1")
    click_calculate(page)
    assert page.get_by_text("40 hours and 0 minutes", exact=False).is_visible()


def test_holiday_info_shows_correct_calculation(page):
    fill_holiday_days(page, 0, "2")
    click_calculate(page)
    assert page.get_by_text("2 day(s)", exact=False).is_visible()


def test_no_holidays_no_info_message(page):
    fill_week_hours(page, 0, "40")
    click_calculate(page)
    assert not page.get_by_text("Holiday hours added", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Working pattern switch
# ──────────────────────────────────────────────────────────────

def test_switch_to_4_day_pattern(page):
    click_4_day_radio(page)
    radio = page.get_by_label("4 days / 40 hours").first
    assert radio.is_checked()


def test_4_day_pattern_holiday_uses_10h(page):
    click_4_day_radio(page)
    fill_holiday_days(page, 0, "1")
    click_calculate(page)
    assert page.get_by_text("Holiday hours added: 1 day(s) × 10h", exact=False).is_visible()


# ──────────────────────────────────────────────────────────────
# Multiple weeks
# ──────────────────────────────────────────────────────────────

def test_multiple_weeks_total_correct(page):
    fill_week_hours(page, 0, "40")
    fill_week_hours(page, 1, "40")
    click_calculate(page)
    assert page.get_by_text("80 hours and 0 minutes", exact=False).is_visible()


def test_mixed_hours_across_weeks(page):
    fill_week_hours(page, 0, "35")
    fill_week_hours(page, 1, "45")
    click_calculate(page)
    assert page.get_by_text("80 hours and 0 minutes", exact=False).is_visible()