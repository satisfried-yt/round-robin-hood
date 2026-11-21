"""v0.2.0 actual HA adapter with explicit event/service/store test doubles."""
import unittest
from test_adapter import AdapterTests
from test_core import config
from test_conditions_020 import rules


class ConditionAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await AdapterTests.asyncSetUp(self)

    async def asyncTearDown(self):
        await AdapterTests.asyncTearDown(self)

    async def request(self, action, **fields):
        return await AdapterTests.request(self,action,**fields)

    async def _set_config(self, member_ids):
        cfg=config()
        cfg['profiles']=[{'id':'winter','name':'Winter','enabled':True,'strategy':'classic',
                          'consumer_ids':member_ids,'dashboard_order':'fixed',
                          'conditions':rules(('sensor.room','<',21,1))}]
        self.hass.states.set('sensor.room','unavailable',{'unit_of_measurement':'C'})
        await self.rt.configure(cfg,self.rt.controller.revision)
        await self.hass.drain()

    async def test_live_sensor_event_releases_and_then_shuts_down_single_consumer(self):
        await self._set_config(['a'])
        await self.request('activate')
        self.hass.states.set('sensor.grid','2500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.assertEqual(self.hass.services.calls,[])
        self.assertIn('sensor.room',self.rt.controller.status()['profiles'][0]['conditions_reason'])
        self.hass.states.set('sensor.room','19.5',{'unit_of_measurement':'C'})
        self.hass.states.set('sensor.grid','2500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.assertEqual([c[1] for c in self.hass.services.calls],['turn_on'])
        self.hass.states.set('sensor.room','unknown',{'unit_of_measurement':'C'})
        await self.hass.drain()
        self.assertEqual([c[1] for c in self.hass.services.calls],['turn_on','turn_off'])
        self.assertEqual(self.rt.controller.mode,'running')
        self.assertFalse(self.rt.controller.status()['profiles'][0]['conditions_allowed'])

    async def test_live_profile_invalidates_both_members_in_one_bulk_service(self):
        await self._set_config(['a','b'])
        self.hass.states.set('sensor.room','18',{'unit_of_measurement':'C'})
        await self.request('activate')
        self.hass.states.set('sensor.grid','2500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.hass.states.set('sensor.grid','1500',{'unit_of_measurement':'W'})
        await self.hass.drain()
        self.assertEqual(self.rt.controller.owned,['a','b'])
        self.hass.states.set('sensor.room','unavailable',{'unit_of_measurement':'C'})
        await self.hass.drain()
        off=[c for c in self.hass.services.calls if c[1]=='turn_off']
        self.assertEqual(len(off),1,off)
        self.assertEqual(off[0][2]['entity_id'],['switch.a','switch.b'])
        self.assertEqual(self.rt.controller.owned,[])
        self.assertEqual(self.rt.controller.mode,'running')

    async def test_unload_removes_condition_sensor_event_listener(self):
        await self._set_config(['a'])
        self.assertTrue(any('sensor.room' in ids for kind,ids,callback in self.hass.listeners if kind=='change'))
        await self.boot.async_unload_entry(self.hass,self.entry)
        self.assertEqual(self.hass.listeners,[])
        self.rt=self.entry.runtime_data


if __name__=='__main__': unittest.main()
