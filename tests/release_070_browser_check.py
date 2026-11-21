"""v0.7 onboarding & setup, safety, responsive grids and 24h history (Chromium)."""
import asyncio
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        bridge.onboarding_bypass=False
        reporter=asyncio.create_task(bridge.reports())
        errors=[]
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1200,'height':900})
                page.on('pageerror',lambda e:errors.append(str(e)))
                await page.expose_function('rrhTestWS',bridge.api)
                async def start():
                    await page.goto('about:blank')
                    await page.set_content(bridge.page_html())
                    await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                    await page.wait_for_function('document.querySelector("#panel")._data?.version === "0.9.3"')
                    return page.locator('rrh-hood-panel')
                panel=await start()
                await panel.locator('#safety-dialog').wait_for(state='visible')
                assert not await panel.locator('#dismiss-notice').is_checked()
                assert await panel.locator('#setup-wizard').is_hidden()
                print('PASS: notice appears before the wizard on empty first install',flush=True)
                await panel.locator('#notice-continue').click()
                await panel.locator('#welcome-dialog').wait_for(state='visible')
                await panel.locator('#welcome-wizard').click()
                await panel.locator('#setup-wizard').wait_for(state='visible')
                assert bridge.controller.config.notice_dismissed is False
                await panel.locator('#wizard-close').click()
                panel=await start()
                await panel.locator('#safety-dialog').wait_for(state='visible')
                print('PASS: without remember checkbox the notice reappears after reload',flush=True)
                await panel.locator('#dismiss-notice').check()
                await panel.locator('#notice-continue').click()
                await panel.locator('#welcome-dialog').wait_for(state='visible')
                await panel.locator('#welcome-wizard').click()
                await panel.locator('#setup-wizard').wait_for(state='visible')
                assert bridge.controller.config.notice_dismissed is True
                print('PASS: notice acknowledgment persisted to actual controller state',flush=True)
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-grid').select_option('sensor.test_grid')
                await panel.locator('#wizard-next').click()
                await panel.locator('.wizard-entity').first.select_option('switch.test_1')
                await panel.locator('.wizard-name').first.fill('Gartenheizer')
                await panel.locator('.wizard-watts').first.fill('1000')
                await panel.get_by_role('button',name='+ Weiteren Verbraucher hinzufügen').click()
                await panel.locator('.wizard-entity').nth(1).select_option('switch.test_2')
                await panel.locator('.wizard-name').nth(1).fill('Poolpumpe')
                await panel.locator('.wizard-watts').nth(1).fill('500')
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-strategy').select_option('maximum_efficiency')
                assert 'Optimierungs' in await panel.locator('#wizard-strategy-help').inner_text() or 'Leistung' in await panel.locator('#wizard-strategy-help').inner_text()
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-pv').fill('4000')
                await panel.locator('#wizard-buy').fill('0.30')
                await panel.locator('#wizard-feed').fill('0.08')
                await panel.locator('#wizard-next').click()
                await panel.locator('#wizard-reserve').fill('150')
                await panel.locator('#wizard-delay').fill('25')
                await panel.locator('#wizard-age').fill('45')
                await panel.locator('#wizard-next').click()
                assert 'Poolpumpe' in await panel.locator('#wizard-content').inner_text()
                await panel.locator('#wizard-next').click()
                await panel.locator('#setup-wizard').wait_for(state='hidden')
                assert bridge.controller.config.setup_complete
                assert bridge.controller.mode=='paused'
                assert bridge.controller.config.grid_entity=='sensor.test_grid'
                assert bridge.controller.config.reserve_w==150
                assert len(bridge.controller.config.consumers)==2
                assert bridge.controller.config.energy.pv_size.value==4.0
                assert bridge.controller.config.profiles[0].strategy=='maximum_efficiency'
                assert bridge.commands==[]
                print('PASS: 7-step wizard stores grid, 2 switches, strategy, watts-to-kWp, tariffs and limits atomically, leaves all OFF',flush=True)
                await panel.locator('[data-nav="consumers"]').click()
                columns=await panel.locator('.consumer').evaluate_all('els=>els.map(e=>({w:e.offsetWidth,x:e.offsetLeft,y:e.offsetTop}))')
                assert len(columns)==2 and columns[0]['w']==columns[1]['w'] and columns[0]['y']==columns[1]['y']
                await panel.locator('[data-nav="settings"]').click()
                assert await panel.locator('#demo-toggle').is_visible()
                assert await panel.locator('#show-notice').is_visible()
                assert await panel.locator('#show-wizard').is_visible()
                await panel.locator('#show-wizard').click()
                await panel.locator('#setup-wizard').wait_for(state='visible')
                await panel.locator('#wizard-cancel').click()
                assert len(bridge.controller.config.consumers)==2
                assert bridge.controller.config.setup_complete
                print('PASS: manual wizard restart/cancel never modifies an existing configuration',flush=True)
                await panel.locator('[data-nav="energy"]').click()
                if not await panel.locator("#energy-settings").evaluate("el=>el.open"):
                    await panel.locator("#energy-settings summary").click()
                assert await panel.locator('#stat-pv-fixed').input_value()=='4000'
                assert await panel.locator('#stat-currency').input_value()=='EUR'
                assert await panel.locator('#energy-chart svg').count()==1
                assert '24 Stunden' in await panel.locator('#energy-chart').text_content()
                print('PASS: single energy editor on energy page, W display and documented 24h chart',flush=True)
                await panel.locator('#stat-currency').select_option('CHF')
                await panel.locator('#save-energy').click()
                assert 'Beide Tarife' in await panel.locator('#energy-save-error').inner_text()
                assert bridge.controller.config.energy.currency=='EUR'
                await panel.locator('#stat-import-fixed').fill('0.42')
                await panel.locator('#stat-feed-fixed').fill('0.12')
                await panel.locator('#save-energy').click()
                await page.wait_for_function('document.querySelector("#panel")._data?.config?.energy?.currency === "CHF"')
                assert bridge.controller.config.energy.import_price.value==.42
                assert bridge.controller.config.energy.feed_in_price.value==.12
                assert 'CHF/kWh' in await panel.locator('#import-price-label').inner_text()
                print('PASS: currency switch requires both tariffs re-entered, then stores CHF values with explicit acknowledgment',flush=True)
                lines=await panel.evaluate("""el=>{
                  const t=Date.now()/1000;
                  const point=(offset,active=true)=>[t-offset,500,300,60,800,active];
                  el._drawHistory24h(el.$('#energy-chart'),{history:[point(650),point(620),point(320),point(290),point(260,false),point(120),point(90)]});
                  return el.$('#energy-chart').querySelectorAll('polyline').length;
                }""")
                assert lines==3,lines
                print('PASS: 24h visual timeline breaks the line at missing time spans and unavailable readings',flush=True)


                await panel.locator('[data-nav="dashboard"]').click()
                size=await panel.locator('#live-chart-card').evaluate('(el)=>({x:el.offsetLeft,w:el.offsetWidth,p:el.parentElement.offsetWidth})')
                assert size['w'] > size['p']*.95, size
                await panel.locator('[data-nav="about"]').click()
                assert '0.9.3' in await panel.locator('#page-about').inner_text()
                await panel.locator('[data-nav="howto"]').click()
                assert '/round_robin_hood/guide/de/index.html' in (await panel.locator('#guide-frame').get_attribute('src'))
                print('PASS: full-width dashboard chart and How-to/About pages',flush=True)
                await page.set_viewport_size({'width':390,'height':844})
                await panel.locator('#page-choice').select_option('consumers')
                assert await panel.locator('#consumers').evaluate('(el)=>el.scrollWidth<=el.clientWidth+1')
                await panel.locator('#page-choice').select_option('dashboard')
                assert await panel.locator('#live-chart-card svg').count()==1
                assert await panel.locator('main').evaluate('el=>el.scrollWidth<=el.clientWidth+1')
                print('PASS: narrow mobile browser no clipped panel; all controls responsive',flush=True)
                assert not errors,errors
                await browser.close()
        finally:
            reporter.cancel()
            try: await reporter
            except asyncio.CancelledError: pass

if __name__=='__main__':asyncio.run(main())
