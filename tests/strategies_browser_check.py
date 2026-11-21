"""v0.3.0: profile strategy editor and compact dashboard in actual Chromium."""
import asyncio
from contextlib import suppress
import shutil
import tempfile

from playwright.async_api import async_playwright
from browser_check import Bridge, capture
import load_core


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[dict(id=key,name=f'Verbraucher {key.upper()}',entity_id=f'switch.test_{i}',watts=w,
                               enabled=True,virtual_confirmed=True)
                          for i,(key,w) in enumerate([('a',800),('b',300),('c',1200)],1)]
        cfg['profiles']=[dict(id='main',name='Standard',enabled=True,strategy='classic',
                              dashboard_order='allocation',consumer_ids=['a','b','c'])]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for c in bridge.controller.config.consumers:bridge.controller.seed_switch(c.entity_id,'off')
        reports=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),
                                                  headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1360,'height':990})
                errors=[]
                page.on('pageerror',lambda err:errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles?.length === 1")
                assert await panel.locator('.pipeline-shell #dashboard-pipeline .profile-card').count() == 1
                assert 'Dynamische Reihenfolge' in await panel.locator('#dashboard-pipeline .profile-meta').inner_text()
                assert 'Klassischer Round Robin' in await panel.locator('#dashboard-pipeline .profile-meta').inner_text()
                assert 'Vorhandene Netzleistung' in await panel.locator('#source').inner_text()
                assert 'sensor.test_grid' not in await panel.locator('#source').inner_text()
                assert await panel.locator('#pipeline-title').get_attribute('title')
                assert await panel.locator('.info-button').first.evaluate('(e)=>e.getBoundingClientRect().width') <= 24
                print('PASS: nested allocation card, contextual help and friendly grid name',flush=True)

                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-strategy option').count()==8
                assert await panel.locator('#profile-fair-fields').is_hidden()
                await panel.locator('#profile-strategy').select_option('fair_runtime')
                assert await panel.locator('#profile-fair-fields').is_visible()
                assert await panel.locator('#profile-efficiency-fields').is_hidden()
                await panel.locator('#profile-runtime-window').select_option('30d')
                await panel.locator('#profile-fair-rotation').fill('1200')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await page.wait_for_function("document.querySelector('#panel')._data.profiles[0].strategy === 'fair_runtime'")
                assert bridge.controller.config.profiles[0].runtime_window == '30d'
                assert bridge.controller.config.profiles[0].fair_rotation_s == 1200
                assert 'Faire Laufzeitverteilung' in await panel.locator('#profiles-list .profile-meta').inner_text()
                print('PASS: Fair Runtime settings persist through real profile editor',flush=True)

                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                await panel.locator('#profile-strategy').select_option('maximum_efficiency')
                assert await panel.locator('#profile-efficiency-fields').is_visible()
                await panel.locator('#profile-efficiency-gain').fill('250')
                await panel.locator('#profile-efficiency-interval').fill('90')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert bridge.controller.config.profiles[0].strategy=='maximum_efficiency'
                assert bridge.controller.config.profiles[0].efficiency_min_gain_w==250
                assert bridge.controller.config.profiles[0].efficiency_interval_s==90
                print('PASS: optimizer thresholds persist; different strategy controls are contextual',flush=True)

                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#source-settings summary').click()
                options=await panel.locator('#grid-entity option').all_text_contents()
                assert any('Vorhandene Netzleistung – sensor.test_grid' in value for value in options)
                assert await panel.locator('#show-data-quality').is_checked()
                await panel.locator('#show-data-quality').uncheck()
                await panel.locator('#save-settings').click()
                await page.wait_for_function("document.querySelector('#panel')._data.config.data_quality_visible === false")
                assert await panel.locator('#freshness-settings').is_hidden()
                assert not bridge.controller.config.data_quality_visible
                await panel.locator('[data-nav="dashboard"]').click()
                assert 'Alter:' not in await panel.locator('#source').inner_text()
                print('PASS: data-quality UI can be hidden; underlying source remains configured',flush=True)

                await page.set_viewport_size({'width':375,'height':850})
                await page.wait_for_timeout(200)
                assert not await panel.evaluate('(el)=>el.scrollWidth>el.clientWidth+1')
                assert await panel.locator('#dashboard-pipeline .profile-card').count()==1
                await capture(page,panel,'ui-strategies-mobile-030.png')
                await page.set_viewport_size({'width':1360,'height':990})
                await capture(page,panel,'ui-strategies-desktop-030.png')
                assert not errors,errors
                print('PASS: mobile layout and browser console without errors',flush=True)
                await browser.close()
        finally:
            reports.cancel()
            with suppress(asyncio.CancelledError): await reports
            await bridge.controller.close()


if __name__=='__main__':asyncio.run(main())
