"""Ephemeral RRH sandbox: no Home Assistant entities, services or storage access.

The simulator uses the REAL allocation controller with six in-memory devices;
every service command is replaced by a fake observation and a synthetic fresh
net-power report. It is deliberately not serialised into the live RRH document.
"""
from __future__ import annotations

from .controller import Controller
from .model import Config, UserError


DEMO_LOADS = (300, 500, 750, 1000, 1200, 1800)


class DemoSandbox:
    def __init__(self):
        self.generator_w = 1600
        self.saved = None
        self.controller = Controller(None, send=self._send, save=self._save,
                                     send_all_off=self._send_all_off,
                                     send_level=self._send_level)

    async def start(self):
        config = Config().to_dict()
        config["grid_entity"] = "sensor.rrh_demo_grid"
        config["consumers"] = [
            {"id": f"demo{i}", "name": f"Demo-Verbraucher {i} ({w} W)",
             "entity_id": f"switch.rrh_demo_{i}", "watts": w,
             "enabled": True, "virtual_confirmed": True}
            for i, w in enumerate(DEMO_LOADS, 1)
        ]
        config["profiles"] = [{"id": "demo_standard", "name":"Demo – Standard", "enabled":True,
                               "strategy":"classic", "consumer_ids":[f"demo{i}" for i in range(1,7)],
                               "dashboard_order":"fixed", "allow_power_skip":True}]
        for item in config["consumers"]:
            self.controller.seed_switch(item["entity_id"], "off")
        await self.controller.configure(config, 0)
        self.sample()

    async def _save(self, data):
        self.saved = data

    async def _send(self, entity_id, target, token):
        self.controller.observe_switch(entity_id, target, command_token=token)
        self.sample()

    async def _send_all_off(self, entities):
        for eid in entities:
            self.controller.observe_switch(eid, "off", command_token="main-off")
        self.sample()

    async def _send_level(self, consumer, target, token):
        self.controller.observe_power_level(consumer.id, target)
        self.sample()

    def sample(self):
        controller = self.controller
        managed = sum(controller._load_w(c) for c in controller.config.consumers
                      if controller.states.get(c.entity_id) == "on")
        controller.observe_grid(str(self.generator_w - managed), "W")

    def set_power(self, power_w):
        if type(power_w) is not int or power_w < 0 or power_w > 10000:
            raise UserError("Demo-Leistung: 0 bis 10.000 W erforderlich.")
        self.generator_w = power_w
        self.sample()

    async def close(self):
        await self.controller.close()
