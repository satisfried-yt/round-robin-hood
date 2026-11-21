"""Actual shipped frontend in Chromium; HA services and sensor simulated by Bridge."""
import asyncio
from contextlib import suppress
from pathlib import Path
import shutil
import tempfile
from playwright.async_api import async_playwright
from browser_check import Bridge
import load_core

async def main():
    root=load_core.ROOT
    with tempfile.TemporaryDirectory() as temp:
        bridge=Bridge(temp)
        cfg=bridge.controller.config.to_dict()
        cfg['grid_entity']='sensor.test_grid'
        cfg['consumers']=[{'id':str(i),'name':n,'entity_id':f'switch.test_{i}','watts':w,'enabled':True,'virtual_confirmed':True}
            for i,n,w in [(1,'Testheizung',1800),(2,'Testverbraucher',500),(3,'Pooltechnik',800)]]
        await bridge.controller.configure(cfg,bridge.controller.revision)
        for entity in bridge.values: bridge.controller.seed_switch(entity,'off')
        reporting=asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                page=await browser.new_page(viewport={'width':1360,'height':960})
                errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
                await page.expose_function('rrhTestWS',bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT/'frontend/panel.js'))
                panel=page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                await panel.locator('[data-nav="consumers"]').click()
                async def layout():
                    return await panel.locator('.consumer').evaluate_all('''els=>els.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,right:r.right}})''')
                for count in [3,2,1]:
                    if count!=3:
                        cfg=bridge.controller.config.to_dict()
                        cfg['consumers']=cfg['consumers'][:count]
                        cfg['profiles'][0]['consumer_ids']=[c['id'] for c in cfg['consumers']]
                        await bridge.controller.configure(cfg,bridge.controller.revision)
                        await page.wait_for_function(f"document.querySelector('#panel')._data?.consumers.length === {count}")
                    geom=await layout()
                    assert len(geom)==count
                    assert all(abs(g['w']-geom[0]['w'])<1 for g in geom),geom
                    assert geom[0]['w']>350,geom
                    assert len(set(g['y'] for g in geom))==1,geom
                    assert geom==sorted(geom,key=lambda g:g['x']),geom
                    print(f'PASS: {count} desktop cards fill equal-width grid slots in left-to-right order',flush=True)
                    if count==1:
                        await page.screenshot(path=str(root/'test-results/ui-single-consumer-015.png'),full_page=True)
                cfg=bridge.controller.config.to_dict()
                cfg['consumers']=[{'id':str(i),'name':n,'entity_id':f'switch.test_{i}','watts':w,'enabled':True,'virtual_confirmed':True}
                    for i,n,w in [(1,'Testheizung',1800),(2,'Testverbraucher',500),(3,'Pooltechnik',800)]]
                cfg['profiles'][0]['consumer_ids']=[c['id'] for c in cfg['consumers']]
                await bridge.controller.configure(cfg,bridge.controller.revision)
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 3")
                for width,expected in [(320,1),(390,1),(768,2),(1024,3),(1360,3),(1920,3)]:
                    await page.set_viewport_size({'width':width,'height':900})
                    geom=await layout()
                    first_y=geom[0]['y']
                    cols=sum(abs(g['y']-first_y)<1 for g in geom)
                    assert cols==expected,(width,geom)
                    assert all(g['right']<=width+1 for g in geom),(width,geom)
                    assert not await panel.locator('main').evaluate('el=>el.scrollWidth>el.clientWidth+1'),width
                    print(f'PASS: {width}px viewport renders {expected} columns without horizontal overflow',flush=True)
                    if width==390:await page.screenshot(path=str(root/'test-results/ui-mobile-consumers-015.png'),full_page=True)
                    if width==1360:await page.screenshot(path=str(root/'test-results/ui-desktop-consumers-015.png'),full_page=True)
                assert not errors,errors
                print('PASS: no uncaught JS exceptions',flush=True)
                await browser.close()
        finally:
            reporting.cancel()
            with suppress(asyncio.CancelledError):await reporting
            await bridge.controller.close()
if __name__=='__main__': asyncio.run(main())
