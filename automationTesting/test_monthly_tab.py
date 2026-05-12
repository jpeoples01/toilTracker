# monthlyTabTest.py
def test_monthly_tab_visible(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()


def test_monthly_default_working_pattern(page):
    radio = page.get_by_label("5 days / 40 hours").first
    assert radio.is_checked()

def test_monthly_unselected_working_pattern(page):
    radio = page.get_by_label("4 days / 40 hours").first
    assert not radio.is_checked()


def test_enter_hours_and_calculate(page):
    # Week 1 hours
    page.get_by_label("Hours worked").first.fill("40")
    page.get_by_text("Calculate").click()
    page.wait_for_timeout(1000)

    assert page.get_by_text("Total hours this month", exact=False).is_visible()


def test_monthly_overtime_message(page):
    inputs = page.get_by_label("Hours worked")
    for i in range(min(4, inputs.count())):
        inputs.nth(i).fill("50")

    page.get_by_text("Calculate").click()
    page.wait_for_timeout(1000)

    assert page.get_by_text("You have worked", exact=False).is_visible()