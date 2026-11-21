"""v0.9.1 guided-setup and compact dashboard regression using production UI and simulated HA transport."""
import asyncio
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        bridge=Bridge(tmp)
        bridge.states.update({
            'sensor.tariff_now':{'state':'0.32','attributes':{'friendly_name':'Tariff live','unit_of_measurement':'EUR/kWh'}},
            'sensor.feed_now':{'state':'0.08','attributes':{'friendly_name':'Export tariff','unit_of_measurement':'EUR/kWh'}},
            'sensor.pv_capacity':{'state':'4500','attributes':{'friendly_name':'Installed PV','unit_of_measurement':'W'}},
        })
        reporting=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1100,'height':900})
                page.on('pageerror',lambda err: errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.goto('about:blank')
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.version==='0.9.3'")
                assert await panel.locator('#stat-grid-energy-entity').count()==0
                assert await panel.locator('#rrh-live-chart svg rect').count()>=3
                height=await panel.locator('#rrh-live-chart svg').evaluate('el=>el.getBoundingClientRect().height')
                assert height<=92,height
                print('PASS compact horizontal efficiency indicator and removed redundant export-meter input',flush=True)
                await page.evaluate("document.querySelector('#panel')._openWizard(true)")
                assert await panel.locator('#setup-wizard').is_visible()
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-grid').select_option('sensor.test_grid')
                await panel.locator('#wizard-next').click()
                assert 'Verbraucher' in await panel.locator('#wizard-content').inner_text()
                await panel.locator('.wizard-entity').select_option('switch.test_1')
                await panel.locator('.wizard-name').fill('Waschmaschine')
                await panel.locator('.wizard-watts').fill('500')
                await panel.locator('#wizard-next').click()
                assert 'Anleitung' in await panel.locator('#wizard-content').inner_text()
                await panel.locator('#wizard-next').click()
                print('WIZARD STEP',await panel.evaluate('el=>[el._wizardStep,el.shadowRoot.querySelector("#wizard-error")?.textContent,el.shadowRoot.querySelector("#wizard-content")?.textContent.slice(0,240)]'),flush=True)
                print('errors',errors,flush=True)
                print('RENDER',await panel.evaluate('el=>{try{el._wizardRender();return [true,el.shadowRoot.querySelectorAll("#wizard-content .wizard-source").length]}catch(e){return [false,e.message,e.stack]}}'),flush=True)
                for key,id in [('pv','sensor.pv_capacity'),('buy','sensor.tariff_now'),('feed','sensor.feed_now')]:
                    await panel.locator(f'#wizard-{key}-mode').select_option('entity')
                    await panel.locator(f'#wizard-{key}-entity').select_option(id)
                assert await panel.locator('#wizard-buy').is_hidden()
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-next').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config?.setup_complete === true",timeout=10000)
                cfg=bridge.controller.config
                assert cfg.consumers[0].name=='Waschmaschine'
                assert cfg.energy.pv_size.entity_id=='sensor.pv_capacity'
                assert cfg.energy.import_price.entity_id=='sensor.tariff_now'
                assert cfg.energy.feed_in_price.entity_id=='sensor.feed_now'
                assert cfg.energy.grid_export_energy_entity==''
                print('PASS wizard custom consumer name and three HA entity sources saved safely',flush=True)
                assert not errors,errors
                await browser.close()
        finally:
            reporting.cancel()
            try:await reporting
            except asyncio.CancelledError:pass

if __name__=='__main__':asyncio.run(main())
