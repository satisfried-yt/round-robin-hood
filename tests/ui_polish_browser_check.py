"""v0.2.1: compact, accessible UI help and live condition diagnostics in Chromium."""
import asyncio
from contextlib import suppress
import shutil
import tempfile

from playwright.async_api import async_playwright

from browser_check import Bridge, capture
import load_core


async def main():
    with tempfile.TemporaryDirectory() as temp:
        bridge = Bridge(temp)
        config = bridge.controller.config.to_dict()
        config['grid_entity'] = 'sensor.test_grid'
        config['consumers'] = [
            {'id': 'a', 'name': 'Heizung', 'entity_id': 'switch.test_1', 'watts': 300,
             'enabled': True, 'virtual_confirmed': True,
             'conditions': {'enabled': True, 'logic': 'all', 'rules': [
                 {'id': 'a-rule', 'entity_id': 'sensor.room_temp', 'operator': '<',
                  'value': 21, 'hysteresis': 1}]}}
        ]
        config['profiles'] = [{
            'id': 'standard', 'name': 'Standard', 'enabled': True,
            'strategy': 'classic', 'dashboard_order': 'fixed', 'consumer_ids': ['a']
        }]
        config['profiles'][0]['conditions'] = {
            'enabled': True, 'logic': 'all', 'rules': [
                {'id': 'p-rule', 'entity_id': 'sensor.room_temp', 'operator': '<',
                 'value': 25, 'hysteresis': 0},
                {'id': 'p-second', 'entity_id': 'sensor.missing', 'operator': '>',
                 'value': 10, 'hysteresis': 0}
            ]
        }
        await bridge.controller.configure(config, bridge.controller.revision)
        bridge.controller.seed_switch('switch.test_1', 'off')
        bridge.controller.observe_condition('sensor.room_temp', '20')
        bridge.controller.observe_condition('sensor.missing', 'unavailable')
        reports = asyncio.create_task(bridge.reports())
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(executable_path=shutil.which('chromium'),
                                                   headless=True, args=['--no-sandbox'])
                page = await browser.new_page(viewport={'width': 1360, 'height': 980})
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                await page.expose_function('rrhTestWS', bridge.api)
                await page.set_content(bridge.page_html())
                await page.add_script_tag(path=str(load_core.COMPONENT / 'frontend/panel.js'))
                panel = page.locator('rrh-hood-panel')
                await page.wait_for_function("document.querySelector('#panel')._data?.consumers.length === 1")

                # A mouseover tells what the control does without adding a permanent paragraph.
                actions = panel.locator('.operation-action')
                assert await actions.count() == 3
                for label, expected in [('activate', 'Automatik ein'), ('main-off', 'alle konfigurierten'),
                                        ('pause', 'Laufende Verbraucher')]:
                    tooltip = await panel.locator(f'#{label}').get_attribute('title')
                    assert expected.lower() in tooltip.lower(), (label, tooltip)
                await actions.nth(1).locator('.info-button').hover()
                assert await actions.nth(1).locator('.info-popover').is_visible()
                assert 'Kein zertifizierter Not-Aus' in await actions.nth(1).locator('.info-popover').inner_text()
                print('PASS: operation buttons explain behavior on hover, including safety limitation', flush=True)

                # Preserve live measurements and shorten repeated explanatory copy.
                assert await panel.locator('#available').inner_text() != '—'
                assert await panel.locator('.operation-help').count() == 0
                assert await panel.locator('footer.card').count() == 0
                assert await panel.locator('#pipeline-title .info-wrap').count() == 1
                print('PASS: live values remain; static dashboard text is replaced with help', flush=True)

                # Report failed/missing sensors compactly, but keep exact entity IDs in opened details.
                dashboard = panel.locator('#dashboard-pipeline')
                summary = dashboard.locator('.profile-card > .profile-heading .condition-status summary')
                assert '1/2 erfüllt' in await summary.inner_text()
                assert 'Sensor fehlt' in await summary.inner_text()
                await summary.click()
                profile_detail = dashboard.locator('.profile-heading .condition-status')
                assert 'sensor.missing' in await profile_detail.locator('.condition-details').inner_text()
                bridge.controller.observe_condition('sensor.room_temp', '26')
                await page.wait_for_function("document.querySelector('#panel')._data?.profiles[0].condition_checks[0].passed === false")
                await page.wait_for_function("document.querySelector('#panel').shadowRoot.querySelector('#dashboard-pipeline .profile-heading .condition-status summary').textContent.includes('0/2')")
                assert await profile_detail.get_attribute('open') is not None
                print('PASS: compact failure count and invalid sensor remain readable; open details survive redraw', flush=True)

                await panel.locator('[data-nav="consumers"]').click()
                consumer = panel.locator('#consumers .consumer')
                assert await consumer.locator('.condition-status').count() == 2
                assert '0/2' in await consumer.locator('.condition-status').first.locator('summary').inner_text()
                assert not await consumer.get_by_text('Profilbedingung gesperrt:', exact=False).count()
                await consumer.locator('.condition-status').last.locator('summary').click()
                assert 'sensor.room_temp' in await consumer.locator('.condition-status').last.locator('.condition-details').inner_text()
                print('PASS: profile and consumer rules distinguishable without repeated long reasons', flush=True)

                # Forms: explanatory paragraphs become help without affecting the fields.
                await consumer.get_by_role('button', name='Bearbeiten: Heizung').click()
                assert await panel.locator('#editor .help').count() == 0
                assert await panel.locator('#editor .info-button').count() >= 5
                assert await panel.locator('#consumer-watts').input_value() == '300'
                await panel.locator('#override-delay').check()
                assert await panel.locator('#consumer-delay').is_visible()
                await panel.locator('#override-delay').uncheck()
                assert not await panel.locator('#consumer-delay').is_visible()
                await panel.locator('#cancel-editor').click()
                await panel.locator('[data-nav="settings"]').click()
                await panel.locator('#source-settings summary').click()
                assert await panel.locator('#settings-form .help').count() == 0
                assert await panel.locator('#grid-entity').input_value() == 'sensor.test_grid'
                await panel.locator('[data-nav="profiles"]').click()
                await panel.locator('#profiles-list .profile-controls button[title="Profil bearbeiten"]').click()
                assert await panel.locator('#profile-editor .help').count() == 0
                assert await panel.locator('#profile-conditions-list .condition-row').count() == 2
                await panel.locator('#cancel-profile').click()
                print('PASS: editor and settings hints are compact while fields retain their behavior', flush=True)

                await panel.locator('[data-nav="dashboard"]').click()
                await panel.locator('#main-off').click()
                await page.wait_for_function("document.querySelector('#panel')._data?.mode === 'stopped'")
                assert (await panel.locator('#reason').inner_text()).strip() == 'Betrieb gestoppt'
                assert await panel.locator('#last-action').inner_text() == ''
                print('PASS: stopped operation uses a single status line, without duplicate history', flush=True)

                # Mobile displays all three controls in one compact row, and touch help is actionable.
                await page.set_viewport_size({'width': 375, 'height': 820})
                rects = await actions.evaluate_all('''els => els.map(el => {
                  const r=el.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,right:r.right};})''')
                assert max(r['y'] for r in rects) - min(r['y'] for r in rects) < 5, rects
                assert all(r['right'] <= 375 for r in rects), rects
                await actions.nth(2).locator('.info-button').click()
                assert await actions.nth(2).locator('.info-button').get_attribute('aria-expanded') == 'true'
                assert 'Pausiert die Automatik' in await actions.nth(2).locator('.info-popover').inner_text()
                await panel.locator('#operation-heading').click()
                assert await actions.nth(2).locator('.info-button').get_attribute('aria-expanded') == 'false'
                assert not (await panel.evaluate('(el) => el.scrollWidth > el.clientWidth + 1'))
                await capture(page, panel, 'ui-polish-mobile-021.png')
                print('PASS: mobile operation controls share a row; touch info opens and closes', flush=True)
                assert not errors, errors
                print('PASS: no browser errors', flush=True)
                await browser.close()
        finally:
            reports.cancel()
            with suppress(asyncio.CancelledError):
                await reports
            await bridge.controller.close()


if __name__ == '__main__':
    asyncio.run(main())
