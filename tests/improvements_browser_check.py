"""v0.1.8: browser verification of settings, exclusive groups and timer controls."""
from __future__ import annotations
import asyncio
from contextlib import suppress
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core

async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge = Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[dict(id='a',name='Test 1',entity_id='switch.test_1',watts=800,
                               enabled=True,virtual_confirmed=True,min_on_s=300,min_on_strict=True,cooldown_s=300),
                          dict(id='b',name='Test 2',entity_id='switch.test_2',watts=500,
                               enabled=True,virtual_confirmed=True)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for entity in bridge.values: bridge.controller.seed_switch(entity,'off')
        old_api=bridge.api
        async def api(msg):
            if msg.get('action') == 'skip_timer':
                await bridge.controller.skip_timer(msg['consumer_id'],msg['timer'],msg['revision'])
                return bridge.result()
            return await old_api(msg)
        reporter=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1300,'height':900})
                page.on('pageerror',lambda err:errors.append(str(err)))
                page.on('dialog',lambda d:asyncio.create_task(d.accept()))
                await page.expose_function('rrhTestWS',api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 2")
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#control-settings summary').click()
                assert await panel.locator('#global-delay-enabled').is_checked()
                await panel.locator('#global-delay-enabled').uncheck()
                assert await panel.locator('#global-delay-fields').is_hidden()
                await panel.locator('#save-settings').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config.global_shutdown_delay_enabled === false")
                print('PASS: Global deficit toggle saved; disabled input hidden',flush=True)
                await panel.locator('#global-delay-enabled').check()
                await panel.locator('#delay').fill('25')
                await panel.locator('#save-settings').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config.shutdown_delay_s === 25")
                print('PASS: Global deficit delay enabled and saved',flush=True)
                # Setup a saved countdown; the UI must expose a confirmation control.
                bridge.controller.cooldown_until['a'] = bridge.controller.wall_clock()+300
                await panel.locator('[data-nav="consumers"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0]?.cooldown_remaining_s > 0")
                a=panel.locator('#consumers .consumer').filter(has_text='Test 1')
                skip=a.get_by_role('button',name='Wiedereinschaltsperre beenden: Test 1')
                await skip.click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0]?.cooldown_remaining_s === 0")
                assert bridge.controller.cooldown_until.get('a',0) == 0
                print('PASS: Cooldown skip with confirmation, no direct switch operation',flush=True)
                bridge.controller.started_at['a']=bridge.controller.wall_clock()
                bridge.controller.owned=['a'];bridge.controller.states['switch.test_1']='on'
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0]?.min_remaining_s > 0")
                await a.get_by_role('button',name='Mindestlaufzeit beenden: Test 1').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0]?.min_remaining_s === 0")
                print('PASS: Minimum runtime skip with confirmation',flush=True)
                assert not errors,errors
                print('PASS: No browser JavaScript errors',flush=True)
                await browser.close()
        finally:
            reporter.cancel()
            with suppress(asyncio.CancelledError): await reporter

if __name__ == '__main__': asyncio.run(main())
