"""v0.4.0: fixed period labels, expiry and 14-day editor roundtrip in real UI."""
import asyncio
from contextlib import suppress
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[dict(id='a',name='Wassertest',entity_id='switch.test_1',watts=1800,
                               enabled=True,virtual_confirmed=True)]
        cfg['profiles']=[dict(id='main',name='Standard',enabled=True,strategy='fair_energy',
                              dashboard_order='allocation',consumer_ids=['a'],runtime_window='24h',
                              fair_rotation_s=60,allow_power_skip=True)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        bridge.controller.seed_switch('switch.test_1','off')
        moment=[1_700_000_000.0]
        bridge.controller.wall_clock=lambda:moment[0]
        bridge.controller.fairness.ensure_started('fair_energy','main',moment[0]-86400+30)
        bridge.controller.fairness.segments=[['fair_energy','main','a',moment[0]-100,moment[0]-50,1800]]
        bridge.controller.fairness.totals['fair_energy']['main']={'a':25}
        task=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,
                                                  args=['--no-sandbox','--disable-dev-shm-usage'])
                page=await browser.new_page(viewport={'width':1200,'height':900})
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function('document.querySelector("#panel")._data?.profiles?.length === 1')
                assert '0,025 kWh' in await panel.locator('.fairness-stat').first.inner_text()
                text=await panel.locator('#dashboard-pipeline .fair-period').inner_text()
                assert 'Feste Periode (24h)' in text and 'danach Neustart bei 0' in text,text
                print('PASS: anchored 24-hour period visible with accurate Wh and next reset',flush=True)
                moment[0]+=31
                await page.wait_for_function('document.querySelector("#panel")._data?.profiles?.[0]?.fair_values?.a === 0', timeout=9000)
                assert '0,000 kWh' in await panel.locator('.fairness-stat').first.inner_text()
                assert bridge.controller.status()['profiles'][0]['fair_period_end'] == 1_700_000_000-86400+30+2*86400
                print('PASS: crossing the fixed boundary resets visible credit automatically',flush=True)
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-runtime-window option[value="14d"]').count() == 1
                await panel.locator('#profile-runtime-window').select_option('14d')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await page.wait_for_function('document.querySelector("#panel")._data?.profiles?.[0]?.runtime_window === "14d"')
                assert 'Feste Periode (14d)' in await panel.locator('#profiles-list .fair-period').inner_text()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-runtime-window').input_value() == '14d'
                print('PASS: 14-day period persists after save/reopen and changes live label',flush=True)
                await page.set_viewport_size({'width':390,'height':850})
                assert await panel.locator('#profile-fair-period-info').count()==1
                assert not errors,errors
                print('PASS: fixed period UI remains usable on narrow mobile viewport',flush=True)
                await browser.close()
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):await task
            await bridge.controller.close()


if __name__ == '__main__':asyncio.run(main())
