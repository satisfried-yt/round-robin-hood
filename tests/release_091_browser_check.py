"""Browser check for startup controls, source filtering, six locale labels, offline guide link."""
import asyncio, shutil, tempfile
from playwright.async_api import async_playwright
import load_core
from browser_check import Bridge

async def main():
    with tempfile.TemporaryDirectory() as tmp:
        bridge=Bridge(tmp)
        bridge.states.update({
            'sensor.price_eur':{'state':'0.30','attributes':{'friendly_name':'Day-ahead price','unit_of_measurement':'EUR/kWh'}},
            'sensor.price_chf':{'state':'0.26','attributes':{'friendly_name':'CHF price','unit_of_measurement':'CHF/kWh'}},
            'sensor.temperature':{'state':'25','attributes':{'friendly_name':'Temperature','unit_of_measurement':'°C'}},
            'sensor.pv_capacity':{'state':'4000','attributes':{'friendly_name':'Nominal PV','unit_of_measurement':'W'}},
            'sensor.no_unit':{'state':'0.28','attributes':{'friendly_name':'Unlabelled number'}},
            'sensor.bad_timestamp':{'state':'2026-11-18T01:00:00+01:00','attributes':{'friendly_name':'Date'}},
            'sensor.unavailable_price':{'state':'unavailable','attributes':{'friendly_name':'Offline price','unit_of_measurement':'EUR/kWh'}},
        })
        ticker=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1120,'height':900})
                page.on('pageerror',lambda err:errors.append(str(err)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.goto('about:blank')
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.version==='0.9.3'")
                await panel.locator('[data-nav="settings"]').click()
                assert await panel.locator('#startup-mode').input_value()=='off'
                await panel.locator('#source-settings > summary').click()
                await panel.locator('#grid-entity').select_option('sensor.test_grid')
                await panel.locator('#startup-mode').select_option('last')
                await panel.locator('#save-settings').click()
                await page.wait_for_timeout(1500)
                print('SAVE DEBUG',await panel.evaluate('el=>[el._data?.config?.startup_mode,el.shadowRoot.querySelector("#command-error")?.textContent,el.shadowRoot.querySelector("#settings-error")?.textContent]'),flush=True)
                await page.wait_for_function("document.querySelector('#panel')._data?.config?.startup_mode==='last'",timeout=10000)
                print('PASS restart behavior persists through the settings form',flush=True)
                await page.evaluate("document.querySelector('#panel')._setPage('energy')")
                await panel.locator('#stat-import-mode').select_option('entity')
                options=await panel.locator('#stat-import-entity option').evaluate_all('els=>els.map(x=>x.value)')
                assert 'sensor.price_eur' in options, options
                assert 'sensor.temperature' not in options
                assert 'sensor.no_unit' not in options
                assert 'sensor.pv_capacity' not in options
                assert 'sensor.unavailable_price' not in options
                assert 'sensor.price_chf' not in options
                pv=await panel.locator('#stat-pv-entity option').evaluate_all('els=>els.map(x=>x.value)')
                assert 'sensor.pv_capacity' in pv and 'sensor.price_eur' not in pv, pv
                print('PASS currency-aware price and nominal PV source filtering',flush=True)
                await panel.locator('#stat-currency').select_option('CHF')
                options=await panel.locator('#stat-import-entity option').evaluate_all('els=>els.map(x=>x.value)')
                assert 'sensor.price_chf' in options and 'sensor.price_eur' not in options,options
                print('PASS changing currency refreshes selectable compatible sensors',flush=True)
                for lang in ('de','en','fr','es','pt','it'):
                    values=await panel.evaluate('''(el,lang)=>{el._language=lang;el._translateStatic();
                      return [el.shadowRoot.querySelector('#startup-mode option[value="on"]').textContent,
                      el.shadowRoot.querySelector('#startup-settings strong').textContent]}''',lang)
                    assert len(values[0])>5 and len(values[1])>5,(lang,values)
                print('PASS new restart labels are present across all six UI languages',flush=True)
                await page.evaluate("document.querySelector('#panel')._setPage('howto')")
                assert await panel.locator('#guide-frame').count()==1
                assert 'guide/it/index.html' in await panel.locator('#guide-frame').get_attribute('src')
                print('PASS Anleitung links to the bundled offline chapter navigator',flush=True)
                assert not errors, errors
                await browser.close()
        finally:
            ticker.cancel()
            try: await ticker
            except asyncio.CancelledError: pass

if __name__=='__main__':asyncio.run(main())
