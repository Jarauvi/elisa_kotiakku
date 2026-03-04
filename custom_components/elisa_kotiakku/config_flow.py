"""Config flow for Elisa Kotiakku integration."""

import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
_LOGGER = logging.getLogger(__name__)

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
    session = async_get_clientsession(hass)
    headers = {
        "x-api-key": data[CONF_API_KEY],
        "accept": "application/json"
    }
    
    try:
        async with session.get(data[CONF_URL], headers=headers, timeout=10) as response:
            # --- DEBUGGING SECTION ---
            # We read the body regardless of status to see error messages
            response_text = await response.text()
            _LOGGER.debug("API Response Status: %s", response.status)
            _LOGGER.debug("API Response Body: %s", response_text)
            # -------------------------

            if response.status == 401:
                return "invalid_auth"
            
            # If status is 4xx or 5xx, this raises an exception
            response.raise_for_status()

    except aiohttp.ClientConnectorError as err:
        # This catches DNS or "No route to host" errors
        _LOGGER.error("Connection error: %s", err)
        return "cannot_connect"
    except Exception as err:
        # This catches EVERYTHING else and prints the actual error to your log
        _LOGGER.error("Validation failed: %s", err)
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
                vol.Required(CONF_URL, default="https://residential.gridle.com/api/public/measurements"): str,
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_POWER_UNIT, default=DEFAULT_POWER_UNIT): vol.In([UNIT_W, UNIT_KW]),
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                ),
            }),
            errors=errors,
        )

