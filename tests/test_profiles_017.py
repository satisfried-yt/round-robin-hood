"""Profile 0.1.7: migrations, ownership, independent cursors, priority and delays.

This tests the production pure engine. HA services and timestamps are explicit
fakes, not a live Home Assistant instance.
"""
import asyncio
import base64
from copy import deepcopy
import unittest

from test_core import Rig, config, document
from rrh_tested.model import Config, UserError
from rrh_tested.controller import Controller


def grouped():
    cfg = config()
    cfg["profiles"] = [
        {"id":"heating", "name":"Winter", "enabled":True, "strategy":"classic",
         "consumer_ids":["a","b"], "dashboard_order":"allocation"},
        {"id":"drying", "name":"Sommer", "enabled":True, "strategy":"classic",
         "consumer_ids":["c"], "dashboard_order":"fixed"},
    ]
    return cfg


def stored(cfg=None, cursor=None, owned=None, **extra):
    result = document(cfg or grouped(),cursor=cursor,owned=owned)
    result.update(extra)
    return result


class ProfileValidation(unittest.TestCase):
    def test_016_migration_preserves_consumers_order_and_cursor(self):
        legacy = config()
        legacy.pop("profiles")  # The exact storage shape from v0.1.6.
        async def noop(*args): pass
        r = Controller(stored(legacy,cursor="b"),send=noop,save=noop)
        for consumer in r.config.consumers:
            r.seed_switch(consumer.entity_id,"off")
        self.assertEqual([p.id for p in r.config.profiles],["standard"])
        self.assertEqual(r.config.profiles[0].consumer_ids,("a","b","c"))
        self.assertEqual(r.profile_cursors,{"standard":"b"})
        self.assertEqual(r.status()["next_id"],"c")
        self.assertEqual(r.config.consumers[0].icon,"mdi:power-plug")
        self.assertIsNone(r.config.consumers[0].shutdown_delay_s)
        self.assertTrue(r._generation)

    def test_group_duplicates_invalid_assignments_and_unknown_strategy(self):
        for variant in ("duplicate", "missing", "strategy", "order", "dup_name"):
            cfg=grouped()
            if variant=="duplicate": cfg['profiles'][1]['consumer_ids'].append('b')
            if variant=="missing": cfg['profiles'][0]['consumer_ids'].append('nonexistent')
            if variant=="strategy": cfg['profiles'][0]['strategy']='invalid_strategy'
            if variant=="order": cfg['profiles'][0]['dashboard_order']='random'
            if variant=="dup_name": cfg['profiles'][1]['name']='wInTeR'
            with self.subTest(variant=variant), self.assertRaises(UserError): Config.parse(cfg)

    def test_profile_list_shape_rejected_instead_of_silent_auto_migration(self):
        for invalid in (None, {}, "", 0, False):
            cfg=grouped(); cfg["profiles"]=invalid
            with self.subTest(value=invalid), self.assertRaises(UserError): Config.parse(cfg)

    def test_empty_profile_allowed_and_not_activated_without_members(self):
        cfg=grouped(); cfg['profiles'][1]['consumer_ids']=[]
        parsed=Config.parse(cfg)
        self.assertEqual(parsed.profiles[1].consumer_ids,())
        self.assertEqual(Config.parse(parsed.to_dict()),parsed)

    def test_per_consumer_delay_bounds_and_builtin_icon_validation(self):
        for value in (-1,601,True,"30",float("nan")):
            cfg=grouped(); cfg['consumers'][0]['shutdown_delay_s']=value
            with self.subTest(value=value), self.assertRaises(UserError): Config.parse(cfg)
        for value in ("bad", "mdi:Bad Icon", "http://evil", 2):
            cfg=grouped(); cfg['consumers'][0]['icon']=value
            with self.subTest(value=value), self.assertRaises(UserError): Config.parse(cfg)
        cfg=grouped(); cfg['consumers'][0]['shutdown_delay_s']=0
        self.assertEqual(Config.parse(cfg).consumers[0].shutdown_delay_s,0)

    def test_custom_images_restricted_and_persisted(self):
        png=b"\x89PNG\r\n\x1a\n"+b"valid-for-validation"
        good='data:image/png;base64,'+base64.b64encode(png).decode()
        cfg=grouped(); cfg['consumers'][0]['icon_image']=good
        self.assertEqual(Config.parse(cfg).to_dict()['consumers'][0]['icon_image'],good)
        for bad in ('data:image/svg+xml;base64,'+base64.b64encode(b'<svg/>').decode(),
                    'https://any.domain/image.png','data:image/png;base64,!!!!',
                    'data:image/png;base64,'+base64.b64encode(b'not-png').decode(),
                    'data:image/png;base64,'+base64.b64encode(png+b'a'*50000).decode()):
            cfg['consumers'][0]['icon_image']=bad
            with self.subTest(bad=bad[:40]), self.assertRaises(UserError): Config.parse(cfg)


