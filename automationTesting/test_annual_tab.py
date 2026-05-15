def switch_to_annual_tab(page):
    assert page.get_by_text("TOIL MONTHLY TRACKER").is_visible()
    page.get_by_text("TOIL ANNUAL LEAVE ACCRUEMENT").click()
    page.wait_for_timeout(1000)


def test_annual_tab_metrics_visible(page):
    switch_to_annual_tab(page)

    assert page.get_by_text("Hours banked").is_visible()
    assert page.get_by_text("Hours used", exact=True).first.is_visible()
    assert page.get_by_text("Hours remaining").is_visible()


def test_add_valid_overtime_entry(page):
    switch_to_annual_tab(page)

    input_hours = page.locator("input[aria-label='Hours worked'][max='24']")
    input_hours.click()
    input_hours.click(click_count=3)
    input_hours.press_sequentially("12")
    input_hours.press("Tab")
    page.wait_for_timeout(1500)

    # preview message appears before clicking — assert it here
    assert page.get_by_text("qualifies for annual TOIL pot", exact=False).is_visible()

    # click add and assert the entry appears in the log table
    page.get_by_text("Add to log").click()
    page.wait_for_timeout(1500)
    assert page.get_by_text("12.0h worked", exact=False).is_visible()


def test_reject_below_threshold_overtime(page):
    switch_to_annual_tab(page)

    input_hours = page.locator("input[aria-label='Hours worked'][max='24']")
    input_hours.click()
    input_hours.click(click_count=3)
    input_hours.press_sequentially("9")
    input_hours.press("Tab")
    page.wait_for_timeout(1500)

    # error message appears after clicking when below threshold
    page.get_by_text("Add to log").click()
    page.wait_for_timeout(1000)
    assert page.get_by_text("does not meet the 3h overtime threshold").is_visible()


def test_hours_used_update(page):
    switch_to_annual_tab(page)

    page.get_by_label("Total TOIL hours used this year").fill("4")
    page.get_by_text("Update hours used").click()

    assert page.get_by_text("Hours used", exact=True).first.is_visible()