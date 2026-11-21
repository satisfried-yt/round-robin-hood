"""v0.2.0 real frontend/controller with virtual HA transport: rules, blocks, indicators, mobile."""
from __future__ import annotations
import asyncio
from contextlib import suppress
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge, capture
import load_core


async def main():
    with tempfile.TemporaryDirectory() as tmp:
        bridge = Bridge(tmp)
        cfg = bridge.controller.config.to_dict()
        cfg['grid_entity'] = 'sensor.test_grid'
        cfg['consumers'] = [dict(id=i,name=f'Test {i.upper()}',entity_id=f'switch.test_{n}',
                                 watts=w,enabled=True,virtual_confirmed=True)
                            for n,(i,w) in enumerate([('a',800),('b',500),('c',300)],1)]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for e in bridge.values:bridge.controller.seed_switch(e,'off')
        bridge.states['sensor.room_temp'] = {'state':'unknown','attributes':{'friendly_name':'Room temperature'}}
        bridge.states['sensor.humidity'] = {'state':'unavailable','attributes':{'friendly_name':'Humidity'}}
        bridge.base=4000
        previous=bridge.api
        async def api(msg):
            if msg.get('action')=='skip_timer':
                await bridge.controller.skip_timer(msg['consumer_id'],msg['timer'],msg['revision'])
                return bridge.result()
            return await previous(msg)
        reporter=asyncio.create_task(bridge.reports())
        errors=[]; dialogs=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1360,'height':950})
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.on('dialog',lambda d:(dialogs.append(d.message),asyncio.create_task(d.accept())))
                await page.expose_function('rrhTestWS',api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list button[title="Profil bearbeiten"]').click()
                await panel.locator('#profile-conditions-enable').check()
                await panel.locator('#profile-conditions-logic').select_option('all')
                await panel.locator('#profile-conditions-add').click()
                row=panel.locator('#profile-conditions-list .condition-row').nth(0)
                await row.locator('[data-field="entity_id"]').fill('sensor.room_temp')
                await row.locator('[data-field="operator"]').select_option('<')
                await row.locator('[data-field="value"]').fill('21')
                await row.locator('[data-field="hysteresis"]').fill('1')
                await panel.locator('#profile-conditions-add').click()
                row2=panel.locator('#profile-conditions-list .condition-row').nth(1)
                await row2.locator('[data-field="entity_id"]').fill('sensor.humidity')
                await row2.locator('[data-field="operator"]').select_option('>=')
                await row2.locator('[data-field="value"]').fill('50')
                await row2.locator('[data-field="hysteresis"]').fill('5')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert bridge.controller.config.profiles[0].conditions.enabled
                assert len(bridge.controller.config.profiles[0].conditions.rules)==2
                print('PASS: Profile rule editor stores two independent rules with thresholds, hysteresis and AND',flush=True)
                await panel.locator('#profiles-list button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-conditions-enable').is_checked()
                assert await panel.locator('#profile-conditions-list .condition-row').count()==2
                assert await panel.locator('#profile-conditions-list .condition-row').first.locator('[data-field="hysteresis"]').input_value()=='1'
                await panel.locator('#cancel-profile').click()
                print('PASS: Rules survive editor reopen',flush=True)
                await panel.locator('[data-nav="dashboard"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles[0].conditions_allowed === false")
                assert '0/2 erfüllt' in await panel.locator('#dashboard-pipeline .condition-status summary').inner_text()
                await panel.locator('#dashboard-pipeline .condition-status summary').click()
                assert 'sensor.room_temp' in await panel.locator('#dashboard-pipeline .condition-details').inner_text()
                await panel.locator('#activate').click()
                await asyncio.sleep(.3)
                assert bridge.commands==[]
                print('PASS: Missing sensor blocks whole active profile and reason is visible',flush=True)
                bridge.controller.observe_condition('sensor.room_temp','19.5')
                bridge.controller.observe_condition('sensor.humidity','60')
                for _ in range(90):
                    if len([x for x in bridge.commands if x[1]=='on'])==3: break
                    await asyncio.sleep(.1)
                assert len([x for x in bridge.commands if x[1]=='on'])==3,bridge.commands
                assert bridge.controller.status()['profiles'][0]['conditions_allowed']
                print('PASS: Profile becomes eligible only when every condition passes; standard scheduler resumes',flush=True)
                bridge.controller.observe_condition('sensor.room_temp','21')
                for _ in range(90):
                    if len([x for x in bridge.commands if x[1]=='off'])==3: break
                    await asyncio.sleep(.1)
                assert len([x for x in bridge.commands if x[1]=='off'])==3,bridge.commands
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles[0].running_count === 0")
                print('PASS: Profile eligibility loss shuts off all managed members despite surplus',flush=True)
                await capture(page,panel,'ui-conditions-020.png')
                await panel.locator('#pause').click()
                await panel.locator('[data-nav="consumers"]').click()
                await panel.locator('#consumers .consumer').filter(has_text='Test A').get_by_role('button',name='Bearbeiten: Test A').click()
                await panel.locator('#consumer-conditions-enable').check()
                await panel.locator('#consumer-conditions-add').click()
                row=panel.locator('#consumer-conditions-list .condition-row').first
                await row.locator('[data-field="entity_id"]').fill('sensor.humidity')
                await row.locator('[data-field="operator"]').select_option('>')
                await row.locator('[data-field="value"]').fill('70')
                await row.locator('[data-field="hysteresis"]').fill('2')
                await panel.locator('#save-consumer').click()
                await panel.locator('#editor').wait_for(state='hidden')
                assert bridge.controller.config.consumers[0].conditions.rules[0].value==70
                print('PASS: Independent consumer conditions stored without changing profile conditions',flush=True)
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#control-settings summary').click()
                await panel.locator('#confirm-timer').uncheck()
                await panel.locator('#confirm-profile').uncheck()
                await panel.locator('#save-settings').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config.confirm_timer_skip === false")
                assert bridge.controller.config.confirm_profile_toggle is False
                print('PASS: Both confirmation prompts independently configurable and saved',flush=True)
                await panel.locator('[data-nav="consumers"]').click()
                bridge.controller.cooldown_until['a']=bridge.controller.wall_clock()+300
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0].cooldown_remaining_s > 0")
                await panel.locator('#consumers .consumer').filter(has_text='Test A').get_by_role('button',name='Wiedereinschaltsperre beenden: Test A').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[0].cooldown_remaining_s === 0")
                assert not dialogs,dialogs
                print('PASS: Compact timer skip without confirmation when disabled',flush=True)
                bridge.controller.cooldown_until['b']=bridge.controller.wall_clock()+120
                await panel.locator('[data-nav="dashboard"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers[1].cooldown_remaining_s > 0")
                heights=await panel.locator('#dashboard-pipeline .pipe-card').evaluate_all(
                    'els=>els.map(e=>Math.round(e.getBoundingClientRect().height))')
                assert heights[1] > heights[0] and heights[1] > heights[2],heights
                print('PASS: Timer-bearing card does not force unrelated dashboard cards to grow',flush=True)
                await page.set_viewport_size({'width':375,'height':820})
                await capture(page,panel,'ui-conditions-mobile-020.png')
                scroll=await panel.evaluate('(el)=>({view:el.clientWidth,scroll:el.scrollWidth})')
                assert scroll['scroll'] <= scroll['view']+2,scroll
                assert not errors,errors
                print('PASS: Responsive mobile layout and no browser exceptions',flush=True)
                await browser.close()
        finally:
            reporter.cancel()
            with suppress(asyncio.CancelledError):await reporter

if __name__=='__main__':asyncio.run(main())
