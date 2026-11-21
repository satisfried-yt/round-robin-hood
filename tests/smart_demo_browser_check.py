"""v0.5.0 interactive panel, smart load editors, residual selection and isolated demo."""
import asyncio
from contextlib import suppress
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core
from rrh_tested.demo import DemoSandbox
from rrh_tested.model import UserError


class Bridge050(Bridge):
    def __init__(self, path):
        super().__init__(path)
        self.demo = None
        self.states.update({
            'number.heater':{'state':'0','attributes':{'friendly_name':'Heizstab Leistung','unit_of_measurement':'W','min':0,'max':3000,'step':50}},
            'select.stage':{'state':'off','attributes':{'friendly_name':'Stufenschalter','options':['off','1','2','3']}},
            'climate.heater':{'state':'off','attributes':{'friendly_name':'Brandson','fan_modes':['1','2','3','4'],'hvac_modes':['off','heat']}},
        })

    def result(self):
        c = self.demo.controller if self.demo else self.controller
        return {**c.status(), 'demo_mode':self.demo is not None,
                'demo_power_w':self.demo.generator_w if self.demo else None,
                'notice_dismissed': bool(self.onboarding_bypass or self.controller.config.notice_dismissed),
                'setup_complete':self.controller.config.setup_complete,'setup_needed':False}

    async def api(self, msg):
        if msg['type'].endswith('/status'):
            return self.result()
        action = msg['action']
        if action == 'demo_mode':
            if msg['demo_enabled']:
                if self.demo or self.controller.mode == 'running':
                    raise UserError('Echte Automatik muss gestoppt sein.')
                self.demo=DemoSandbox()
                await self.demo.start()
            else:
                await self.demo.close()
                self.demo=None
            return self.result()
        if action == 'demo_power':
            self.demo.set_power(msg['demo_power_w'])
            await self.demo.controller.settle()
            return self.result()
        if not self.demo:
            await super().api(msg)
            return self.result()
        c=self.demo.controller
        if action == 'activate': await c.activate()
        elif action == 'pause': c.pause()
        elif action == 'emergency_off': await c.emergency_off()
        elif action == 'configure':
            await c.configure(msg['config'],msg['revision']);self.demo.sample()
        elif action == 'participation': await c.participation(msg['consumer_id'],msg['enabled'],msg['revision'])
        elif action == 'profile_participation': await c.profile_participation(msg['profile_id'],msg['enabled'],msg['revision'])
        elif action == 'reset_fair': await c.reset_fair(msg['profile_id'],msg['metric'],msg['revision'])
        elif action == 'skip_timer': await c.skip_timer(msg['consumer_id'],msg['timer'],msg['revision'])
        else: raise UserError('Unknown demo action')
        await c.settle()
        return self.result()


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge050(temp)
        task=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,
                                                 args=['--no-sandbox','--disable-dev-shm-usage'])
                page=await browser.new_page(viewport={'width':1200,'height':980})
                page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('dialog',lambda dialog:asyncio.create_task(dialog.accept()))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function('document.querySelector("#panel")._data?.version === "0.9.3"')
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#source-settings summary').click()
                await panel.locator('#grid-entity').select_option('sensor.test_grid')
                await panel.locator('#save-settings').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config.grid_entity === "sensor.test_grid"')

                await panel.locator('[data-nav="consumers"]').click()
                await panel.locator('#add').click()
                await panel.locator('#consumer-power-mode').select_option('variable')
                await panel.locator('#consumer-name').fill('Heizstab')
                await panel.locator('#consumer-entity').select_option('number.heater')
                await panel.locator('#consumer-watts').fill('200')
                await panel.locator('#consumer-max-watts').fill('3000')
                await panel.locator('#consumer-power-step').fill('50')
                await panel.locator('#save-consumer').click()
                await panel.locator('#editor').wait_for(state='hidden')
                assert bridge.controller.config.consumers[0].power_mode=='variable'
                print('PASS: create stepless HA number consumer and persist power range',flush=True)

                await panel.locator('#add').click()
                await panel.locator('#consumer-power-mode').select_option('staged')
                await panel.locator('#consumer-name').fill('Brandson')
                await panel.locator('#consumer-entity').select_option('climate.heater')
                await panel.locator('#consumer-stage-entity').select_option('climate.heater')
                await panel.locator('#consumer-watts').fill('500')
                await panel.locator('#consumer-stage-lines').fill('500=1\n1000=2\n1500=3\n2000=4')
                await panel.locator('#save-consumer').click()
                await panel.locator('#editor').wait_for(state='hidden')
                assert bridge.controller.config.consumers[1].power_mode=='staged'
                assert len(bridge.controller.config.consumers[1].power_steps)==4
                print('PASS: climate staged consumer with four options persists',flush=True)

                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#residual-settings summary').click()
                await panel.locator('#residual-consumer').select_option(bridge.controller.config.consumers[0].id)
                await panel.locator('#save-settings').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config.residual_consumer_id === document.querySelector("#panel")._data?.config.consumers?.[0]?.id')
                print('PASS: global residual heater setting persisted',flush=True)

                await panel.locator('[data-nav="dashboard"]').click()
                assert await panel.locator('#demo-controls').is_hidden()
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#demo-toggle').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.demo_mode === true')
                await panel.locator('[data-nav="dashboard"]').click()
                assert await panel.locator('#demo-controls').is_visible()
                assert await panel.locator('#demo-power').input_value()=='1600'
                assert len(bridge.demo.controller.config.consumers)==6
                await panel.locator('[data-nav="consumers"]').click()
                visible=await panel.locator('.consumer h3').all_text_contents()
                assert len(visible)==6 and all('Demo-Verbraucher' in name for name in visible),visible
                assert 'Brandson' not in ' '.join(visible)
                print('PASS: demo shows only six virtual devices, hides real profiles and loads',flush=True)

                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator('#demo-power').fill('3100')
                await panel.locator('#demo-power').dispatch_event('change')
                await page.wait_for_function('document.querySelector("#panel")._data?.demo_power_w === 3100')
                await panel.locator('#activate').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.mode === "running"')
                await bridge.demo.controller.settle()
                assert bridge.demo.controller.status()['managed_w']>0
                assert bridge.commands==[]
                print('PASS: demo slider and virtual scheduler operate without actual switch calls',flush=True)
                await panel.locator('#main-off').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.mode === "stopped"')
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#demo-toggle').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.demo_mode === false')
                await panel.locator('[data-nav="consumers"]').click()
                visible=await panel.locator('.consumer h3').all_text_contents()
                assert 'Brandson' in visible and 'Heizstab' in visible and len(visible)==2,visible
                assert bridge.controller.config.residual_consumer_id==bridge.controller.config.consumers[0].id
                assert bridge.commands==[]
                print('PASS: exiting demo restores original consumers and residual setting with zero real commands',flush=True)
                await page.set_viewport_size({'width':390,'height':850})
                await panel.locator('#page-choice').select_option('settings')
                await panel.locator('#demo-toggle').click()
                await panel.locator('#page-choice').select_option('dashboard')
                assert await panel.locator('#demo-controls').is_visible()
                assert await panel.locator('#demo-power').is_visible()
                width=await page.evaluate('document.documentElement.scrollWidth')
                assert width <= 391,(width,errors)
                assert not errors,errors
                print('PASS: demo panel and slider accessible on narrow viewport; no JS errors',flush=True)
                await browser.close()
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):await task
            if bridge.demo: await bridge.demo.close()
            await bridge.controller.close()

if __name__=='__main__':asyncio.run(main())
