"""Browser acceptance: welcome routes, guide full-text, equal cards and translated donation tooltip."""
from pathlib import Path
import asyncio, shutil, tempfile
from playwright.async_api import async_playwright
import load_core
from browser_check import Bridge
from rrh_tested.demo import DemoSandbox

class OnboardingBridge(Bridge):
    def __init__(self,tmp):
        super().__init__(tmp)
        self.onboarding_bypass=False
        self.demo=None
    def result(self):
        result=super().result()
        if self.demo:
            result.update(self.demo.controller.status())
            result['demo_mode']=True
            result['setup_needed']=False
        return result
    async def api(self,msg):
        if msg.get('action')=='demo_mode':
            if msg.get('demo_enabled'):
                self.demo=DemoSandbox()
                await self.demo.start()
            else:
                await self.demo.close()
                self.demo=None
            return self.result()
        return await super().api(msg)

async def scenario(browser, path, option):
    with tempfile.TemporaryDirectory() as tmp:
        bridge=OnboardingBridge(tmp)
        reports=asyncio.create_task(bridge.reports())
        page=await browser.new_page(viewport={'width':1240,'height':930})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        await page.expose_function('rrhTestWS',bridge.api)
        await page.goto('about:blank')
        await page.set_content(bridge.page_html())
        await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
        panel=page.locator('rrh-hood-panel')
        try:
            await page.wait_for_function("document.querySelector('#panel')._data?.version === '0.9.3'")
            await panel.locator('#safety-dialog[open]').wait_for()
            await panel.locator('#notice-continue').click()
            await panel.locator('#welcome-dialog[open]').wait_for()
            assert await panel.locator('#welcome-dialog .welcome-choice').count()==3
            assert not await panel.locator('#setup-wizard').evaluate('el=>el.open')
            if option=='wizard':
                await panel.locator('#welcome-wizard').click()
                await panel.locator('#setup-wizard[open]').wait_for()
                assert not await panel.locator('#welcome-dialog').evaluate('el=>el.open')
                print('PASS safety notice -> welcome -> setup wizard',flush=True)
            elif option=='skip':
                await panel.locator('#welcome-skip').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.config?.setup_complete === true")
                assert bridge.controller.mode!='running'
                assert bridge.controller.config.grid_entity==''
                assert not bridge.commands
                assert not await panel.locator('#welcome-dialog').evaluate('el=>el.open')
                print('PASS skip setup saves onboarding decision without any real HA commands',flush=True)
            elif option=='demo':
                await panel.locator('#welcome-demo').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.demo_mode === true")
                assert bridge.demo is not None
                assert len(bridge.demo.controller.config.consumers)==6
                assert not bridge.controller.config.consumers
                assert not bridge.commands
                print('PASS welcome starts isolated demo with six simulated consumers',flush=True)
            if option=='skip':
                # first-row equal height including expanded startup card
                await panel.locator('[data-nav="settings"]').click()
                heights=await panel.locator('#settings-form .settings-grid > details').evaluate_all('els=>els.slice(0,3).map(el=>el.getBoundingClientRect().height)')
                assert max(heights)-min(heights)<2,heights
                print('PASS settings cards in the same row have equal height',flush=True)
                await panel.locator('[data-nav="dashboard"]').click()
                assert await panel.locator('#donation-link').text_content()=='Gib einen Drink aus'
                assert 'Rum-Cola' in await panel.locator('#donation-link').get_attribute('title')
                assert 'Rum-Cola' in await panel.locator('#donation-info .info-popover').text_content()
                for lang in ('de','en','fr','es','pt','it'):
                    title,tip=await panel.evaluate('''(el,lang)=>{
                     el._language=lang;el._translateStatic();
                     return [el.shadowRoot.querySelector('#welcome-wizard strong').textContent,
                             el.shadowRoot.querySelector('#donation-info .info-popover').textContent];
                    }''',lang)
                    assert len(title)>5 and len(tip)>20,(lang,title,tip)
                print('PASS donation tooltip with tap target and six language variations',flush=True)
            assert not errors,errors
        finally:
            if bridge.demo:await bridge.demo.close()
            await page.close()
            reports.cancel()
            try:await reports
            except asyncio.CancelledError:pass

async def docs_search(browser):
    for lang in ('de','en'):
        p=await browser.new_page()
        errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        base=load_core.COMPONENT/'frontend/guides'/lang
        html=(base/'index.html').read_text()
        idx=(base/'search-index.js').read_text()
        html=html.replace('<script src="search-index.js"></script>', '<script>'+idx+'</script>')
        await p.goto('about:blank')
        await p.set_content(html)
        await p.wait_for_function('window.RRH_GUIDE_SEARCH_INDEX?.length===16')
        assert await p.locator('#nav a').count()==16
        await p.locator('#filter').fill('nonexistent-random-placeholder-82726')
        assert await p.locator('#nav a:visible').count()==0
        assert '0' in await p.locator('#search-status').text_content()
        await p.locator('#filter').fill('Hysterese' if lang=='de' else 'hysteresis')
        n=await p.locator('#nav a:visible').count()
        assert 1<=n<16,(lang,n)
        await p.locator('#filter').fill('')
        assert await p.locator('#nav a:visible').count()==16
        assert not errors, errors
        print(f'PASS {lang} full-text guide filters 16 chapters including body text',flush=True)
        await p.close()

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
        try:
            for opt in ('wizard','skip','demo'):
                await scenario(browser,load_core.COMPONENT,opt)
            await docs_search(browser)
        finally:await browser.close()

if __name__=='__main__':asyncio.run(main())
