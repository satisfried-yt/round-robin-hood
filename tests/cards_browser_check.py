"""Card-layout/interaction regressions using the shipped UI and real controller.

HA transport, entities and services come from the explicitly simulated Bridge.
No HA server is launched. Run: python tests/cards_browser_check.py
"""
from __future__ import annotations

import asyncio
from contextlib import suppress
import json
import os
from pathlib import Path
import shutil
import tempfile

from playwright.async_api import async_playwright
from browser_check import Bridge, capture
import load_core

ROOT = load_core.ROOT


async def main():
    results = []
    errors = []
    console_errors = []
    layout_results = []

    def record(name):
        results.append(name)
        print(f"PASS: {name}", flush=True)

    with tempfile.TemporaryDirectory() as tmp:
        bridge = Bridge(tmp)
        cfg = bridge.controller.config.to_dict()
        cfg["grid_entity"] = "sensor.test_grid"
        cfg["consumers"] = [
            {"id": key, "name": name, "entity_id": entity, "watts": watts,
             "enabled": True, "virtual_confirmed": True}
            for key, name, entity, watts in [
                ("a", "Testheizung", "switch.test_1", 1800),
                ("b", "Pooltechnik", "switch.test_2", 500),
                ("c", "Zusatzverbraucher", "switch.test_3", 800),
            ]
        ]
        await bridge.controller.configure(cfg, bridge.controller.revision)
        for entity in bridge.values:
            bridge.controller.seed_switch(entity, "off")
        reporting = asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                executable = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
                browser = await pw.chromium.launch(executable_path=executable, headless=True, args=["--no-sandbox"])
                page = await browser.new_page(viewport={"width":1360, "height":1000}, device_scale_factor=1)
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)
                await page.expose_function("rrhTestWS", bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT / "frontend/panel.js"))
                panel = page.locator("rrh-hood-panel")
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                # Legacy card interaction regression: show all existing panes in this fixture.
                # Actual single-page navigation is separately tested in navigation_browser_check.py.
                await panel.evaluate("el=>el.shadowRoot.querySelectorAll('.page').forEach(p=>p.hidden=false)")

                async def settled():
                    await page.wait_for_function("document.querySelector('#panel')._writing === false")

                assert await panel.locator(".overview-grid > article.card").count() == 10
                assert await panel.locator("#consumers > article.card.consumer").count() == 3
                assert await panel.locator(".settings-grid > details.card").count() == 6
                assert await panel.locator(".card .consumer").count() == 0
                assert await panel.locator("#page-settings .settings-card[open]").count() == 1
                assert await panel.locator(".consumer .consumer-icon").count() == 3
                assert await panel.locator(".consumer .ordinal").count() == 0
                assert await panel.locator(".consumer.is-next").count() == 1
                assert await panel.locator(".consumer.is-next").get_attribute("data-consumer") == "a"
                assert await panel.locator(".consumer.is-next .next-chip").inner_text() == "N\u00e4chster Kandidat"
                record("Independent semantic cards; MDI icons replace numbering; next candidate labelled in text")

                geometry = await panel.locator(".metric-card").evaluate_all("els=>els.slice(0,4).map(e=>({x:e.offsetLeft,y:e.offsetTop,w:e.offsetWidth}))")
                assert len({g["y"] for g in geometry}) == 1 and len({g["x"] for g in geometry}) == 4
                assert abs(geometry[0]["w"] - geometry[2]["w"]) <= 1
                record("Desktop metrics fill four equal columns")

                # Native <details> remains keyboard-operable; no custom widget library.
                summary = panel.locator("#control-settings summary")
                await summary.focus()
                await page.keyboard.press("Enter")
                assert await panel.locator("#control-settings").get_attribute("open") is not None
                await page.keyboard.press("Space")
                assert await panel.locator("#control-settings").get_attribute("open") is None
                await summary.click()
                await panel.locator("#reserve-input").fill("150")
                await panel.locator("#delay").fill("0")
                await panel.locator("#freshness-settings summary").click()
                await panel.locator("#max-age").fill("90")
                await panel.locator("#save-settings").click()
                await settled()
                assert bridge.controller.config.reserve_w == 150
                assert bridge.controller.config.shutdown_delay_s == 0
                assert bridge.controller.config.max_age_s == 90
                assert bridge.controller.mode == "paused" and bridge.commands == []
                assert "150 W" in await panel.locator("#control-summary").inner_text()
                assert "90 s" in await panel.locator("#freshness-summary").inner_text()
                record("Keyboard-operated settings cards save one configuration; no switching or auto-start")

                # Invalid input must reopen its collapsed card for native validation/focus.
                await panel.locator("#max-age").fill("0")
                await panel.locator("#freshness-settings summary").click()
                before_revision = bridge.controller.revision
                await panel.locator("#save-settings").click()
                assert await panel.locator("#freshness-settings").get_attribute("open") is not None
                assert await panel.locator("#max-age").evaluate("el=>el.getRootNode().activeElement===el")
                assert bridge.controller.revision == before_revision
                await panel.locator("#reset-settings").click()
                assert await panel.locator("#max-age").input_value() == "90"
                record("Collapsed invalid input reopens and receives focus; no invalid configuration saved")

                await panel.locator("#reserve-input").fill("175")
                await panel.locator("#reserve-input").focus()
                await asyncio.sleep(1.8)  # At least one normal production poll.
                assert await panel.locator("#reserve-input").input_value() == "175"
                assert await panel.locator("#reserve-input").evaluate("el=>el.getRootNode().activeElement===el")
                assert await panel.locator("#control-settings").get_attribute("open") is not None
                assert bridge.controller.config.reserve_w == 150
                await panel.locator("#reset-settings").click()
                record("Live polling preserves unsaved fields, open cards and keyboard focus")

                # Reorder by keyboard, preserving the operated consumer and its action.
                up = panel.locator('[data-consumer="c"] [data-control="up"]')
                await up.focus()
                await page.keyboard.press("Enter")
                await page.wait_for_function("document.querySelector('#panel')._data.config.consumers[1].id === 'c' && !document.querySelector('#panel')._writing")
                assert await panel.locator(".consumer").evaluate_all("els=>els.map(e=>e.dataset.consumer)") == ["a","c","b"]
                assert await up.evaluate("el=>el.getRootNode().activeElement===el")
                assert await panel.locator(".consumer .consumer-icon").count() == 3
                assert await panel.locator(".consumer .ordinal").count() == 0
                await panel.locator('[data-consumer="c"] [data-control="down"]').click()
                await settled()
                assert [c.id for c in bridge.controller.config.consumers] == ["a","b","c"]
                assert bridge.commands == []
                record("Keyboard reordering renumbers cards, preserves focus and sends no switch commands")

                # Long names/IDs are valid backend data; ensure they cannot break card geometry.
                long_name = "Verbraucher_" + "X" * 68
                long_entity = "switch." + "l" * 200
                long_config = bridge.controller.config.to_dict()
                long_config["consumers"].append({"id":"long", "name":long_name, "entity_id":long_entity,
                    "watts":12345, "enabled":False, "virtual_confirmed":True})
                await bridge.controller.configure(long_config, bridge.controller.revision)
                bridge.controller.seed_switch(long_entity, "unavailable")
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 4")
                for width in [320, 390, 768, 1024, 1360, 1920]:
                    await page.set_viewport_size({"width":width,"height":900})
                    info = await panel.evaluate("""el=>{
                        const root=el.shadowRoot;
                        const cards=[...root.querySelectorAll('.consumer')];
                        const y=cards[0].getBoundingClientRect().top;
                        const overflowing=[...root.querySelectorAll('main,.card')].filter(e=>
                            e.getClientRects().length && e.tagName!=='DIALOG' && e.scrollWidth>e.clientWidth+1);
                        return {width:innerWidth, columns:cards.filter(c=>Math.abs(c.getBoundingClientRect().top-y)<1).length,
                          overflow:overflowing.map(e=>e.id||e.className),
                          order:cards.map(c=>c.dataset.consumer)};
                    }""")
                    if info["overflow"]:
                        issue=await panel.evaluate("""el=>[...el.shadowRoot.querySelectorAll('main,.card')].filter(x=>x.getClientRects().length && x.scrollWidth>x.clientWidth+1 && x.tagName!=='DIALOG').map(x=>({tag:x.tagName,id:x.id,cls:x.className,width:x.clientWidth,scroll:x.scrollWidth,html:x.outerHTML.slice(0,350),parents:[x.parentElement?.id,x.parentElement?.parentElement?.id,x.parentElement?.parentElement?.parentElement?.id],hiddenPage:[x.closest('.page')?.id,x.closest('.page')?.hidden]}))""")
                        print('DIAG_OVERFLOW',issue,flush=True)
                    assert not info["overflow"], info
                    assert info["order"] == ["a","b","c","long"]
                    if width <= 390: assert info["columns"] == 1, info
                    if width == 768: assert info["columns"] == 2, info
                    if width >= 1360: assert info["columns"] == 3, info
                    if width == 1024: assert info["columns"] == 3, info
                    layout_results.append(info)
                record("320/390/768/1024/1360/1920 px: 1/2/3 columns, long content wraps, order preserved")

                await page.set_viewport_size({"width":1360,"height":1000})
                await panel.evaluate("el=>{el.style.width='720px';el.style.marginLeft='256px';}")
                assert await panel.locator("main").evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                columns = await panel.locator(".consumer").evaluate_all("els=>els.filter(e=>Math.abs(e.offsetTop-els[0].offsetTop)<1).length")
                assert columns == 2, columns
                await panel.evaluate("el=>{el.style.width='';el.style.marginLeft='';}")
                record("Grid responds to panel width with a simulated sidebar, not only the viewport")

                await page.set_viewport_size({"width":320,"height":844})
                sizes = await panel.locator("button,summary").evaluate_all("els=>els.filter(e=>e.getClientRects().length).map(e=>({label:e.id||e.textContent,info:e.classList.contains('info-button'),w:e.getBoundingClientRect().width,h:e.getBoundingClientRect().height}))")
                assert all((s["w"] >= (23.9 if s["info"] else 43.9)) and (s["h"] >= (23.9 if s["info"] else 43.9)) for s in sizes), sizes
                await panel.locator("#add").click()
                assert await panel.locator("#editor").evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                assert await panel.locator("#consumer-name").evaluate("el=>el.getRootNode().activeElement===el")
                await page.keyboard.press("Escape")
                assert await panel.locator("#editor").is_hidden()
                assert await panel.locator("#add").evaluate("el=>el.getRootNode().activeElement===el")
                record("320 px primary targets 44 px; compact info targets at least 24 px; modal and Escape work")

                # Restore the ordinary three-consumer fixture for the shipped screenshots.
                normal = bridge.controller.config.to_dict()
                normal["consumers"] = [c for c in normal["consumers"] if c["id"] != "long"]
                normal.update(reserve_w=100,shutdown_delay_s=30,max_age_s=60)
                await bridge.controller.configure(normal, bridge.controller.revision)
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                await panel.locator("#reset-settings").click()
                await page.set_viewport_size({"width":768,"height":1024})
                await capture(page, panel, "ui-tablet-settings.png")
                record("Tablet settings view captured from the running UI, with controls expanded")

                for card_id in ["source-settings","control-settings","freshness-settings"]:
                    if await panel.locator(f"#{card_id}").get_attribute("open") is not None:
                        await panel.locator(f"#{card_id} summary").click()
                await panel.locator("#activate").click()
                await asyncio.sleep(.3)
                assert bridge.commands == [], bridge.commands
                bridge.base = 2500
                for _ in range(80):
                    if len(bridge.commands) == 2: break
                    await asyncio.sleep(.1)
                assert bridge.commands == [("switch.test_1","on"),("switch.test_2","on")]
                await page.wait_for_function("document.querySelector('#panel')._data?.next_id === 'c'")
                assert await panel.locator(".consumer.is-next").get_attribute("data-consumer") == "c"
                assert await panel.locator(".consumer-state").all_text_contents() == ["Ein \u00b7 RRH-gesteuert", "Ein \u00b7 RRH-gesteuert", "Aus"]
                assert await panel.locator("#add").is_disabled()
                assert await panel.locator("#save-settings").is_disabled()
                assert await panel.locator("#pause").is_enabled()
                record("Confirmed allocations move the candidate badge; live locks and pause remain functional")

                await page.set_viewport_size({"width":390,"height":844})
                await capture(page, panel, "ui-mobile.png")
                await page.set_viewport_size({"width":1360,"height":1000})
                await capture(page, panel, "ui-desktop.png")
                record("Complete mobile and desktop card views captured from the real running component")

                await panel.locator("#pause").click()
                await settled()
                assert "Zum Bearbeiten zuerst pausieren" not in await panel.locator("#settings-hint").inner_text()
                assert await panel.locator("#save-settings").is_enabled()
                record("Pausing unlocks settings and clears the stale running-only editing hint")
                await panel.locator("#source-settings summary").click()
                await panel.evaluate("""el=>{
                    const vars={'--primary-background-color':'#111820','--secondary-background-color':'#24313d',
                      '--card-background-color':'#1b2630','--primary-text-color':'#eef3f7',
                      '--secondary-text-color':'#b4c1cd','--divider-color':'#3a4c5a',
                      '--primary-color':'#72cfc0','--text-primary-color':'#102b26','--error-color':'#ff9999'};
                    for(const [key,value] of Object.entries(vars)) el.style.setProperty(key,value);
                }""")
                bg = await panel.locator("#grid-entity").evaluate("el=>getComputedStyle(el).backgroundColor")
                assert bg == "rgb(27, 38, 48)", bg
                assert await panel.locator("#grid-card").evaluate("el=>getComputedStyle(el).color") == "rgb(238, 243, 247)"
                await capture(page, panel, "ui-dark.png")
                record("Theme variables style cards and form controls; dark-theme screenshot captured")

                await panel.locator("#source-settings summary").click()
                await panel.locator("#grid-card").evaluate("el=>el.scrollIntoView()")
                viewport = page.viewport_size.copy()
                await page.set_viewport_size({"width":390,"height":844})
                await panel.locator("#add").click()
                await page.screenshot(path=str(ROOT/"test-results/ui-mobile-editor.png"), full_page=True)
                await page.keyboard.press("Escape")
                record("Mobile dark-theme consumer editor captured with the real selection controls")

                assert errors == [], errors
                assert console_errors == [], console_errors
                record("No uncaught JavaScript errors or browser console errors in card scenarios")
                (ROOT/"test-results/card-layout.json").write_text(json.dumps(layout_results,indent=2)+"\n")
                (ROOT/"test-results/browser-version.txt").write_text(browser.version+"\n")
                await browser.close()
        finally:
            reporting.cancel()
            with suppress(asyncio.CancelledError): await reporting
            await bridge.controller.close()
    print(f"\n{len(results)} card browser scenarios passed. Real component/controller; HA boundary simulated.")


if __name__ == "__main__":
    asyncio.run(main())
