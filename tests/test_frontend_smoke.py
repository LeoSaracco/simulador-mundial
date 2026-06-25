import os

import pytest


pytestmark = pytest.mark.frontend

APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")


def test_frontend_main_simulation_flow(page):
    page.goto(APP_URL)
    page.wait_for_load_state("networkidle")

    button = page.locator("#btnSimular")
    assert button.is_visible()
    assert button.is_enabled()

    with page.expect_response(
        lambda response: "/simulator/run" in response.url
        and response.request.method == "POST",
        timeout=30000,
    ) as simulation_response:
        button.click()

    response = simulation_response.value
    assert response.ok

    page.wait_for_selector("#resultsSection", state="visible", timeout=30000)
    page.wait_for_function(
        "document.getElementById('championResult').innerText.trim().length > 0",
        timeout=30000,
    )
    page.wait_for_function(
        "document.getElementById('dashboardResult').innerText.trim().length > 10",
        timeout=30000,
    )
    page.wait_for_function(
        "document.getElementById('bracketResult').innerText.trim().length > 10",
        timeout=30000,
    )

    assert page.locator("#championResult").is_visible()
    assert page.locator("#dashboardResult").is_visible()
    assert page.locator("#bracketResult").is_visible()

    page.set_viewport_size({"width": 375, "height": 667})
    page.wait_for_timeout(500)

    scroll_width = page.evaluate("document.body.scrollWidth")
    viewport_width = page.evaluate("window.innerWidth")
    assert scroll_width <= viewport_width
