"""Only bootstrap here. All everyday configuration belongs to the panel."""
from homeassistant.config_entries import ConfigFlow
from .const import DOMAIN, NAME, ENTRY_GENERATION


class RoundRobinHoodConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()
        if user_input is not None:
            return self.async_create_entry(title=NAME, data={"generation": ENTRY_GENERATION})
        return self.async_show_form(step_id="user")