class ProfileControl(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await asyncio.sleep(0)

    async def test_priority_and_independent_persistent_cursors(self):
        cfg=grouped()
        r=Rig(stored(cfg),power=2500)
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        self.assertEqual(r.c.profile_cursors,{'heating':'a'})
        await r.grid(700)  # next Winter member fits
        self.assertEqual(r.calls[-1],('switch.b','on'))
        await r.grid(700)  # Summer member now next but does not fit
        self.assertEqual(len(r.calls),2)
        self.assertEqual(r.c.status()['next_profile_id'],'drying')
        await r.grid(900)
        self.assertEqual(r.calls[-1],('switch.c','on'))
        self.assertEqual(r.c.profile_cursors,{'heating':'b','drying':'c'})
        self.assertEqual([p['next_id'] for p in r.c.status()['profiles']],[None,None])
        restarted=Rig(deepcopy(r.disk),power=100,states={'switch.a':'on','switch.b':'on','switch.c':'on'})
        self.assertEqual(restarted.c.profile_cursors,{'heating':'b','drying':'c'})
        self.assertEqual(restarted.c.mode,'paused')
        self.assertEqual(restarted.c.config.profiles[0].dashboard_order,'allocation')

    async def test_higher_priority_unaffordable_blocks_smaller_group(self):
        cfg=grouped()
        r=Rig(stored(cfg),power=1200)
        await r.run()
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()['next_id'],'a')
        self.assertIn('Kein Überholen',r.c.reason)

    async def test_earlier_group_cooling_skip_allows_lower_group(self):
        cfg=grouped(); cfg['consumers'][0]['cooldown_s']=300
        cfg['consumers'][1]['cooldown_s']=300
        r=Rig(stored(cfg),power=1900)
        r.c.cooldown_until={'a':r.now+300,'b':r.now+300}
        await r.run()
        self.assertEqual(r.calls,[('switch.c','on')])
        self.assertEqual(r.c.profile_cursors,{'drying':'c'})

    async def test_waiting_cooldown_in_high_group_blocks_lower(self):
        cfg=grouped(); cfg['consumers'][0].update(cooldown_s=300,cooldown_wait=True)
        r=Rig(stored(cfg),power=2500)
        r.c.cooldown_until={'a':r.now+300}
        await r.run()
        self.assertEqual(r.calls,[])
        self.assertEqual(r.c.status()['next_id'],'a')
        self.assertIn('Wiedereinschaltsperre',r.c.reason)

    async def test_shed_lower_priority_first_and_fifo_within_group(self):
        cfg=grouped(); cfg['shutdown_delay_s']=0
        r=Rig(stored(cfg,owned=['a','c','b']),power=0,
              states={'switch.a':'on','switch.b':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls,[('switch.c','off')])  # Summer loses first
        await r.grid(0)
        self.assertEqual(r.calls[1],('switch.a','off'))  # then FIFO Winter
        await r.grid(0)
        self.assertEqual(r.calls[2],('switch.b','off'))

    async def test_delay_override_per_device_with_global_fallback(self):
        cfg=grouped()
        cfg['shutdown_delay_s']=30
        cfg['consumers'][0]['shutdown_delay_s']=10
        cfg['consumers'][2]['shutdown_delay_s']=50
        r=Rig(stored(cfg,owned=['a','c']),power=0,
              states={'switch.a':'on','switch.c':'on'})
        await r.run()
        self.assertEqual(r.calls,[])
        await r.tick(11)
        self.assertEqual(r.calls,[('switch.a','off')])  # high prio due, low still protected by delay
        await r.grid(0)
        await r.tick(40)
        self.assertEqual(r.calls[-1],('switch.c','off'))

    async def test_runtime_profile_toggle_stops_only_owned_group(self):
        cfg=grouped()
        # Keep higher profile fully served: v0.3.1 now preempts lower loads
        # for an unserved higher-priority candidate even during operation.
        cfg['profiles'][0]['consumer_ids']=['a']
        r=Rig(stored(cfg,owned=['a','c']),power=100,
              states={'switch.a':'on','switch.c':'on'})
        await r.run()
        await r.c.profile_participation('heating',False,r.c.revision)
        await r.c.settle()
        self.assertEqual(r.calls,[('switch.a','off')])
        self.assertEqual(r.c.config.profiles[0].enabled,False)
        self.assertTrue(r.c.config.profiles[1].enabled)
        self.assertEqual(r.c.status()['next_profile_id'],None)  # Summer device still on
        await r.c.profile_participation('heating',True,r.c.revision)
        await r.c.settle()
        self.assertEqual(r.c.config.profiles[0].enabled,True)
        self.assertEqual(r.c.mode,'running')

    async def test_profile_deactivation_overrides_strict_minimum(self):
        cfg=grouped(); cfg['consumers'][0].update(min_on_s=1200,min_on_strict=True)
        r=Rig(stored(cfg,owned=['a']),power=50,states={'switch.a':'on'})
        await r.run()
        self.assertEqual(r.calls,[])
        await r.c.profile_participation('heating',False,r.c.revision)
        await r.c.settle()
        self.assertEqual(r.calls,[('switch.a','off')])

    async def test_unassigned_device_not_started(self):
        cfg=grouped(); cfg['profiles'][1]['consumer_ids']=[]
        r=Rig(stored(cfg),power=4000)
        await r.run()
        self.assertEqual(r.calls,[('switch.a','on')])
        await r.grid(4000)
        self.assertEqual(r.calls[-1],('switch.b','on'))
        await r.grid(4000)
        self.assertEqual(len(r.calls),2)
        self.assertEqual(r.c.states['switch.c'],'off')

    async def test_modification_during_running_rejected_but_toggle_allowed(self):
        cfg=grouped(); r=Rig(stored(cfg),power=1500)
        await r.run()
        with self.assertRaises(UserError):
            await r.c.configure(cfg,r.c.revision)
        await r.c.profile_participation('drying',False,r.c.revision)
        self.assertFalse(r.c.config.profiles[1].enabled)
        with self.assertRaises(UserError):
            await r.c.profile_participation('drying',True,r.c.revision-1)

    async def test_group_transfer_rejects_duplicates_but_retains_physical_entities(self):
        cfg=grouped(); r=Rig(stored(cfg),power=200)
        change=r.c.config.to_dict()
        change['profiles'][0]['consumer_ids'].remove('b')
        change['profiles'][1]['consumer_ids'].append('b')
        await r.c.configure(change,r.c.revision)
        self.assertEqual(r.c.config.profiles[1].consumer_ids,('c','b'))
        self.assertEqual(r.c.config.consumers[1].entity_id,'switch.b')
        bad=r.c.config.to_dict()
        bad['profiles'][0]['consumer_ids'].append('b')
        with self.assertRaises(UserError): await r.c.configure(bad,r.c.revision)


if __name__ == '__main__': unittest.main()
