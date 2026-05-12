# annualTabTest.py
def switch_to_annual_tab(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()
    page.get_by_text("TOIL ANNUAL LEAVE ACCRUEMENT").click()
    page.wait_for_timeout(1000)


def test_annual_tab_metrics_visible(page):
    switch_to_annual_tab(page)

    assert page.get_by_text("Hours banked").is_visible()
    assert page.get_by_text("Hours used").is_visible()
    assert page.get_by_text("Hours remaining").is_visible()


def test_add_valid_overtime_entry(page):
    switch_to_annual_tab(page)

    page.get_by_label("Hours worked").fill("12")
    page.get_by_text("Add to log").click()

    assert page.get_by_text("TOIL", exact=False).is_visible()


def test_reject_below_threshold_overtime(page):
    switch_to_annual_tab(page)

    page.get_by_label("Hours worked").fill("9")
    page.get_by_text("Add to log").click()

    assert page.get_by_text("does not meet the 3h overtime threshold").is_visible()


def test_hours_used_update(page):
    switch_to_annual_tab(page)

    page.get_by_label("Total TOIL hours used this year").fill("4")
    page.get_by_text("Update hours used").click()

    assert page.get_by_text("Hours used").is_visible()