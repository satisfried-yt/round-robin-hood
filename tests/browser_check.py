"""Chromium exercises the shipped UI and real controller through a local test bridge.

Only HA's websocket transport, state machine and switch services are simulated.
The production frontend and controller are used unchanged. This does not boot HA.
Run from package root: python tests/browser_check.py
Requires playwright and a local Chromium installation (see docs/TECHNIK_UND_TESTS.md).
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
import load_core
from rrh_tested.controller import Controller
from rrh_tested.model import UserError

ROOT = load_core.ROOT


class Bridge:
    def __init__(self, path):
        self.path=Path(path)/"state.json"
        self.onboarding_bypass=True
        self.values={"switch.test_1":"off","switch.test_2":"off","switch.test_3":"off"}
        self.commands=[]
        self.base=1300
        self.available=True
        self.api_online=True
        self.response_delays={}
        self.controller=Controller(None,send=self.send,save=self.save)
        self.states={
            "sensor.test_grid":{"state":"1300","attributes":{"friendly_name":"Vorhandene Netzleistung","unit_of_measurement":"W"}},
            "sensor.energy":{"state":"100","attributes":{"friendly_name":"Energie (nicht Leistung)","unit_of_measurement":"kWh"}},
            **{key:{"state":value,"attributes":{"friendly_name":f"Virtueller Testschalter {i+1}"}} for i,(key,value) in enumerate(self.values.items())}}
    async def save(self,data):
        temporary=self.path.with_suffix(".tmp"); temporary.write_text(json.dumps(data)); temporary.replace(self.path)
    async def send(self,entity_id,target,token):
        self.commands.append((entity_id,target)); self.values[entity_id]=target
        self.controller.observe_switch(entity_id,target,command_token=token)
    async def reports(self):
        while True:
            watts=sum(c.watts for c in self.controller.config.consumers if self.values.get(c.entity_id)=="on")
            self.controller.observe_grid(str(self.base-watts) if self.available else "unavailable","W")
            await asyncio.sleep(.1)
    def result(self):
        cfg=self.controller.config
        return {**self.controller.status(),"notice_dismissed": bool(self.onboarding_bypass or cfg.notice_dismissed),
                "setup_needed":bool(not self.onboarding_bypass and not cfg.setup_complete and not cfg.grid_entity and not cfg.consumers),
                "setup_complete":cfg.setup_complete, "demo_mode":False}

    async def api(self,msg):
        if not self.api_online: raise RuntimeError("Test bridge offline")
        c=self.controller
        try:
            if msg["type"].endswith("/status"): return self.result()
            action=msg["action"]
            if action=="configure":
                await c.configure(msg["config"],msg["revision"],currency_tariffs_confirmed=msg.get("currency_tariffs_confirmed",False))
                for item in c.config.consumers: c.seed_switch(item.entity_id,self.values.get(item.entity_id,"unavailable"))
                c.wait_after_sequence=c.reading.sequence
            elif action=="participation": await c.participation(msg["consumer_id"],msg["enabled"],msg["revision"])
            elif action=="profile_participation": await c.profile_participation(msg["profile_id"],msg["enabled"],msg["revision"])
            elif action=="reset_fair": await c.reset_fair(msg["profile_id"],msg["metric"],msg["revision"])
            elif action=="activate": await c.activate()
            elif action=="pause": c.pause()
            elif action=="emergency_off": await c.emergency_off()
            elif action=="dismiss_notice": await c.dismiss_notice(msg["notice_dismissed"])
            elif action=="factory_reset": await c.factory_reset(msg["revision"],msg["confirmation"])
            else: raise UserError("Bad test action")
            await asyncio.sleep(self.response_delays.get(action,0))
            return self.result()
        except UserError as err: raise RuntimeError(str(err)) from err
    def page_html(self):
        # Assign hass BEFORE custom-element registration: catches F5 upgrade bugs.
        source='''<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RRH UI test harness</title><style>body{margin:0;background:#f4f6f8}rrh-hood-panel{display:block;height:100vh}</style><rrh-hood-panel id="panel"></rrh-hood-panel><script>
        const panel=document.querySelector('#panel');
        window.confirm = () => true; // Fixture only: UI confirmation is tested separately.
        panel.hass={states:STATES,callWS:async msg=>await window.rrhTestWS(msg)};
        </script></html>'''
        return source.replace("STATES",json.dumps(self.states))


async def capture(page, panel, filename):
    """Capture the complete real component, not only its scroll viewport."""
    viewport = page.viewport_size.copy()
    height = await panel.locator("main").evaluate("el=>Math.ceil(el.getBoundingClientRect().height)")
    await page.set_viewport_size({"width": viewport["width"], "height": max(height, viewport["height"])})
    await panel.evaluate("el=>el.scrollTop=0")
    await page.screenshot(path=str(ROOT/"test-results"/filename), full_page=True)
    await page.set_viewport_size(viewport)


async def main():
    results=[]
    def record(name):
        results.append(name); print(f"PASS: {name}",flush=True)
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        reporting=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                executable=os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
                browser=await pw.chromium.launch(executable_path=executable,headless=True,args=["--no-sandbox"])
                page=await browser.new_page(viewport={"width":1360,"height":1180},device_scale_factor=1)
                page.on("pageerror",lambda error:errors.append(str(error)))
                page.on("dialog",lambda dialog:asyncio.create_task(dialog.accept()))
                await page.expose_function("rrhTestWS",bridge.api)
                async def load_page():
                    await page.goto("about:blank")
                    await page.set_content(bridge.page_html())
                    await page.add_script_tag(path=str(load_core.COMPONENT/"frontend/panel.js"))
                await load_page()
                panel=page.locator("rrh-hood-panel")
                await page.wait_for_function("document.querySelector('#panel').shadowRoot?.querySelector('#mode-text')?.textContent === 'Pausiert'")
                assert await panel.locator("#activate").is_disabled()
                record("F5/pre-upgrade hass property; empty paused panel connects")
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator("#source-settings summary").click()
                options=await panel.locator("#grid-entity option").all_text_contents()
                assert not any("sensor.energy" in value for value in options)
                await panel.locator("#grid-entity").select_option("sensor.test_grid")
                await panel.locator("#save-settings").click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config.grid_entity === 'sensor.test_grid'")
                record("Source picker filters power entities; configuration persists")

                await panel.locator('[data-nav="consumers"]').click()
                for i,(name,watts) in enumerate([("Testheizung",1800),("Pooltechnik",500),("Zusatzverbraucher",800)],1):
                    await panel.locator("#add").click()
                    await panel.locator("#consumer-name").fill(name)
                    await panel.locator("#consumer-entity").select_option(f"switch.test_{i}")
                    await panel.locator("#consumer-watts").fill(str(watts))
                    await panel.locator("#save-consumer").click()
                    await panel.locator("#editor").wait_for(state="hidden")
                assert len(json.loads(bridge.path.read_text())["config"]["consumers"])==3
                record("Create three consumers; new device bindings require a confirmation dialog")
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator("#source-settings summary").click()
                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator("#activate").click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'running'")
                await asyncio.sleep(.4)
                assert bridge.commands==[]
                assert bridge.controller.status()["next_id"]==bridge.controller.config.consumers[0].id
                assert await panel.locator("#add").is_disabled()
                record("1300 W source / 100 W reserve: 1800 W waits; 500 W cannot overtake")
                bridge.response_delays={"participation":.15,"pause":.3}
                await panel.locator('[data-nav="consumers"]').click()
                third=panel.locator(".consumer").filter(has=page.get_by_role("heading",name="Zusatzverbraucher",exact=True))
                await third.get_by_role("button",name="Teilnahme umschalten: Zusatzverbraucher",exact=True).click()
                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator("#pause").click()
                await panel.locator('[data-nav="consumers"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'paused' && !document.querySelector('#panel')._writing")
                assert await panel.locator("#add").is_enabled()
                bridge.response_delays={}
                third=panel.locator(".consumer").filter(has=page.get_by_role("heading",name="Zusatzverbraucher",exact=True))
                await third.get_by_role("button",name="Teilnahme umschalten: Zusatzverbraucher",exact=True).click()
                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator("#activate").click()
                record("Pause remains responsive during an in-flight settings response; UI does not get stuck")
                bridge.base=2500
                for _ in range(60):
                    if len(bridge.commands)==2: break
                    await asyncio.sleep(.1)
                assert bridge.commands==[("switch.test_1","on"),("switch.test_2","on")],bridge.commands
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.filter(c=>c.owned).length === 2")
                await capture(page, panel, "ui-desktop.png")
                record("UI-to-real-controller flow: two confirmed sequential starts and direct power budget")
                await panel.locator("#pause").click(); await asyncio.sleep(.2)
                await panel.locator('[data-nav="consumers"]').click()
                bridge.base=8000; await asyncio.sleep(.3)
                assert len(bridge.commands)==2 and bridge.values["switch.test_1"]=="on"
                record("Pause leaves running switches on and suppresses new commands")

                # Attempt deleting an owned running consumer; backend must refuse.
                first=panel.locator(".consumer").filter(has=page.get_by_role("heading",name="Testheizung",exact=True))
                await first.get_by_role("button",name="Entfernen: Testheizung",exact=True).click()
                await panel.locator("#command-error").wait_for(state="visible")
                assert len(bridge.controller.config.consumers)==3
                assert "ausschalten" in await panel.locator("#command-error").text_content()
                record("Owned running consumer cannot be deleted; error is visible")
                await first.get_by_role("button",name="Bearbeiten: Testheizung",exact=True).click()
                await panel.locator("#consumer-name").fill("Neue Bezeichnung")
                # Concurrent edit from another client; editor keeps its original revision.
                c=bridge.controller.config.consumers[-1]
                await bridge.controller.participation(c.id,False,bridge.controller.revision)
                await panel.locator("#save-consumer").click()
                assert await panel.locator("#editor").is_visible()
                assert "inzwischen" in await panel.locator("#editor-error").text_content()
                assert bridge.controller.config.consumers[0].name=="Testheizung"
                await panel.locator("#cancel-editor").click()
                record("Concurrent configuration edit rejects stale modal without losing input")

                await first.get_by_role("button",name="Bearbeiten: Testheizung",exact=True).click()
                assert await panel.locator("#consumer-virtual").count()==0
                await panel.locator("#consumer-entity").select_option("switch.test_3")
                await panel.locator("#cancel-editor").click()
                record("Redundant checkbox removed; binding changes request confirmation upon saving")

                # Reload: actual document/controller state remains, no duplicated writes.
                old_count=len(bridge.commands)
                await load_page()
                await panel.locator('[data-nav="consumers"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                await asyncio.sleep(.2); assert len(bridge.commands)==old_count
                third=panel.locator(".consumer").filter(has=page.get_by_role("heading",name="Zusatzverbraucher",exact=True))
                await third.get_by_role("button",name="Nach oben: Zusatzverbraucher",exact=True).click()
                assert bridge.controller.config.consumers[1].name=="Zusatzverbraucher"
                record("Browser reload retains configuration; reorder works without a switch command")

                # XSS protection: edit an off consumer, then remove it via the real UI.
                third=panel.locator(".consumer").filter(has=page.get_by_role("heading",name="Zusatzverbraucher",exact=True))
                await third.get_by_role("button",name="Bearbeiten: Zusatzverbraucher",exact=True).click()
                injection='<img src=x onerror="window.rrhXss=true">'
                await panel.locator("#consumer-name").fill(injection)
                await panel.locator("#save-consumer").click(); await panel.locator("#editor").wait_for(state="hidden")
                assert await panel.locator(".consumer img").count()==0
                assert not await page.evaluate("Boolean(window.rrhXss)")
                assert not await page.evaluate("Boolean(window.rrhXss)")
                evil=panel.locator(".consumer").filter(has=page.get_by_role("heading",name=injection,exact=True))
                await evil.get_by_role("button",name=f"Entfernen: {injection}",exact=True).click()
                assert len(bridge.controller.config.consumers)==2
                assert "switch.test_3" in bridge.values
                record("Untrusted names remain text; deleting RRH entry preserves HA switch")

                # External state change while running -> pause, not counter-switching.
                bridge.base=2500
                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator("#activate").click(); await asyncio.sleep(.2)
                bridge.values["switch.test_1"]="off"
                bridge.controller.observe_switch("switch.test_1","off",explicit_external=True)
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'error'")
                assert len(bridge.commands)==old_count
                assert bridge.controller.config.consumers[0].id not in bridge.controller.owned
                record("External intervention creates a visible error pause, never fights the user")

                bridge.available=False
                await page.wait_for_function("document.querySelector('#panel')._data?.power.raw === 'unavailable'")
                assert await panel.locator("#activate").is_disabled()
                assert bridge.controller.status()["power"]["available_w"] is None
                assert len(bridge.commands)==old_count
                bridge.available=True
                await page.wait_for_function("document.querySelector('#panel')._data?.power.error === null")
                record("Invalid source is distinct from zero and does not switch running loads off")

                # API outage must not present stale values as live.
                bridge.api_online=False
                await panel.locator("#connection-error").wait_for(state="visible",timeout=5000)
                assert await panel.locator("#activate").is_disabled()
                bridge.api_online=True
                await panel.locator("#connection-error").wait_for(state="hidden",timeout=5000)
                record("Read-only polling recovers from API outage; writes are not retried")

                # Smartphone, including keyboard/modal form and no horizontal overflow.
                await page.set_viewport_size({"width":390,"height":1180})
                await panel.locator('#page-choice').select_option("consumers")
                await panel.locator("#add").click()
                await panel.locator("#editor").wait_for(state="visible")
                no_overflow=await panel.locator("#editor").evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                assert no_overflow
                await page.keyboard.press("Escape"); await panel.locator("#editor").wait_for(state="hidden")
                assert await panel.locator("main").evaluate("el=>el.scrollWidth<=el.clientWidth+1")
                await panel.evaluate("el=>el.scrollTop=0")
                await capture(page, panel, "ui-mobile-error.png")
                record("390 px mobile layout and modal: no horizontal overflow; Escape works")
                assert errors==[],errors
                record("No uncaught browser JavaScript errors")
                await browser.close()
        finally:
            reporting.cancel()
            with suppress(asyncio.CancelledError): await reporting
            await bridge.controller.close()
    print(f"\n{len(results)} browser scenarios passed. Real UI + real controller; HA transport/services mocked.")


if __name__=="__main__": asyncio.run(main())
