# demo_playwright.py
# Script de demo para el Live Coding de la Clase 5
# Solo el docente lo instala y ejecuta; los alumnos lo observan.
#
# Setup previo:
#   pip install playwright
#   playwright install chromium
#   python -m uvicorn main:app --reload --port 8000  (en otra terminal)
#
# Ejecutar:
#   python demo_playwright.py

import asyncio

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright


APP_URL = "http://localhost:8000"


def console_safe(text: str) -> str:
    return text.encode("ascii", errors="ignore").decode("ascii")


async def test_simulacion_completa():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        page = await browser.new_page()

        print("\nIniciando demo de testing E2E con Playwright\n")

        await page.goto(APP_URL)
        await page.wait_for_load_state("networkidle")
        print(f"OK App cargada en {APP_URL}")

        btn = page.locator("#btnSimular")
        assert await btn.is_enabled(), "El boton deberia estar habilitado al inicio"
        print("OK Boton #btnSimular esta habilitado")

        async with page.expect_response(
            lambda response: "/simulator/run" in response.url
            and response.request.method == "POST",
            timeout=30000,
        ) as simulation_response:
            await btn.click()
            print("Click en 'Simular Mundial'...")

            try:
                await page.wait_for_function(
                    "document.getElementById('btnSimular').disabled === true",
                    timeout=1000,
                )
                print("OK Boton deshabilitado durante la simulacion")
            except PlaywrightTimeoutError:
                print("INFO La simulacion fue rapida; no se capturo el estado disabled")

        response = await simulation_response.value
        assert response.ok, f"POST /simulator/run fallo con status {response.status}"
        print("OK POST /simulator/run respondio correctamente")

        await page.wait_for_function(
            "document.getElementById('btnSimular').disabled === false",
            timeout=30000,
        )
        await page.wait_for_selector("#resultsSection", state="visible", timeout=30000)
        await page.wait_for_function(
            "document.getElementById('championResult').innerText.trim().length > 0",
            timeout=30000,
        )
        await page.wait_for_function(
            "document.getElementById('dashboardResult').innerText.trim().length > 10",
            timeout=30000,
        )
        print("OK Simulacion completada y resultados renderizados")

        results = page.locator("#resultsSection")
        assert await results.is_visible(), "resultsSection deberia estar visible"
        print("OK Seccion de resultados visible (#resultsSection)")

        champion = page.locator("#championResult")
        assert await champion.is_visible(), "championResult deberia estar visible"
        champion_text = await champion.inner_text()
        print(f"OK Campeon mostrado: {console_safe(champion_text.strip())[:60]}")

        dashboard = page.locator("#dashboardResult")
        assert await dashboard.is_visible(), "dashboardResult deberia estar visible"
        dashboard_text = await dashboard.inner_text()
        assert len(dashboard_text) > 10, "El dashboard deberia tener contenido"
        print("OK Dashboard ejecutivo con datos (#dashboardResult)")

        await page.set_viewport_size({"width": 375, "height": 667})
        await page.wait_for_timeout(500)

        scroll_width = await page.evaluate("document.body.scrollWidth")
        viewport_width = await page.evaluate("window.innerWidth")
        if scroll_width > viewport_width:
            print(
                f"WARN Scroll horizontal detectado en mobile: "
                f"body={scroll_width}px > viewport={viewport_width}px"
            )
        else:
            print(
                f"OK Sin scroll horizontal en mobile "
                f"(body={scroll_width}px, viewport={viewport_width}px)"
            )

        await browser.close()
        print("\nDemo completada\n")


asyncio.run(test_simulacion_completa())
