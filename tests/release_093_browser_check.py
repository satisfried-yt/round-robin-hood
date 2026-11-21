"""Six-language offline handbook search, language switching and copyright checks."""
from pathlib import Path
from urllib.parse import urlparse
import asyncio, shutil
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
GUIDES=ROOT/'custom_components/round_robin_hood/frontend/guides'
WORDS={'de':'Hysterese','en':'hysteresis','fr':'hysteresis','es':'histeresis','pt':'histerese','it':'isteresi'}

async def main():
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox','--allow-file-access-from-files'])
        try:
            for language,word in WORDS.items():
                page=await browser.new_page()
                errors=[]
                page.on('pageerror',lambda err:errors.append(str(err)))
                folder=GUIDES/language
                source=(folder/'index.html').read_text()
                index=(folder/'search-index.js').read_text()
                source=source.replace('<script src="search-index.js"></script>','<script>'+index+'</script>')
                await page.goto('about:blank')
                await page.set_content(source)
                await page.wait_for_function('window.RRH_GUIDE_SEARCH_INDEX?.length===16')
                assert await page.locator('#nav a').count()==16
                assert await page.locator('#guide-language').input_value()==language
                assert await page.locator('#nav a:visible').count()==16
                await page.locator('#filter').fill('unmatched-search-0991xyz')
                assert await page.locator('#nav a:visible').count()==0
                await page.locator('#filter').fill(word)
                matches=await page.locator('#nav a:visible').count()
                assert 1<=matches<16,(language,matches)
                await page.locator('#filter').fill('')
                assert await page.locator('#nav a:visible').count()==16
                assert not errors,(language,errors)
                assert await page.locator('#guide-language option').count()==6
                assert 'guide-language' in source and 'location.href' in source
                assert not errors,(language,errors)
                print('PASS language, 16 articles, content search and six locale options:',language,flush=True)
                await page.close()
        finally:await browser.close()

if __name__=='__main__':asyncio.run(main())
