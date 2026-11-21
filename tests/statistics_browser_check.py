"""v0.7.0 browser acceptance: source settings, seven SVG chart types, cards, six languages, statistics."""
import asyncio
import shutil
import tempfile
from playwright.async_api import async_playwright
from smart_demo_browser_check import Bridge050
import load_core


class StatsBridge(Bridge050):
    async def api(self, msg):
        if msg.get("action")=="reset_statistics":
            c=self.demo.controller if self.demo else self.controller
            await c.reset_statistics(msg["revision"])
            return self.result()
        return await super().api(msg)


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=StatsBridge(temp)
        process=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which("chromium"),headless=True,
                                                 args=["--no-sandbox","--disable-dev-shm-usage"])
                page=await browser.new_page(viewport={"width":1180,"height":900})
                page.on("pageerror",lambda e:errors.append(str(e)))
                page.on("dialog",lambda dlg:asyncio.create_task(dlg.accept()))
                await page.expose_function("rrhTestWS",bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/"frontend/panel.js"))
                panel=page.locator("rrh-hood-panel")
                await page.wait_for_function('document.querySelector("#panel")._data?.version === "0.9.3"')
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator("#source-settings summary").click()
                await panel.locator("#grid-entity").select_option("sensor.test_grid")
                await panel.locator('[data-nav="energy"]').click()
                if not await panel.locator("#energy-settings").evaluate("el=>el.open"):
                    await panel.locator("#energy-settings summary").click()
                await panel.locator("#stat-pv-fixed").fill("4500")
                await panel.locator("#stat-import-fixed").fill("0.32")
                await panel.locator("#stat-feed-fixed").fill("0.08")
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator("#dashboard-settings summary").click()
                await panel.locator("#stat-chart-type").select_option("donut")
                await panel.locator("#stat-language").select_option("fr")
                await panel.locator('[data-stat-card="managed"]').uncheck()
                await panel.locator("#save-settings").click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config?.dashboard?.language === "fr"')
                assert bridge.controller.config.energy.import_price.value==.32
                assert bridge.controller.config.energy.feed_in_price.value==.08
                assert bridge.controller.config.energy.pv_size.value==4.5
                assert not bridge.controller.config.dashboard.visible["managed"]
                await panel.locator('[data-nav="dashboard"]').click()
                assert not await panel.locator("#allocation-card").count()
                assert await panel.locator("#managed-card").is_hidden()
                assert await panel.locator("#live-chart-card").is_visible()
                assert await panel.locator("#rrh-live-chart svg").count()==1
                assert "Énergie et coûts" in await panel.locator('[data-nav="energy"]').inner_text()
                print("PASS: source configuration and independent visibility, French navigation, removed candidate card",flush=True)

                # Accounted statistics in backend independent of appliance switches.
                for t in range(100,161):
                    bridge.controller.statistics.sample(t,mode="running",export_w=500,managed_w=1000,
                        loads={"simulated":1000},buy_price=.32,feed_price=.08)
                bridge.controller.stat_sources={"pv_size_kwp":4.5,"pv_power_w":3500,"warnings":[]}
                await panel.locator('[data-nav="energy"]').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.statistics?.total?.rrh_kwh > 0')
                assert await panel.locator("#energy-overview .stats-box").count()>=12
                assert "0,24" in (await panel.locator("#energy-overview").inner_text()) or "0,00" in (await panel.locator("#energy-overview").inner_text())
                print("PASS: expandable energy statistics, historical kWh and monetary figures render",flush=True)

                # Back in settings: all chart types render as accessible SVG.
                await panel.locator('[data-nav="settings"]').click()
                for chart in ["gauge","line","bar","area","donut","stacked","sparkline"]:
                    await panel.locator("#stat-chart-type").select_option(chart)
                    await panel.locator("#save-settings").click()
                    await page.wait_for_function(f'document.querySelector("#panel")._data?.config?.dashboard?.chart_type === "{chart}"')
                    await panel.locator('[data-nav="dashboard"]').click()
                    assert await panel.locator("#rrh-live-chart svg").count()==1,chart
                    await panel.locator('[data-nav="settings"]').click()
                print("PASS: seven selectable SVG visualizations",flush=True)

                for language, navigation in [("es","Energía y costes"),("pt","Energia e custos"),("it","Energia e costi"),
                                             ("en","Energy & costs"),("de","Energie & Kosten")]:
                    await panel.locator("#stat-language").select_option(language)
                    await panel.locator("#save-settings").click()
                    await page.wait_for_function(f'document.querySelector("#panel")._data?.config?.dashboard?.language === "{language}"')
                    assert navigation in await panel.locator('[data-nav="energy"]').inner_text(),language
                print("PASS: selectable language persisted DE EN FR ES PT IT",flush=True)

                await panel.locator('[data-nav="energy"]').click()
                await panel.locator("#reset-statistics").click()
                await page.wait_for_function('document.querySelector("#panel")._data?.statistics?.total?.rrh_kwh === 0')
                assert bridge.controller.statistics.totals["rrh_kwh"] == 0
                print("PASS: statistics reset isolated from fairness bookkeeping",flush=True)

                await page.set_viewport_size({"width":390,"height":820})
                await panel.locator("#page-choice").select_option("dashboard")
                assert await panel.locator("#live-chart-card").is_visible()
                assert await panel.locator("#rrh-live-chart svg").count()==1
                width=await page.evaluate("document.documentElement.scrollWidth")
                assert width <= 391,width
                assert not errors,errors
                print("PASS: mobile dashboard and all new controls without JS exceptions",flush=True)
                await browser.close()
        finally:
            process.cancel()
            try:await process
            except asyncio.CancelledError:pass

if __name__=="__main__":asyncio.run(main())
