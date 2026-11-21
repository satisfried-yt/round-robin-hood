"""v0.8.0: real production JS and controller, simulated HA transport and devices."""
import asyncio
import os
from pathlib import Path
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core

async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        bridge.onboarding_bypass=False
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['reserve_w']=0
        cfg['notice_dismissed']=True
        cfg['setup_complete']=True
        cfg['consumers']=[{'id':'a','name':'Testheizung','entity_id':'switch.test_1','watts':500,
                           'enabled':True,'virtual_confirmed':True,'icon':'mdi:radiator'},
                          {'id':'b','name':'Pool','entity_id':'switch.test_2','watts':500,
                           'enabled':True,'virtual_confirmed':True}]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for c in bridge.controller.config.consumers:bridge.controller.seed_switch(c.entity_id,'off')
        reporting=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1200,'height':900})
                page.on('pageerror',lambda err:errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.goto('about:blank')
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                await page.wait_for_function('document.querySelector("#panel")._data?.version === "0.9.3"')
                panel=page.locator('rrh-hood-panel')
                assert 'Power your home. Not their profits.' in await panel.locator('.brand-tagline').inner_text()
                assert 'More for the little guy.' in await panel.locator('.brand-subline').inner_text()
                assert await panel.locator('#donation-link').is_visible()
                assert await panel.locator('#donation-link').get_attribute('href')=='https://www.tipeeestream.com/satisfriedyt/donation'
                print('PASS branded slogan, donation link, version and logo',flush=True)
                await panel.locator('[data-nav="consumers"]').click()
                await panel.locator('.consumer-controls button').count()
                await panel.locator('.consumer').first.get_by_role('button',name='Bearbeiten').click()
                assert await panel.locator('#consumer-icon').get_attribute('type')=='hidden'
                assert await panel.locator('#mdi-choices').count()==0
                assert await panel.locator('#consumer-icon-gallery .icon-choice').count()>=12
                assert await panel.locator('#consumer-icon-gallery .icon-choice span').count()==0
                await panel.locator('.icon-choice[data-icon="mdi:fan"]').click()
                assert await panel.locator('#consumer-icon').input_value()=='mdi:fan'
                assert await panel.locator('.icon-choice[data-icon="mdi:fan"]').get_attribute('aria-pressed')=='true'
                await panel.locator('#cancel-editor').click()
                print('PASS icon-only gallery with keyboard-accessible button controls',flush=True)
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('.profile-controls button').filter(has_text='Bearbeiten').first.click()
                assert await panel.locator('.participants-panel legend').inner_text()=='Teilnehmer des Profils'
                assert await panel.locator('.participants-panel #profile-members').count()==1
                await panel.locator('#cancel-profile').click()
                print('PASS profile members inside dedicated fieldset',flush=True)
                await panel.locator('[data-nav="energy"]').click()
                locations=await panel.evaluate("el=>{let a=el.shadowRoot.querySelector('#energy-form'),b=el.shadowRoot.querySelector('#energy-overview');return [a.getBoundingClientRect().top,b.getBoundingClientRect().top, getComputedStyle(el.shadowRoot.querySelector('.energy-edit-grid')).gridTemplateColumns]}")
                assert locations[0] < locations[1],locations
                assert len(locations[2].split(' '))==3,locations
                print('PASS energy tariff cards top-aligned in three columns',flush=True)
                await panel.locator('[data-nav="about"]').click()
                for url in ['www.tiktok.com/@satisfried_yt','www.youtube.com/@Satisfried_yt','www.twitch.tv/satisfried_yt','github.com/satisfried-yt']:
                    assert await panel.locator(f'a[href*="{url}"]').count()==1,url
                assert 'Satisfried_yt' in await panel.locator('#page-about').inner_text()
                await page.evaluate("document.querySelector('#panel').hass = {...document.querySelector('#panel').hass, config:{version:'2026.11.0'}}")
                await page.wait_for_function("document.querySelector('#panel').shadowRoot.querySelector('#ha-core-version').textContent === '2026.11.0'")
                print('PASS external profile links and HA Core diagnostic version',flush=True)
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#dashboard-settings summary').click()
                await panel.locator('#show-donation').uncheck()
                await panel.locator('#save-settings').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config?.dashboard?.show_donation === false')
                await panel.locator('[data-nav="dashboard"]').click()
                assert await panel.locator('#donation-link').is_hidden()
                print('PASS donation link disabled and persisted, without changing statistics',flush=True)
                # All six UI languages must carry v0.8 strings.
                for language,expected in [('en','Buy me a drink'),('fr','Offrir un verre'),('es','Invítame a una copa'),('pt','Paga-me uma bebida'),('it','Offrimi un drink'),('de','Gib einen Drink aus')]:
                    await panel.locator('[data-nav="settings"]').click()
                    if not await panel.locator('#dashboard-settings').evaluate('el=>el.open'):
                        await panel.locator('#dashboard-settings summary').click()
                    await panel.locator('#stat-language').select_option(language)
                    await panel.locator('#save-settings').click()
                    await page.wait_for_function(f'document.querySelector("#panel")._data?.config?.dashboard?.language === "{language}"')
                    assert await panel.locator('#donation-link').inner_text()==expected,language
                print('PASS newly introduced UI strings available across DE/EN/FR/ES/PT/IT',flush=True)
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#factory-reset-open').click()
                await panel.locator('#factory-reset-dialog').wait_for(state='visible')
                assert await panel.locator('#reset-proceed').is_disabled()
                await panel.locator('#reset-confirm-input').fill('DELETE')
                assert await panel.locator('#reset-proceed').is_disabled()
                await panel.locator('#reset-confirm-input').fill('RESET ROUND ROBIN HOOD')
                assert await panel.locator('#reset-proceed').is_enabled()
                await panel.locator('#reset-proceed').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config?.consumers?.length === 0',timeout=10000)
                assert not bridge.controller.config.consumers
                assert not bridge.controller.config.profiles
                assert bridge.controller.config.grid_entity==''
                assert not bridge.controller.config.notice_dismissed
                assert bridge.controller.mode=='stopped'
                assert await panel.locator('#safety-dialog').is_visible()
                assert ('switch.test_1','off') in bridge.commands
                print('PASS typed confirmation, real all-OFF command and persisted full reset',flush=True)
                await panel.locator('#notice-continue').click()
                await panel.locator('#welcome-dialog').wait_for(state='visible',timeout=10000)
                await panel.locator('#welcome-wizard').click()
                await panel.locator('#setup-wizard').wait_for(state='visible',timeout=10000)
                assert not bridge.controller.config.setup_complete
                print('PASS reset reopens safety notice then fresh setup wizard; switches remain off',flush=True)
                assert not errors,errors
                await browser.close()
        finally:
            reporting.cancel()
            try:await reporting
            except asyncio.CancelledError:pass
if __name__=='__main__':asyncio.run(main())
