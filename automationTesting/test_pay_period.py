# payPeriodTest.py
def test_pay_period_display(page):
    page.get_by_text("Pay period").scroll_into_view_if_needed()

    assert page.get_by_text("Period start").is_visible()
    assert page.get_by_text("Period end").is_visible()
    assert page.get_by_text("Payday").is_visible()
    assert page.get_by_text("Weeks").is_visible()


def test_weeks_value_valid(page):
    weeks_text = page.locator("text=Weeks").locator("..").inner_text()
    valid_weeks = ["3", "4", "5"]

    assert any(w in weeks_text for w in valid_weeks)


def test_month_selector_changes_period(page):
    month_select = page.get_by_label("Select pay period month")
    month_select.select_option(index=1)

    assert page.get_by_text("Period start").is_visible()