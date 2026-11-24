"""Thin HA adapter: existing entities, standard services and atomic HA storage."""
from __future__ import annotations

from datetime import timedelta
import logging
import json
from pathlib import Path
from typing import Any

from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_state_report_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import STORAGE_KEY, STORAGE_VERSION
from .controller import Controller
from .demo import DemoSandbox
from .model import UserError, Config
from .energy_sources import numeric_source_value, divisor_and_scale

_LOGGER = logging.getLogger(__name__)


class Runtime:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY, atomic_writes=True)
        self.controller: Controller
        self.demo: DemoSandbox | None = None
        self._unsub: list = []
        self._timer = None
        self._command_context: Context | None = None
        self._command_token: str | None = None
        self._grid_identity = None

    async def start(self) -> None:
        existed = await self.hass.async_add_executor_job(Path(self.store.path).is_file)
        saved = await self.store.async_load()
        if existed and saved is None:
            raise UserError("Vorhandene RRH-Speicherdaten konnten nicht gelesen werden. Keine neue Konfiguration angelegt; HA-Protokoll und Sicherung pr\u00fcfen.")
        # Resolve the Home Assistant timezone asynchronously once. EnergyLedger
        # subsequently uses the tzinfo directly, including after statistics reset.
        timezone_name = self.hass.config.time_zone
        timezone = await dt_util.async_get_time_zone(timezone_name)
        if timezone is None:
            raise UserError(f"Ungültige Home-Assistant-Zeitzone: {timezone_name!r}")
        self.controller = Controller(saved, send=self._send, send_all_off=self._send_all_off,
                                     send_level=self._send_level, save=self._save_verified, timezone=timezone)
        self.bind()
        # On initial setup/reload require one actual new source report before dispatch.
        self.controller.wait_after_sequence = self.controller.reading.sequence
        self.controller.restore_startup()
        self._timer = async_track_time_interval(self.hass, self._tick, timedelta(seconds=1))
        self.controller.wake()

    def _read_stored_document(self) -> dict:
        with open(self.store.path, encoding="utf-8") as handle:
            return json.load(handle)

    async def _save_verified(self, data: dict) -> None:
        # HA Store can log and suppress WriteError, or defer writes during shutdown.
        # Never interpret its return alone as a durable allocation/configuration commit.
        await self.store.async_save(data)
        stored = await self.hass.async_add_executor_job(self._read_stored_document)
        if stored.get("version") != STORAGE_VERSION or stored.get("key") != STORAGE_KEY or stored.get("data") != data:
            raise OSError("RRH storage verification failed; expected document is not on disk")

    @callback
    def _tick(self, _now: Any) -> None:
        self.controller.sample_statistics(values=self._stat_sources())
        self.controller.wake()
        if self.demo is not None:
            self.demo.sample()
            self.demo.controller.sample_statistics(values={"import_price":0.30,"feed_in_price":0.08,"pv_size_kwp":6.0,"pv_power_w":self.demo.generator_w})

    def _stat_sources(self) -> dict:
        """Read existing HA energy/price helpers. No alteration of Energy dashboard settings."""
        result={"warnings":[]}
        cfg=self.controller.config.energy
        def read(eid,kind):
            if not eid: return None
            state=self.hass.states.get(eid)
            if state is None or state.state in ("unknown","unavailable") or state.attributes.get("restored"):
                result["warnings"].append(f"{eid}: keine gültigen Sensordaten")
                return None
            try:
                return numeric_source_value(state.state, state.attributes.get("unit_of_measurement"), kind, cfg.currency)
            except ValueError:
                result["warnings"].append(f"{eid}: Zahlenwert oder Einheit ungültig")
                return None
        for key, source, kind in (("pv_size_kwp",cfg.pv_size,"capacity"),
                                  ("import_price",cfg.import_price,"price"),
                                  ("feed_in_price",cfg.feed_in_price,"price")):
            result[key]=source.value if source.mode=="fixed" else read(source.entity_id,kind)
        result["pv_power_w"]=read(cfg.pv_power_entity,"power")
        result["pv_meter_kwh"]=read(cfg.pv_energy_entity,"energy")
        result["export_meter_kwh"]=read(cfg.grid_export_energy_entity,"energy")
        return result

    @property
    def active(self) -> Controller:
        return self.demo.controller if self.demo is not None else self.controller

    async def switch_demo(self, enabled: bool) -> None:
        if type(enabled) is not bool:
            raise UserError("Ungültiger Demo-Modus.")
        if enabled and self.demo is None:
            c = self.controller
            if c.mode == "running" or c.pending or c._emergency_active or c.emergency_unresolved:
                raise UserError("Demo-Modus: echte Automatik zuerst mit Alle AUS stoppen.")
            if any(cid in c.owned and c.states.get(item.entity_id) == "on"
                   for item in c.config.consumers for cid in [item.id]):
                raise UserError("Demo-Modus: verwaltete Geräte sind noch eingeschaltet.")
            demo = DemoSandbox()
            await demo.start()
            self.demo = demo
        elif not enabled and self.demo is not None:
            if self.demo.controller.pending is not None or self.demo.controller._emergency_active:
                raise UserError("Demo-Modus: laufenden virtuellen Schaltauftrag erst abschließen.")
            await self.demo.close()
            self.demo = None

    def demo_power(self, power_w: int) -> None:
        if self.demo is None:
            raise UserError("Demo-Leistung ist nur im Demo-Modus einstellbar.")
        self.demo.set_power(power_w)

    @callback
    def bind(self) -> None:
        for cancel in self._unsub:
            cancel()
        self._unsub.clear()
        cfg = self.controller.config
        ids = [c.entity_id for c in cfg.consumers]
        for entity_id in ids:
            state = self.hass.states.get(entity_id)
            self.controller.seed_switch(entity_id, self._normal_state(entity_id, state) if state else "unavailable")
            self._read_level(entity_id, state, initial=True)
        condition_ids = self.controller._condition_sensor_ids()
        for entity_id in sorted(condition_ids):
            state = self.hass.states.get(entity_id)
            self.controller.observe_condition(entity_id, state.state if state else None,
                                              restored=bool(state.attributes.get("restored", False)) if state else False)
        ids.extend(sorted(condition_ids - set(ids)))
        ids.extend([c.stage_entity_id for c in cfg.consumers if c.stage_entity_id and c.stage_entity_id not in ids])
        if cfg.grid_entity:
            self._read_grid(self.hass.states.get(cfg.grid_entity))
            ids.append(cfg.grid_entity)
            self._unsub.append(async_track_state_report_event(self.hass, [cfg.grid_entity], self._reported))
        if ids:
            self._unsub.append(async_track_state_change_event(self.hass, ids, self._changed))

    @callback
    def _read_grid(self, state: Any) -> None:
        identity = (self.controller.config.grid_entity, state.last_reported if state is not None else None)
        if identity == self._grid_identity:
            return  # Rebinding/re-reading the same HA state is not a new source report.
        self._grid_identity = identity
        if state is None:
            self.controller.observe_grid(None, None)
            return
        # Only a real HA state report changes this timestamp; polling the panel does not.
        age = (dt_util.utcnow() - state.last_reported).total_seconds()
        self.controller.observe_grid(state.state, state.attributes.get("unit_of_measurement"),
                                     age_s=age, restored=bool(state.attributes.get("restored", False)))

    @callback
    def _reported(self, event: Any) -> None:
        self._read_grid(event.data.get("new_state") or self.hass.states.get(self.controller.config.grid_entity))

    @callback
    def _changed(self, event: Any) -> None:
        entity_id = event.data["entity_id"]
        state = event.data.get("new_state")
        if entity_id == self.controller.config.grid_entity:
            self._read_grid(state)
            if entity_id not in self.controller._condition_sensor_ids():
                return
        if entity_id in self.controller._condition_sensor_ids():
            self.controller.observe_condition(entity_id, state.state if state else None,
                                              restored=bool(state.attributes.get("restored", False)) if state else False)
            return
        token = None
        context = state.context if state is not None else event.context
        if self._command_context and (context.id == self._command_context.id or context.parent_id == self._command_context.id):
            token = self._command_token
        if any(c.entity_id == entity_id for c in self.controller.config.consumers):
            self.controller.observe_switch(entity_id, self._normal_state(entity_id, state),
                                           command_token=token, explicit_external=bool(context.user_id))
        self._read_level(entity_id, state, explicit_external=bool(context.user_id))

    def _consumer(self, entity_id: str):
        return next((c for c in self.controller.config.consumers if c.entity_id == entity_id), None)

    def _normal_state(self, entity_id, state) -> str:
        if state is None or state.state in ("unavailable", "unknown"):
            return "unavailable"
        c = self._consumer(entity_id)
        if c is None or c.power_mode == "fixed" or entity_id.startswith("switch."):
            return state.state
        if c.power_mode == "variable":
            try:
                return "on" if float(state.state) > 0 else "off"
            except (TypeError, ValueError):
                return "unavailable"
        if entity_id.startswith("climate."):
            return "off" if state.state == "off" else "on" if state.state in ("heat", "auto") else "unavailable"
        if entity_id.startswith("select."):
            return "off" if state.state == c.off_option else "on" if state.state in {s.option for s in c.power_steps} else "unavailable"
        return "unavailable"

    def _read_level(self, entity_id, state, *, initial=False, explicit_external=False) -> None:
        if state is None or state.state in ("unavailable", "unknown"):
            return
        for c in self.controller.config.consumers:
            if c.power_mode == "fixed" or (c.entity_id != entity_id and c.stage_entity_id != entity_id):
                continue
            level = None
            if c.power_mode == "variable" and c.entity_id == entity_id:
                try: level = float(state.state)
                except (TypeError, ValueError): continue
            elif c.power_mode == "staged" and c.stage_entity_id == entity_id:
                val = (state.attributes.get("fan_mode") if entity_id.startswith("climate.") else state.state)
                match = next((step for step in c.power_steps if step.option == str(val)), None)
                if match: level = match.watts
            if level is not None:
                if initial:
                    self.controller.seed_power_level(c.id, level)
                else:
                    self.controller.observe_power_level(c.id, level, explicit_external=explicit_external)

    async def _ha_service(self, domain, service, data, token):
        if not self.hass.services.has_service(domain, service):
            raise UserError(f"HA-Aktion {domain}.{service} ist nicht verfügbar.")
        self._command_context = Context()
        self._command_token = token
        await self.hass.services.async_call(domain, service, data,
                                            blocking=True, context=self._command_context)

    async def _send_stage(self, consumer, desired, token):
        step = next((item for item in consumer.power_steps if abs(item.watts-desired)<.001), None)
        if step is None:
            raise UserError("Leistungsstufe nicht konfiguriert.")
        eid = consumer.stage_entity_id
        if eid.startswith("select."):
            await self._ha_service("select", "select_option", {"entity_id":eid, "option":step.option}, token)
        elif eid.startswith("climate."):
            await self._ha_service("climate", "set_fan_mode", {"entity_id":eid, "fan_mode":step.option}, token)
        else:
            raise UserError("Unbekannte Stufensteuerung.")
        observed = self.hass.states.get(eid)
        value = (observed.attributes.get("fan_mode") if eid.startswith("climate.") else observed.state) if observed is not None else None
        if str(value) != step.option:
            raise UserError(f"Stufe {step.option} wurde von HA nicht bestätigt; kein Einschalten.")

    async def _send_level(self, consumer, watts, token):
        if consumer.power_mode == "variable":
            await self._ha_service("number", "set_value", {"entity_id":consumer.entity_id,"value":watts}, token)
        elif consumer.power_mode == "staged":
            await self._send_stage(consumer, watts, token)
        else:
            raise UserError("Ein/Aus-Verbraucher können nicht geregelt werden.")
        # A service may return after the entity was updated, or report state
        # without another state_changed event. Explicitly inspect HA feedback.
        eid = consumer.stage_entity_id if consumer.power_mode == "staged" else consumer.entity_id
        self._read_level(eid, self.hass.states.get(eid))

    async def _send(self, entity_id: str, target: str, token: str) -> None:
        c = self._consumer(entity_id)
        if c is not None and c.power_mode != "fixed":
            if c.power_mode == "variable":
                await self._ha_service("number", "set_value", {"entity_id":entity_id,
                                      "value":c.watts if target == "on" else 0}, token)
            elif c.power_mode == "staged":
                if target == "on":
                    await self._send_stage(c, c.watts, token)
                domain = entity_id.split(".")[0]
                if domain == "climate":
                    await self._ha_service("climate", "set_hvac_mode", {"entity_id":entity_id,
                                           "hvac_mode":"heat" if target == "on" else "off"}, token)
                elif domain == "select":
                    if target == "off":
                        await self._ha_service("select", "select_option", {"entity_id":entity_id,
                                               "option":c.off_option}, token)
                else:
                    await self._ha_service("switch", "turn_on" if target == "on" else "turn_off",
                                           {"entity_id":entity_id}, token)
            # Force refresh level/state from HA after a blocking service call.
            observed = self.hass.states.get(entity_id)
            self.controller.observe_switch(entity_id, self._normal_state(entity_id, observed), command_token=token)
            self._read_level(c.stage_entity_id if c.power_mode == "staged" else entity_id,
                             self.hass.states.get(c.stage_entity_id if c.power_mode == "staged" else entity_id))
            return
        service = "turn_on" if target == "on" else "turn_off"
        if not self.hass.services.has_service("switch", service):
            raise UserError("Die ben\u00f6tigte HA-Schaltaktion ist nicht verf\u00fcgbar.")
        self._command_context = Context()
        self._command_token = token
        _LOGGER.info("RRH HA-Service START: switch.%s fuer %s", service, entity_id)
        try:
            await self.hass.services.async_call("switch", service, {"entity_id": entity_id},
                                                blocking=True, context=self._command_context)
        except Exception:
            _LOGGER.exception("RRH HA-Service FEHLER: switch.%s fuer %s", service, entity_id)
            raise
        _LOGGER.info("RRH HA-Service FERTIG: switch.%s fuer %s; beobachteter Zustand=%s", service, entity_id,
                     (self.hass.states.get(entity_id).state if self.hass.states.get(entity_id) else "unavailable"))

    async def _send_all_off(self, entities: list[str]) -> None:
        # The controller's dispatch lock orders this bulk OFF after an in-flight ON.
        fixed = [eid for eid in entities if (c:=self._consumer(eid)) is not None and c.power_mode == "fixed"]
        errors = []
        if fixed:
            try:
                await self._ha_service("switch", "turn_off", {"entity_id":fixed}, "main-off")
            except Exception as err:
                errors.append(str(err))
        for eid in entities:
            c = self._consumer(eid)
            if c is not None and c.power_mode != "fixed":
                try:
                    await self._send(eid, "off", "main-off")
                except Exception as err:
                    errors.append(f"{eid}: {err}")
        if errors:
            raise UserError("Nicht alle AUS-Befehle konnten gesendet werden: " + "; ".join(errors))

    async def factory_reset(self, revision: int, confirmation: str) -> None:
        if self.demo is not None:
            raise UserError("Demo-Modus vor dem vollständigen Reset verlassen.")
        await self.controller.factory_reset(revision, confirmation)
        # Drop all subscribers to previously configured sensors/actuators.
        self.bind()

    def _validate_new_energy_sources(self, proposed: Config) -> None:
        """Check newly selected HA sensors at the backend security boundary.

        Existing unchanged sources remain loadable for backward compatibility;
        invalid live data is nonetheless ignored by _stat_sources.
        """
        old = self.controller.config.energy
        new = proposed.energy
        sources = (
            ("PV-Nennleistung", new.pv_size.entity_id if new.pv_size.mode == "entity" else "", "capacity", old.pv_size.entity_id if old.pv_size.mode == "entity" else ""),
            ("Strompreis", new.import_price.entity_id if new.import_price.mode == "entity" else "", "price", old.import_price.entity_id if old.import_price.mode == "entity" else ""),
            ("Einspeisevergütung", new.feed_in_price.entity_id if new.feed_in_price.mode == "entity" else "", "price", old.feed_in_price.entity_id if old.feed_in_price.mode == "entity" else ""),
            ("PV-Leistung", new.pv_power_entity, "power", old.pv_power_entity),
            ("PV-Energiezähler", new.pv_energy_entity, "energy", old.pv_energy_entity),
            ("Netzeinspeisezähler", new.grid_export_energy_entity, "energy", old.grid_export_energy_entity),
        )
        for label, eid, kind, old_eid in sources:
            if not eid or (eid == old_eid and new.currency == old.currency):
                continue
            state = self.hass.states.get(eid)
            unit = state.attributes.get("unit_of_measurement") if state else None
            if state is None or getattr(state, "state", None) in ("unknown", "unavailable") or state.attributes.get("restored"):
                raise UserError(f"{label}: HA-Entität {eid} liefert aktuell keine gültige Messung.")
            if divisor_and_scale(kind, unit, new.currency) is None:
                raise UserError(f"{label}: Einheit {unit!r} ist nicht kompatibel mit {new.currency} oder {kind}.")
            try:
                numeric_source_value(state.state, unit, kind, new.currency)
            except ValueError as err:
                raise UserError(f"{label}: Entität {eid} liefert keinen nutzbaren Zahlenwert.") from err

    async def configure(self, config: dict, revision: int, *, currency_tariffs_confirmed: bool = False) -> None:
        proposed = Config.parse(config)
        if self.demo is None:
            self._validate_new_energy_sources(proposed)
        await self.active.configure(config, revision, currency_tariffs_confirmed=currency_tariffs_confirmed)
        if self.demo is None:
            self.bind()
            self.controller.wait_after_sequence = self.controller.reading.sequence
            self.controller.wake()
        else:
            self.demo.sample()

    async def stop(self) -> None:
        if self._timer:
            self._timer()
            self._timer = None
        try:
            if self.demo is not None:
                await self.demo.close()
                self.demo = None
            await self.controller.close()
        finally:
            for cancel in self._unsub:
                cancel()
            self._unsub.clear()
