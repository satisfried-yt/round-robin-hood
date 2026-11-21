"""v0.3.2: fair strategy controls, live metric cards, isolated confirmed reset."""
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
        cfg['consumers'] = [dict(id=k,name=f'Verbraucher {k.upper()}',entity_id=f'switch.test_{i}',
                                 watts=w,enabled=True,virtual_confirmed=True)
                            for i,(k,w) in enumerate((('a',1800),('b',500)),1)]
        cfg['profiles'] = [dict(id='main',name='Standard',enabled=True,strategy='fair_runtime',
                                dashboard_order='allocation',consumer_ids=['a','b'],runtime_window='24h',
                                fair_rotation_s=60,allow_power_skip=True)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for c in bridge.controller.config.consumers:
            bridge.controller.seed_switch(c.entity_id,'off')
        bridge.controller.fairness.totals['fair_runtime']['main']={'a':3661, 'b':240}
        bridge.controller.fairness.totals['fair_energy']['main']={'a':1800,'b':500}
        # Fixed period anchored at the start of yesterday's test window.
        now=bridge.controller.wall_clock()
        bridge.controller.fairness.ensure_started('fair_runtime','main',now-7000)
        bridge.controller.fairness.ensure_started('fair_energy','main',now-7000)
        bridge.controller.fairness.segments=[
            ['fair_runtime','main','a',now-3661,now,1800],
            ['fair_runtime','main','b',now-240,now,500],
            ['fair_energy','main','a',now-3600,now,1800],
            ['fair_energy','main','b',now-3600,now,500],
        ]
        reports=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),
                                                  headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                page=await browser.new_page(viewport={'width':1200,'height':940})
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function('document.querySelector("#panel")._data?.profiles?.length === 1')
                await panel.locator('#dashboard-pipeline .fairness-stat').first.wait_for(timeout=4000)
                assert await panel.locator('#dashboard-pipeline .fairness-stat').count()==2
                times=await panel.locator('#dashboard-pipeline .fairness-stat').all_text_contents()
                assert sorted(times)==['Fair-Zeit (24h): 00:04:00','Fair-Zeit (24h): 01:01:01'],times
                assert 'Faire Laufzeitverteilung' in await panel.locator('#dashboard-pipeline .profile-meta').inner_text()
                print('PASS: strategy-scoped Fair Runtime hours displayed on consumer cards',flush=True)

                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                options=await panel.locator('#profile-strategy option').all_text_contents()
                assert len(options)==8 and 'Faire Energieverteilung' in options,options
                assert await panel.locator('#profile-fair-fields').is_visible()
                assert await panel.locator('#profile-power-skip-fields').is_visible()
                assert await panel.locator('#profile-fair-reset').is_enabled()
                assert await panel.locator('#profile-runtime-window').input_value()=='24h'
                assert await panel.locator('#profile-runtime-window option[value="14d"]').count()==1
                assert 'Feste Periode' in await panel.locator('#profile-fair-period-info').inner_text()
                assert await panel.locator('#profile-fair-rotation').input_value()=='60'
                assert await panel.locator('#profile-fair-gap-runtime').input_value()=='60'
                assert await panel.locator('#profile-fair-gap-runtime-row').is_visible()
                assert await panel.locator('#profile-fair-gap-energy-row').is_hidden()
                print('PASS: 8 strategies, fair time window, rotation and reset control present',flush=True)

                await panel.locator('#profile-strategy').select_option('fair_energy')
                assert await panel.locator('#profile-fair-fields').is_visible()
                assert await panel.locator('#profile-fair-gap-runtime-row').is_hidden()
                assert await panel.locator('#profile-fair-gap-energy-row').is_visible()
                assert await panel.locator('#profile-fair-reset').is_enabled()  # Existing profile can reset selected metric before saving.
                await panel.locator('#profile-fair-gap-energy').fill('12.5')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await page.wait_for_function('document.querySelector("#panel")._data.profiles[0].strategy === "fair_energy"')
                assert bridge.controller.config.profiles[0].fair_min_gap_wh == 12.5
                await panel.locator('[data-nav="dashboard"]').click()
                texts=await panel.locator('#dashboard-pipeline .fairness-stat').all_text_contents()
                assert len(texts)==2 and any('1,800 kWh' in x for x in texts) and any('0,500 kWh' in x for x in texts),texts
                print('PASS: Fair Energy uses kWh, not general runtime, without metric crossover',flush=True)

                # The reset is explicitly confirmed through a native dialog.
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-fair-gap-energy').input_value() == '12.5'
                async def accept_dialog(dialog):
                    assert 'zurücksetzen' in dialog.message
                    await dialog.accept()
                page.on('dialog',accept_dialog)
                await panel.locator('#profile-fair-reset').click()
                await page.wait_for_function('document.querySelector("#panel")._data.profiles[0].fair_values.a === 0')
                assert bridge.controller.fairness.totals['fair_energy'].get('main') is None
                assert bridge.controller.fairness.totals['fair_runtime']['main']['a']==3661
                await panel.locator('#profile-editor').wait_for(state='visible')
                assert await panel.locator('#profile-strategy').input_value()=='fair_energy'
                print('PASS: confirmed profile-specific energy reset, other metric preserved',flush=True)

                # Switching strategy in the open editor must not keep the reset
                # button disabled. Reset also must not silently lose the draft.
                await panel.locator('#profile-strategy').select_option('fair_runtime')
                assert await panel.locator('#profile-fair-reset').is_enabled()
                await panel.locator('#profile-fair-reset').click()
                assert await panel.locator('#profile-strategy').input_value()=='fair_runtime'
                assert bridge.controller.fairness.totals['fair_runtime'].get('main') is None
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await page.wait_for_function('document.querySelector("#panel")._data.profiles[0].strategy === "fair_runtime"')
                print('PASS: reset available immediately after strategy change without reopening',flush=True)

                await page.set_viewport_size({'width':390,'height':850})
                await panel.locator('#profile-editor').evaluate('(el)=>el.close()')
                await panel.locator('#page-choice').select_option('dashboard')
                assert await panel.locator('#dashboard-pipeline .fairness-stat').count()==2
                assert not errors,errors
                print('PASS: fair cards present in smartphone layout, no browser exceptions',flush=True)
                await browser.close()
        finally:
            reports.cancel()
            with suppress(asyncio.CancelledError): await reports
            await bridge.controller.close()


if __name__=='__main__':
    asyncio.run(main())
