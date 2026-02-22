"""Config flow for Elisa Kotiakku integration."""

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN, 
    CONF_API_KEY, 
    CONF_URL, 
    CONF_NAME, 
    CONF_SCAN_INTERVAL, 
    DEFAULT_NAME, 
    DEFAULT_SCAN_INTERVAL, 
    MIN_SCAN_INTERVAL,
    CONF_POWER_UNIT,
    DEFAULT_POWER_UNIT,
    UNIT_W,
    UNIT_KW
)

async def validate_input(hass, data):
    """Validate the user input allows us to connect.
    
    This function actually hits the API to see if the URL and Token are valid
    before we allow the user to finish the setup.
    """
    session = async_get_clientsession(hass)
    headers = {"X-API-KEY": data[CONF_API_KEY]}
    
    try:
        async with session.get(data[CONF_URL], headers=headers, timeout=10) as response:
            if response.status == 401:
                return "invalid_auth"
            response.raise_for_status()
    except Exception:
        return "cannot_connect"
    
    return None

class ElisaKotiakkuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elisa Kotiakku."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # VALIDATION STEP: Check if the token/URL works
            error = await validate_input(self.hass, user_input)
            
            if not error:
                # Only create the entry if there's no error
                return self.async_create_entry(
                    title=user_input[CONF_NAME], 
                    data=user_input
                )
            else:
                # If validation failed, add the error to the form
                errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_URL, default="http://127.0.0.1:8000/api/v1/status"): str,
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_POWER_UNIT, default=DEFAULT_POWER_UNIT): vol.In([UNIT_W, UNIT_KW]),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                ),
            }),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Link to Options Flow."""
        return ElisaKotiakkuOptionsFlowHandler(config_entry)

class ElisaKotiakkuOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options (settings updates)."""
    
    def __init__(self, config_entry):
        """Initialize."""
        pass
        #self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    CONF_POWER_UNIT,
                    default=self.config_entry.options.get(
                        CONF_POWER_UNIT, 
                        self.config_entry.data.get(CONF_POWER_UNIT, DEFAULT_POWER_UNIT)
                    ),
                ): vol.In([UNIT_W, UNIT_KW]),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, 
                        self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)),
                vol.Optional(CONF_POWER_UNIT, default=DEFAULT_POWER_UNIT): vol.In([UNIT_W, UNIT_KW]),
            }),
        )