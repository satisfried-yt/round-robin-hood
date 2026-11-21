"""One administrator-only API. The panel never writes HA storage directly."""
from __future__ import annotations

import logging
import probatio as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .model import UserError

_LOGGER = logging.getLogger(__name__)


def runtime(hass: HomeAssistant):
    rt = hass.data.get(DOMAIN, {}).get("runtime")
    if rt is None or rt.controller.closed:
        raise UserError("Round Robin Hood ist nicht geladen. Integration und HA-Protokoll pr\u00fcfen.")
    return rt


@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/status"})
@websocket_api.require_admin
@callback
def status(hass, connection, msg):
    try:
        rt = runtime(hass)
        result = rt.active.status()
        result["demo_mode"] = rt.demo is not None
        result["demo_power_w"] = rt.demo.generator_w if rt.demo is not None else None
        result["notice_dismissed"] = rt.controller.config.notice_dismissed
        result["setup_complete"] = rt.controller.config.setup_complete
        result["setup_needed"] = not rt.controller.config.setup_complete and not rt.controller.config.grid_entity and not rt.controller.config.consumers
        connection.send_result(msg["id"], result)
    except UserError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))


@websocket_api.websocket_command({
    vol.Required("type"): f"{DOMAIN}/command",
    vol.Required("action"): vol.In(["activate", "pause", "emergency_off", "configure", "participation", "profile_participation", "skip_timer", "reset_fair", "reset_statistics", "demo_mode", "demo_power", "dismiss_notice", "factory_reset"]),
    vol.Optional("config"): dict,
    vol.Optional("revision"): int,
    vol.Optional("consumer_id"): str,
    vol.Optional("profile_id"): str,
    vol.Optional("enabled"): bool,
    vol.Optional("timer"): vol.In(["minimum", "cooldown"]),
    vol.Optional("metric"): vol.In(["fair_runtime", "fair_energy"]),
    vol.Optional("demo_enabled"): bool,
    vol.Optional("demo_power_w"): int,
    vol.Optional("notice_dismissed"): bool,
    vol.Optional("currency_tariffs_confirmed"): bool,
    vol.Optional("confirmation"): str,
})
@websocket_api.require_admin
@websocket_api.async_response
async def command(hass, connection, msg):
    try:
        rt = runtime(hass)
        c = rt.active
        action = msg["action"]
        if action == "dismiss_notice":
            if "notice_dismissed" not in msg:
                raise UserError("Hinweisbestätigung fehlt.")
            await rt.controller.dismiss_notice(msg["notice_dismissed"])
        elif action == "demo_mode":
            if "demo_enabled" not in msg:
                raise UserError("Demo-Status fehlt.")
            await rt.switch_demo(msg["demo_enabled"])
        elif action == "demo_power":
            if "demo_power_w" not in msg:
                raise UserError("Demo-Leistung fehlt.")
            rt.demo_power(msg["demo_power_w"])
        elif action == "pause":
            c.pause()
        elif action == "activate":
            await c.activate()
        elif action == "emergency_off":
            await c.emergency_off()
        elif action == "configure":
            if "config" not in msg or "revision" not in msg:
                raise UserError("Konfiguration und Revision fehlen.")
            await rt.configure(msg["config"], msg["revision"], currency_tariffs_confirmed=msg.get("currency_tariffs_confirmed", False))
        elif action == "skip_timer":
            if not all(k in msg for k in ("consumer_id", "timer", "revision")):
                raise UserError("Verbraucher, Zeitregel und Revision fehlen.")
            await c.skip_timer(msg["consumer_id"], msg["timer"], msg["revision"])
        elif action == "factory_reset":
            if "revision" not in msg or "confirmation" not in msg:
                raise UserError("Reset-Revision und Bestätigung fehlen.")
            await rt.factory_reset(msg["revision"], msg["confirmation"])
        elif action == "reset_statistics":
            if "revision" not in msg:
                raise UserError("Konfigurationsrevision fehlt.")
            await c.reset_statistics(msg["revision"])
        elif action == "reset_fair":
            if not all(k in msg for k in ("profile_id", "metric", "revision")):
                raise UserError("Profil, Statistik und Revision fehlen.")
            await c.reset_fair(msg["profile_id"], msg["metric"], msg["revision"])
        elif action == "profile_participation":
            if not all(k in msg for k in ("profile_id", "enabled", "revision")):
                raise UserError("Profil, Aktivierung und Revision fehlen.")
            await c.profile_participation(msg["profile_id"], msg["enabled"], msg["revision"])
        else:
            if not all(k in msg for k in ("consumer_id", "enabled", "revision")):
                raise UserError("Verbraucher, Teilnahme und Revision fehlen.")
            await c.participation(msg["consumer_id"], msg["enabled"], msg["revision"])
        result = rt.active.status()
        result["demo_mode"] = rt.demo is not None
        result["demo_power_w"] = rt.demo.generator_w if rt.demo is not None else None
        result["notice_dismissed"] = rt.controller.config.notice_dismissed
        result["setup_complete"] = rt.controller.config.setup_complete
        result["setup_needed"] = not rt.controller.config.setup_complete and not rt.controller.config.grid_entity and not rt.controller.config.consumers
        connection.send_result(msg["id"], result)
    except UserError as err:
        connection.send_error(msg["id"], "rrh_error", str(err))
    except Exception:
        _LOGGER.exception("RRH API operation failed")
        connection.send_error(msg["id"], "rrh_error", "Vorgang fehlgeschlagen. HA-Protokoll pr\u00fcfen; nicht automatisch wiederholen.")


@callback
def register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, status)
    websocket_api.async_register_command(hass, command)
