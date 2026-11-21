"""Shipping frontend timing editor and active-timer labels, actual Chromium + backend bridge."""
import asyncio
from contextlib import suppress
import os
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict();cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[dict(id='a',name='Heizung',entity_id='switch.test_1',watts=500,enabled=True,virtual_confirmed=True)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        bridge.controller.seed_switch('switch.test_1','off')
        reporting=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1250,'height':950})
                errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html());await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 1")
                await panel.locator('[data-nav="consumers"]').click()
                await panel.locator('[data-control="edit"]').first.click()
                assert await panel.locator('#min-fields').is_hidden()
                assert await panel.locator('#cool-fields').is_hidden()
                await panel.locator('#min-enable').check();await panel.locator('#cool-enable').check()
                assert await panel.locator('#min-fields').is_visible()
                assert await panel.locator('#cool-fields').is_visible()
                await panel.locator('#min-m').fill('12')
                await panel.locator('#min-s').fill('15')
                await panel.locator('#min-strict').check()
                await panel.locator('#cool-m').fill('5')
                await panel.locator('#cool-mode').select_option('wait')
                await panel.locator('#save-consumer').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config.consumers[0].cooldown_s === 300")
                c=bridge.controller.config.consumers[0]
                assert (c.min_on_s,c.min_on_strict,c.cooldown_s,c.cooldown_wait)==(735,True,300,True)
                print('PASS: Conditional timing fields and per-device settings persisted via real editor',flush=True)
                await panel.locator('[data-control="edit"]').first.click()
                assert await panel.locator('#min-m').input_value()=='12'
                assert await panel.locator('#min-s').input_value()=='15'
                assert await panel.locator('#cool-m').input_value()=='5'
                await panel.locator('#cancel-editor').click()
                print('PASS: Timer controls load saved settings on reopening',flush=True)
                bridge.controller.started_at['a']=bridge.controller.wall_clock()
                bridge.controller.owned=['a'];bridge.controller.states['switch.test_1']='on'
                bridge.controller.wake();await bridge.controller.settle()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0].min_remaining_s > 0")
                assert 'Mindestlaufzeit:' in await panel.locator('.timer-chip').first.inner_text()
                await panel.locator('[data-nav="dashboard"]').click()
                assert 'Mindestlaufzeit:' in await panel.locator('#dashboard-pipeline').inner_text()
                print('PASS: Remaining minimum runtime visible on consumer and dashboard cards',flush=True)
                bridge.controller.mode='paused'
                bridge.controller.owned=[]
                bridge.controller.states['switch.test_1']='off'
                bridge.controller.started_at={}
                bridge.controller.cooldown_until['a']=bridge.controller.wall_clock()+300
                bridge.controller.wake();await bridge.controller.settle()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0].cooldown_remaining_s > 0")
                assert 'Sperre:' in await panel.locator('#dashboard-pipeline').inner_text()
                await panel.locator('[data-nav="consumers"]').click()
                assert 'Sperre:' in await panel.locator('.timer-chip').first.inner_text()
                print('PASS: Remaining cooldown visible on consumer and dashboard cards',flush=True)
                await page.set_viewport_size({'width':390,'height':844})
                assert not await panel.locator('main').evaluate('el=>el.scrollWidth>el.clientWidth+1')
                print('PASS: Timer card mobile layout has no horizontal overflow',flush=True)
                assert not errors,errors
                print('PASS: No JavaScript exceptions',flush=True)
                await browser.close()
        finally:
            reporting.cancel()
            with suppress(asyncio.CancelledError):await reporting
            await bridge.controller.close()

if __name__=='__main__': asyncio.run(main())
