"""v0.3.1: strategy controls, enforced power order, running card borders."""
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
                              dashboard_order='fixed',consumer_ids=['a','b','c'])]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for c in bridge.controller.config.consumers:
            bridge.controller.seed_switch(c.entity_id,'off')
        bridge.controller.owned=['a']
        bridge.values['switch.test_1']='on'
        bridge.controller.seed_switch('switch.test_1','on')
        reports=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),
                                                  headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
                page=await browser.new_page(viewport={'width':1280,'height':900})
                errors=[]
                page.on('pageerror',lambda err: errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles?.length === 1")
                cards=panel.locator('#dashboard-pipeline .pipe-card')
                colors=await cards.evaluate_all('els=>els.map(e=>getComputedStyle(e).borderTopColor)')
                assert colors[0]!=colors[1], colors
                assert await cards.first.evaluate('el=>el.classList.contains("pipe-on")')
                print('PASS: nested consumer ON border is green and distinguishable',flush=True)

                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-power-skip-fields').is_visible()
                assert await panel.locator('#profile-display-row').is_visible()
                await panel.locator('#profile-strategy').select_option('power_desc')
                assert await panel.locator('#profile-display-row').is_hidden()
                assert await panel.locator('#profile-allow-power-skip').input_value() == 'false'
                assert await panel.locator('#profile-members button').count()==0
                rows=await panel.locator('#profile-members .member-row span').all_text_contents()
                assert all(r.startswith(name) for r, name in zip(rows, ['Verbraucher C','Verbraucher A','Verbraucher B'])), rows
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await page.wait_for_function("document.querySelector('#panel')._data.profiles[0].strategy === 'power_desc'")
                assert not bridge.controller.config.profiles[0].allow_power_skip
                await panel.locator('[data-nav="dashboard"]').click()
                display=await panel.locator('#dashboard-pipeline .pipe-card strong').all_text_contents()
                assert display==['Verbraucher C','Verbraucher A','Verbraucher B'],display
                print('PASS: strict descending and automatic order, independent of saved display mode',flush=True)

                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                await panel.locator('#profile-strategy').select_option('power_asc')
                await panel.locator('#profile-allow-power-skip').select_option('true')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert bridge.controller.config.profiles[0].allow_power_skip
                await panel.locator('[data-nav="dashboard"]').click()
                display=await panel.locator('#dashboard-pipeline .pipe-card strong').all_text_contents()
                assert display==['Verbraucher B','Verbraucher A','Verbraucher C'],display
                print('PASS: ascending skips if chosen, and automatically orders cards',flush=True)

                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                await panel.locator('#profile-strategy').select_option('fair_runtime')
                assert await panel.locator('#profile-power-skip-fields').is_visible()
                await panel.locator('#profile-allow-power-skip').select_option('true')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-allow-power-skip').input_value() == 'true'
                await panel.locator('#profile-strategy').select_option('maximum_efficiency')
                assert await panel.locator('#profile-power-skip-fields').is_hidden()
                assert await panel.locator('#profile-display-row').is_hidden()
                await panel.locator('#profile-efficiency-margin').fill('75')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert bridge.controller.config.profiles[0].efficiency_start_margin_w == 75
                print('PASS: Fair skip and efficiency margin are saved; unrelated controls are hidden',flush=True)
                assert not errors, errors
                await browser.close()
        finally:
            reports.cancel()
            with suppress(asyncio.CancelledError):await reports
            await bridge.controller.close()


if __name__=='__main__':asyncio.run(main())
