"""Ship-version frontend + real controller: profile workflow and mobile rendering.

Only the HA websocket/states/services boundary is replaced by Bridge.
"""
from __future__ import annotations
import asyncio
import base64
from contextlib import suppress
import shutil
import tempfile

from playwright.async_api import async_playwright
from browser_check import Bridge, capture
import load_core

PNG_1PX = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9YcX6nYAAAAASUVORK5CYII=')


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[{'id':i,'name':name,'entity_id':entity,'watts':w,
                           'enabled':True,'virtual_confirmed':True}
                          for i,name,entity,w in [('a','Heizung 1','switch.test_1',1800),
                                                  ('b','Gerät 2','switch.test_2',500),
                                                  ('c','Entfeuchter 4','switch.test_3',800)]]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for entity in bridge.values: bridge.controller.seed_switch(entity,'off')
        bridge.base=1200
        reporter=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1360,'height':960})
                page.on('pageerror',lambda err:errors.append(str(err)))
                page.on('dialog',lambda dialog:asyncio.create_task(dialog.accept()))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                assert await panel.locator('#menu').count()==0
                assert await panel.locator('#dashboard-pipeline .profile-card').count()==1
                assert await panel.locator('#dashboard-pipeline .consumer-icon').count()==3
                assert await panel.locator('#dashboard-pipeline .ordinal').count()==0
                print('PASS: Dashboard group layout, icons, no obsolete HA sidebar toggle or ordinal numbers',flush=True)

                # Already assigned consumers must not be offered in another profile.
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#add-profile').click()
                await panel.locator('#profile-name').fill('Sommer')
                await panel.locator('#profile-display').select_option('allocation')
                assert await panel.locator('#profile-members .member-row').count()==0
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                # First explicitly unassign the 800 W consumer from Standard.
                await panel.locator('#profiles-list .profile-card').first.locator('button[title="Profil bearbeiten"]').click()
                row=panel.locator('#profile-members .member-row').filter(has_text='Entfeuchter 4')
                await row.locator('input[type="checkbox"]').uncheck()
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                await panel.locator('#profiles-list .profile-card').filter(has_text='Sommer').locator('button[title="Profil bearbeiten"]').click()
                row=panel.locator('#profile-members .member-row').filter(has_text='Entfeuchter 4')
                await row.locator('input[type="checkbox"]').check()
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert len(bridge.controller.config.profiles)==2
                assert bridge.controller.config.profiles[0].consumer_ids==('a','b')
                assert bridge.controller.config.profiles[1].consumer_ids==('c',)
                assert len(set(i for p in bridge.controller.config.profiles for i in p.consumer_ids))==3
                assert bridge.commands==[]
                print('PASS: Create and save Classic Summer group; explicit consumer reassignment without duplication or switch commands',flush=True)

                # Reorder priorities; these are persisted configuration changes only.
                summer=panel.locator('#profiles-list .profile-card').filter(has_text='Sommer')
                await summer.locator('button[title="Priorität erhöhen"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles[0].name === 'Sommer'")
                assert bridge.controller.config.profiles[0].name=='Sommer'
                await panel.locator('#profiles-list .profile-card').first.locator('button[title="Priorität verringern"]').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles[0].name === 'Standard'")
                print('PASS: Priority order can be changed and saved; highest-priority group stays first',flush=True)

                # Fixed vs allocation display order is selected in the profile editor.
                standard=panel.locator('#profiles-list .profile-card').first
                await standard.locator('button[title="Profil bearbeiten"]').click()
                await panel.locator('#profile-display').select_option('allocation')
                await panel.locator('#save-profile').click()
                await panel.locator('#profile-editor').wait_for(state='hidden')
                assert bridge.controller.config.profiles[0].dashboard_order=='allocation'
                print('PASS: Per-profile dashboard ordering is editable and persisted',flush=True)

                # Edit icon, optional custom PNG image, and underload delay.
                await panel.locator('[data-nav="consumers"]').click()
                third=panel.locator('#consumers .consumer').filter(has_text='Entfeuchter 4')
                await third.get_by_role('button',name='Bearbeiten: Entfeuchter 4').click()
                await panel.locator('.icon-choice[data-icon="mdi:fan"]').click()
                await panel.locator('#override-delay').check()
                await panel.locator('#consumer-delay').fill('45')
                await panel.locator('#consumer-image').set_input_files({'name':'fan.png','mimeType':'image/png','buffer':PNG_1PX})
                await panel.locator('#consumer-icon-preview img').wait_for(state='visible')
                await panel.locator('#save-consumer').click()
                await panel.locator('#editor').wait_for(state='hidden')
                c=bridge.controller.config.consumers[2]
                assert c.icon=='mdi:fan' and c.icon_image.startswith('data:image/png;base64,')
                assert c.shutdown_delay_s==45
                assert await panel.locator('#consumers .consumer').filter(has_text='Entfeuchter 4').locator('.consumer-icon img').count()==1
                print('PASS: Native MDI icon, small own PNG icon and per-device 45s deficit delay saved by editor',flush=True)
                await third.get_by_role('button',name='Bearbeiten: Entfeuchter 4').click()
                assert await panel.locator('#consumer-icon').input_value()=='mdi:fan'
                assert await panel.locator('#override-delay').is_checked()
                assert await panel.locator('#consumer-delay').input_value()=='45'
                await panel.locator('#consumer-image-clear').click()
                await panel.locator('#save-consumer').click()
                await panel.locator('#editor').wait_for(state='hidden')
                assert bridge.controller.config.consumers[2].icon_image is None
                print('PASS: Consumer advanced settings survive reopening and custom icon can be removed',flush=True)

                await panel.locator('[data-nav="dashboard"]').click()
                assert await panel.locator('#dashboard-pipeline .profile-card').count()==2
                assert await panel.locator('#dashboard-pipeline .profile-card').first.locator('.pipe-card').count()==2
                assert await panel.locator('#dashboard-pipeline .profile-card').last.locator('.pipe-card').count()==1
                await capture(page,panel,'ui-profiles-017.png')
                print('PASS: Two large dashboard group cards with correct nested consumer tiles',flush=True)

                await panel.locator('#activate').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'running'")
                await asyncio.sleep(.3)
                assert bridge.commands==[]  # High-priority 1800 W load cannot fit.
                assert bridge.controller.status()['next_id']=='a'
                print('PASS: Group 2 cannot overtake unaffordable group 1',flush=True)
                bridge.base=4000
                for _ in range(100):
                    if len(bridge.commands)>=3: break
                    await asyncio.sleep(.1)
                assert bridge.commands[:3]==[('switch.test_1','on'),('switch.test_2','on'),('switch.test_3','on')],bridge.commands
                print('PASS: Single scheduler starts both groups in configured priority and Classic member order',flush=True)

                # Turning a running profile off removes its owned loads but
                # keeps other groups operating. Deactivation overrides timers.
                await panel.locator('[data-nav="profiles"]').click()
                summer=panel.locator('#profiles-list .profile-card').filter(has_text='Sommer')
                await summer.locator('button[title="Profilstatus ändern"]').click()
                for _ in range(70):
                    if ('switch.test_3','off') in bridge.commands: break
                    await asyncio.sleep(.1)
                assert ('switch.test_3','off') in bridge.commands,bridge.commands
                assert bridge.values['switch.test_1']=='on' and bridge.values['switch.test_2']=='on'
                assert bridge.controller.mode=='running'
                assert not bridge.controller.config.profiles[1].enabled
                print('PASS: Disable one active profile: only its owned consumer switches off; others stay on',flush=True)
                await summer.locator('button[title="Profilstatus ändern"]').click()
                for _ in range(70):
                    if bridge.commands[-1:]==[('switch.test_3','on')]: break
                    await asyncio.sleep(.1)
                assert bridge.commands[-1]==('switch.test_3','on'),bridge.commands
                assert bridge.controller.config.profiles[1].enabled
                print('PASS: Re-enable profile during operation; its Classic allocation resumes automatically',flush=True)

                await page.set_viewport_size({'width':390,'height':844})
                assert await panel.locator('main').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
                await panel.locator('#profiles-list .profile-card').first.locator('button[title="Profilstatus ändern"]').wait_for(state='visible')
                await capture(page,panel,'ui-profiles-mobile-017.png')
                print('PASS: Two profile cards fit a smartphone without horizontal overflow',flush=True)
                await panel.locator('#page-choice').select_option('dashboard')
                await panel.locator('#main-off').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'stopped'")
                assert all(v=='off' for v in bridge.values.values())
                assert not errors,errors
                print('PASS: Main OFF still shuts down all test switches; no browser exceptions',flush=True)
                await browser.close()
        finally:
            reporter.cancel()
            with suppress(asyncio.CancelledError): await reporter
            await bridge.controller.close()

if __name__=='__main__': asyncio.run(main())
