"""Round Robin Hood: local Home Assistant surplus allocation integration."""
from pathlib import Path
import logging

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, NAME, PANEL_PATH, VERSION, ENTRY_GENERATION
from .model import UserError
from .runtime import Runtime
from .websocket import register

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass, config):
    data = hass.data.setdefault(DOMAIN, {})
    if not data.get("registered"):
        await hass.http.async_register_static_paths([
            StaticPathConfig(f"/{DOMAIN}/panel.js", str(Path(__file__).parent / "frontend" / "panel.js"), False),
            StaticPathConfig(f"/{DOMAIN}/brand.png", str(Path(__file__).parent / "brand" / "icon@2x.png"), False),
            StaticPathConfig(f"/{DOMAIN}/guide", str(Path(__file__).parent / "frontend" / "guides"), False)
        ])
        register(hass)
        data["registered"] = True
    return True


async def async_setup_entry(hass, entry):
    if entry.data.get("generation") != ENTRY_GENERATION:
        raise ConfigEntryError("Alter RRH-Eintrag erkannt. Der Neubau übernimmt alte Konfigurationen nicht. Vorher HA-Backup sichern und alten Eintrag über Geräte & Dienste entfernen.")
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("runtime") is not None:
        raise ConfigEntryError("Es darf nur eine RRH-Instanz geladen sein.")
    rt = Runtime(hass)
    try:
        await rt.start()
    except UserError as err:
        raise ConfigEntryError(str(err)) from err
    try:
        await panel_custom.async_register_panel(
            hass, frontend_url_path=PANEL_PATH, webcomponent_name="rrh-hood-panel",
            sidebar_title=NAME, sidebar_icon="mdi:solar-power",
            module_url=f"/{DOMAIN}/panel.js?v={VERSION}&dev=weekly-schedules-095",
            embed_iframe=False, require_admin=True, config_panel_domain=DOMAIN,
        )
    except Exception:
        await rt.stop()
        raise
    data["runtime"] = rt
    entry.runtime_data = rt

    async def shutdown(_event):
        await rt.stop()

    entry.async_on_unload(hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, shutdown))
    return True


async def async_unload_entry(hass, entry):
    rt = entry.runtime_data
    try:
        await rt.stop()
    except Exception:
        _LOGGER.exception("RRH storage could not be flushed during unload")
    frontend.async_remove_panel(hass, PANEL_PATH)
    hass.data[DOMAIN].pop("runtime", None)
    return True
