"""Real rendered tab/mobile navigation and backend emergency through an HA test bridge.

Browser/HA transport are different: Chromium runs the shipping JS; fake HA transport,
real product controller and a separate asynchronous grid reporter drive the scenario.
"""
from __future__ import annotations
import asyncio
from contextlib import suppress
import os
from pathlib import Path
import shutil
import tempfile

from playwright.async_api import async_playwright
from browser_check import Bridge, capture
import load_core

ROOT = load_core.ROOT


async def main():
    results=[]; errors=[]
    def check(label):
        results.append(label); print('PASS:',label,flush=True)
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[
            {'id':id, 'name':name, 'entity_id':f'switch.test_{i}', 'watts':watts,
             'enabled':True, 'virtual_confirmed':True}
            for i,(id,name,watts) in enumerate((('a','Testheizung',1800),('b','Pooltechnik',500),('c','Zusatzverbraucher',800)),1)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for e in bridge.values: bridge.controller.seed_switch(e,'off')
        reporting=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                executable=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chromium-browser')
                browser=await pw.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1360,'height':960})
                page.on('pageerror',lambda error:errors.append(str(error)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html()); await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                assert await panel.locator('#page-dashboard').is_visible()
                assert await panel.locator('#page-consumers').is_hidden()
                assert await panel.locator('#page-settings').is_hidden()
                assert await panel.locator('.nav-tabs button').count()==7
                assert await panel.locator('[data-nav="dashboard"]').get_attribute('aria-current')=='page'
                check('Seven-page desktop navigation defaults to dashboard and shows one page')
                assert await panel.locator('#dashboard-pipeline .pipe-card').count()==3
                assert await panel.locator('#managed').inner_text()=='0 W'
                assert await panel.locator('#activate').is_enabled()
                await capture(page,panel,'ui-dashboard.png')
                check('Dashboard shows controller state, grid, managed power and read-only queue cards')
                await panel.locator('[data-nav="profiles"]').click()
                assert await panel.locator('#page-profiles').is_visible()
                assert await panel.locator('#page-dashboard').is_hidden()
                assert await panel.locator('#profiles-list .profile-card').count()==1
                await panel.locator('[data-nav="energy"]').click()
                assert await panel.locator('#page-energy').is_visible()
                assert await panel.locator('#energy-overview .stats-box').count() >= 12
                assert bridge.commands==[]
                check('Editable profile page and live cost statistics page; navigation sends no commands')
                await panel.locator('[data-nav="consumers"]').click()
                assert await panel.locator('#consumers > .consumer').count()==3
                await capture(page,panel,'ui-consumers.png')
                assert await panel.locator('#add').is_enabled()
                check('Consumer management remains on its dedicated card page')
                await panel.locator('[data-nav="settings"]').click()
                assert await panel.locator('#page-settings').is_visible()
                assert await panel.locator('#source-settings summary').is_visible()
                await capture(page,panel,'ui-settings.png')
                check('Settings live on a separate page with the existing entity and safety inputs')
                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator('#activate').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'running'")
                bridge.base=2500
                for _ in range(80):
                    if len(bridge.commands)>=2: break
                    await asyncio.sleep(.1)
                assert bridge.commands==[('switch.test_1','on'),('switch.test_2','on')],bridge.commands
                await page.wait_for_function("document.querySelector('#panel')._data?.managed_w === 2300")
                assert '2.300 W' in await panel.locator('#managed').inner_text()
                assert await panel.locator('#dashboard-pipeline .pipe-on').count()==2
                assert await panel.locator('#dashboard-pipeline .pipe-next').count()==1
                check('Actual controller allocates independently and UI identifies running devices and managed power')
                before_cursor=bridge.controller.cursor
                # Main OFF also stops a switch not owned by RRH; it is not a pause.
                bridge.values['switch.test_3']='on'
                bridge.controller.observe_switch('switch.test_3','on',explicit_external=True)
                await panel.locator('#main-off').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'stopped' && !document.querySelector('#panel')._offRequested")
                assert all(v=='off' for v in bridge.values.values())
                assert bridge.controller.cursor==before_cursor
                assert bridge.controller.owned==[]
                assert bridge.commands[-3:]==[('switch.test_1','off'),('switch.test_2','off'),('switch.test_3','off')],bridge.commands
                check('Main OFF stops all three configured switches including an external one; cursor unchanged')
                await panel.locator('[data-nav="settings"]').click()
                assert await panel.locator('#save-settings').is_enabled()
                check('After emergency OFF, settings can be edited, but no automatic restart occurs')
                await panel.locator('[data-nav="profiles"]').click()
                await page.evaluate("document.querySelector('#panel').hass = {...document.querySelector('#panel').hass, locale:{language:'en'}}")
                assert await panel.locator('[data-nav="consumers"]').inner_text()=='Consumers'
                assert 'Profiles & priority' in (await panel.locator('#page-profiles').inner_text())
                await page.evaluate("document.querySelector('#panel').hass = {...document.querySelector('#panel').hass, locale:{language:'de'}}")
                assert await panel.locator('[data-nav="consumers"]').inner_text()=='Verbraucher'
                check('Navigation and informational pages are localized DE/EN using HA language')
                await page.set_viewport_size({'width':390,'height':844})
                assert await panel.locator('.nav-tabs').is_hidden()
                assert await panel.locator('#page-choice').is_visible()
                await panel.locator('#page-choice').select_option('dashboard')
                assert await panel.locator('#page-dashboard').is_visible()
                assert await panel.locator('#page-profiles').is_hidden()
                assert await panel.locator('main').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
                await capture(page,panel,'ui-mobile-navigation.png')
                check('Mobile single-dropdown page selection, one visible pane and no horizontal overflow')
                # Closing browser does not stop a controller running on an HA process.
                await page.close()
                bridge.base=2500
                await bridge.controller.activate()
                for _ in range(50):
                    if any(t=='on' for e,t in bridge.commands[-3:]): break
                    await asyncio.sleep(.1)
                assert bridge.controller.mode=='running'
                assert any(t=='on' for e,t in bridge.commands[-3:]),bridge.commands
                check('Backend keeps processing and switching after all browser views are closed')
                assert not errors,errors
                check('No uncaught browser JavaScript errors')
                await browser.close()
        finally:
            reporting.cancel()
            with suppress(asyncio.CancelledError): await reporting
            await bridge.controller.close()
    print(f'\n{len(results)} navigation/emergency browser checks passed (real UI + controller, HA boundary simulated).')

if __name__=='__main__': asyncio.run(main())
