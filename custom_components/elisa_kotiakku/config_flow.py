"""Config flow for Elisa Kotiakku integration."""
import copy
import logging
import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

_LOGGER = logging.getLogger(__name__)

from .const import (
    DOMAIN, 
    CONF_API_KEY, 
    CONF_URL, 
    DEFAULT_URL,
    CONF_NAME, 
    CONF_SCAN_INTERVAL, 
    DEFAULT_NAME, 
    DEFAULT_SCAN_INTERVAL, 
    MIN_SCAN_INTERVAL,
    CONF_POWER_UNIT,
    DEFAULT_POWER_UNIT,
    UNIT_W,
    UNIT_KW,
    CONF_BATTERY_CAPACITY,
    DEFAULT_BATTERY_CAPACITY,
    MIN_BATTERY_CAPACITY,
    MAX_BATTERY_CAPACITY,
    CONF_ADD_TAX,
    DEFAULT_ADD_TAX,
    CONF_TAX_PERCENTAGE,
    DEFAULT_TAX_PERCENTAGE,
    CONF_TRANSFER_PRICING,
    DEFAULT_TRANSFER_PRICING,
    TRANSFER_IGNORE,
    TRANSFER_DAY_NIGHT,
    TRANSFER_FIXED,
    TRANSFER_SEASONAL,
    CONF_FIXED_TRANSFER_PRICE,
    DEFAULT_FIXED_TRANSFER_PRICE,
    CONF_DAY_PRICE,
    DEFAULT_DAY_PRICE,
    CONF_NIGHT_PRICE,
    DEFAULT_NIGHT_PRICE,
    CONF_DAY_START,
    DEFAULT_DAY_START,
    CONF_NIGHT_START,
    DEFAULT_NIGHT_START,
    CONF_SUMMER_START_MONTH,
    DEFAULT_SUMMER_START_MONTH,
    CONF_WINTER_START_MONTH,
    DEFAULT_WINTER_START_MONTH,
    CONF_SUMMER_DAY_PRICE,
    DEFAULT_SUMMER_DAY_PRICE,
    CONF_SUMMER_NIGHT_PRICE,
    DEFAULT_SUMMER_NIGHT_PRICE,
    CONF_WINTER_DAY_PRICE,
    DEFAULT_WINTER_DAY_PRICE,
    CONF_WINTER_NIGHT_PRICE,
    DEFAULT_WINTER_NIGHT_PRICE,
    SECTION_API_SETTINGS,
    SECTION_BATTERY_SETTINGS,
    SECTION_CURRENCY_SETTINGS,
    get_config_parameter
    
    
)

async def validate_api_key(hass, data):
    session = async_get_clientsession(hass)
    headers = {
        "x-api-key": data[SECTION_API_SETTINGS][CONF_API_KEY],
        "accept": "application/json"
    }
    
    try:
        async with session.get(data[SECTION_API_SETTINGS][CONF_URL], headers=headers, timeout=10) as response:
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

class ElisaKotiakkuCommonSteps:
    """Shared logic for both Config and Options flows."""

    async def async_step_fixed_transfer(self, user_input=None):
        config_entry = getattr(self, "config_entry", None)
        
        if user_input is not None:
            data = copy.deepcopy(self._base_config)
            data["currency_settings"].update(user_input)
            
            return self.async_create_entry(title="", data=data)
            
        if config_entry:
            current_config = {
                **config_entry.data.get("currency_settings", {}), 
                **config_entry.options
            }
        else:
            current_config = {}
            
        return self.async_show_form(
            step_id="fixed_transfer",
            data_schema=vol.Schema({
                vol.Required(
                    CONF_FIXED_TRANSFER_PRICE, 
                    default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_FIXED_TRANSFER_PRICE, DEFAULT_FIXED_TRANSFER_PRICE))
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                    )
                )
            })
        )
        
    async def async_step_day_night_transfer(self, user_input=None):
        config_entry = getattr(self, "config_entry", None)
        
        if user_input is not None:
            data = copy.deepcopy(self._base_config)
            data["currency_settings"].update(user_input)
            
            return self.async_create_entry(title="", data=data)
            
        if config_entry:
            current_config = {
                **config_entry.data.get("currency_settings", {}), 
                **config_entry.options
            }
        else:
            current_config = {}

        schema = vol.Schema({
            vol.Required(
                CONF_DAY_START, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_START, DEFAULT_DAY_START))
            ): selector.TimeSelector(),
            vol.Required(
                CONF_NIGHT_START, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_START, DEFAULT_NIGHT_START))
            ): selector.TimeSelector(),
            vol.Required(
                CONF_DAY_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_PRICE, DEFAULT_DAY_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            ),
            vol.Required(
                CONF_NIGHT_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_PRICE, DEFAULT_NIGHT_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            )
        })

        return self.async_show_form(
            step_id="day_night_transfer",
            data_schema=schema,
        )
        
    async def async_step_seasonal_transfer(self, user_input=None):
        config_entry = getattr(self, "config_entry", None)
        
        if user_input is not None:
            data = copy.deepcopy(self._base_config)
            data["currency_settings"].update(user_input)
            
            return self.async_create_entry(title="", data=data)
            
        if config_entry:
            current_config = {
                **config_entry.data.get("currency_settings", {}), 
                **config_entry.options
            }
        else:
            current_config = {}

        schema = vol.Schema({
            vol.Required(
                CONF_WINTER_START_MONTH, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_WINTER_START_MONTH, DEFAULT_WINTER_START_MONTH))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": str(i), "label": str(i)} for i in range(1, 13)]
                )    
            ),
            vol.Required(
                CONF_SUMMER_START_MONTH, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_SUMMER_START_MONTH, DEFAULT_SUMMER_START_MONTH))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": str(i), "label": str(i)} for i in range(1, 13)]
                )    
            ),
            vol.Required(
                CONF_DAY_START, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_START, DEFAULT_DAY_START))
            ): selector.TimeSelector(),
            vol.Required(
                CONF_NIGHT_START, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_START, DEFAULT_NIGHT_START))
            ): selector.TimeSelector(),
            vol.Required(
                CONF_WINTER_DAY_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_WINTER_DAY_PRICE, DEFAULT_WINTER_DAY_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            ),
            vol.Required(
                CONF_WINTER_NIGHT_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_WINTER_NIGHT_PRICE, DEFAULT_WINTER_NIGHT_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            ),
            vol.Required(
                CONF_SUMMER_DAY_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_SUMMER_DAY_PRICE, DEFAULT_SUMMER_DAY_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            ),
            vol.Required(
                CONF_SUMMER_NIGHT_PRICE, 
                default=str(get_config_parameter(config_entry, SECTION_CURRENCY_SETTINGS, CONF_SUMMER_NIGHT_PRICE, DEFAULT_SUMMER_NIGHT_PRICE))
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=10, step=0.1, mode=selector.NumberSelectorMode.BOX, unit_of_measurement="c/kWh"
                )
            )
        })

        return self.async_show_form(
            step_id="seasonal_transfer",
            data_schema=schema,
        )
class ElisaKotiakkuConfigFlow(config_entries.ConfigFlow, ElisaKotiakkuCommonSteps, domain=DOMAIN):
    """Handle a config flow for Elisa Kotiakku."""
    
    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ElisaKotiakkuOptionsFlow()
    
    async def _device_exists(self, name: str) -> bool:
        """Check if a device with the given name already exists."""
        device_registry = async_get_device_registry(self.hass)
        return any(device.name == name for device in device_registry.devices.values())

    async def _api_key_exists(self, api_key: str) -> bool:
            """Check if any other entry already uses this API key."""
            current_entries = self._async_current_entries()
            for entry in current_entries:
                existing_key = get_config_parameter(entry, SECTION_API_SETTINGS, CONF_API_KEY, "")
                if existing_key == api_key:
                    return True
            return False
        
    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # VALIDATION STEP: Check if the token/URL works
            error = await validate_api_key(self.hass, user_input)

            if error:
                errors["base"] = error
                
            if await self._device_exists(user_input[SECTION_BATTERY_SETTINGS][CONF_NAME]):
                errors["base"] = "device_already_configured"
            
            if await self._api_key_exists(user_input[SECTION_API_SETTINGS][CONF_API_KEY]):
                errors["base"] = "api_already_configured"
            
            else:
                pricing = user_input[SECTION_CURRENCY_SETTINGS][CONF_TRANSFER_PRICING]

                self._base_config = user_input

                if pricing == TRANSFER_FIXED:
                    return await self.async_step_fixed_transfer()

                if pricing == TRANSFER_SEASONAL:
                    return await self.async_step_seasonal_transfer()

                if pricing == TRANSFER_DAY_NIGHT:
                    return await self.async_step_day_night_transfer()

                return self.async_create_entry(
                    title=user_input[SECTION_BATTERY_SETTINGS][CONF_NAME], 
                    data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(SECTION_API_SETTINGS): section(
                    vol.Schema({
                        vol.Required(CONF_URL, default=DEFAULT_URL): str,
                        vol.Required(CONF_API_KEY): str,
                        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                        )
                    }),
                    {"collapsed": False}
                ),
                vol.Required(SECTION_BATTERY_SETTINGS): section(
                    vol.Schema({
                        vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                        vol.Required(CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY): vol.All(
                            vol.Coerce(float), vol.Range(min=MIN_BATTERY_CAPACITY, max=MAX_BATTERY_CAPACITY)
                        ),
                        vol.Required(CONF_POWER_UNIT, default=DEFAULT_POWER_UNIT): vol.In([UNIT_W, UNIT_KW])
                    }),
                    {"collapsed": False}
                ),
                vol.Required(SECTION_CURRENCY_SETTINGS): section(
                    vol.Schema({
                        vol.Optional(CONF_ADD_TAX, default=DEFAULT_ADD_TAX): bool,
                        vol.Optional(CONF_TAX_PERCENTAGE, default=DEFAULT_TAX_PERCENTAGE): vol.All(
                            vol.Coerce(float), vol.Range(min=0, max=30)
                        ),
                        vol.Required(
                            CONF_TRANSFER_PRICING,
                            default=DEFAULT_TRANSFER_PRICING,
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    {"value": TRANSFER_IGNORE, "label": TRANSFER_IGNORE},
                                    {"value": TRANSFER_FIXED, "label": TRANSFER_FIXED},
                                    {"value": TRANSFER_SEASONAL, "label": TRANSFER_SEASONAL},
                                    {"value": TRANSFER_DAY_NIGHT, "label": TRANSFER_DAY_NIGHT},
                                ],
                                translation_key="transfer_pricing",
                            )
                        )
                    }),
                    {"collapsed": True}
                ),
            }),
            errors=errors,
        )   
        
class ElisaKotiakkuOptionsFlow(config_entries.OptionsFlow, ElisaKotiakkuCommonSteps):
    """Handle options flow for Elisa Kotiakku."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        errors = {}
        
        conf = self.config_entry

        if user_input is not None:
            # VALIDATION STEP: Check if the token/URL works
            error = await validate_api_key(self.hass, user_input)

            if error:
                errors["base"] = error
            else:
                pricing = user_input[SECTION_CURRENCY_SETTINGS][CONF_TRANSFER_PRICING]

                self._base_config = user_input

                if pricing == TRANSFER_FIXED:
                    return await self.async_step_fixed_transfer()

                if pricing == TRANSFER_SEASONAL:
                    return await self.async_step_seasonal_transfer()

                if pricing == TRANSFER_DAY_NIGHT:
                    return await self.async_step_day_night_transfer()

                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required(SECTION_API_SETTINGS): section(
                    vol.Schema({
                        vol.Required(CONF_URL, default=str(get_config_parameter(conf, SECTION_API_SETTINGS, CONF_URL, DEFAULT_URL))): str,
                        vol.Required(CONF_API_KEY, default=str(get_config_parameter(conf, SECTION_API_SETTINGS, CONF_API_KEY, ""))): str,
                        vol.Optional(CONF_SCAN_INTERVAL, default=str(get_config_parameter(conf, SECTION_API_SETTINGS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))): vol.All(
                            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL)
                        )
                    }),
                    {"collapsed": False}
                ),
                vol.Required(SECTION_BATTERY_SETTINGS): section(
                    vol.Schema({
                        vol.Required(CONF_BATTERY_CAPACITY, default=str(get_config_parameter(conf, SECTION_BATTERY_SETTINGS, CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY))): vol.All(
                            vol.Coerce(float), vol.Range(min=MIN_BATTERY_CAPACITY, max=MAX_BATTERY_CAPACITY)
                        )                    }),
                    {"collapsed": False}
                ),
                vol.Required(SECTION_CURRENCY_SETTINGS): section(
                    vol.Schema({
                        vol.Optional(CONF_ADD_TAX, default=bool(get_config_parameter(conf, SECTION_CURRENCY_SETTINGS, CONF_ADD_TAX, DEFAULT_ADD_TAX))): bool,
                        vol.Optional(CONF_TAX_PERCENTAGE, default=str(get_config_parameter(conf, SECTION_CURRENCY_SETTINGS, CONF_TAX_PERCENTAGE, DEFAULT_TAX_PERCENTAGE))): vol.All(
                            vol.Coerce(float), vol.Range(min=0, max=30)
                        ),
                        vol.Required(
                            CONF_TRANSFER_PRICING,
                            default=str(get_config_parameter(conf, SECTION_CURRENCY_SETTINGS, CONF_TRANSFER_PRICING, DEFAULT_TRANSFER_PRICING)),
                        ): selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[
                                    {"value": TRANSFER_IGNORE, "label": TRANSFER_IGNORE},
                                    {"value": TRANSFER_FIXED, "label": TRANSFER_FIXED},
                                    {"value": TRANSFER_SEASONAL, "label": TRANSFER_SEASONAL},
                                    {"value": TRANSFER_DAY_NIGHT, "label": TRANSFER_DAY_NIGHT},
                                ],
                                translation_key="transfer_pricing",
                            )
                        )
                    }),
                    {"collapsed": True}
                ),
            }),
            errors=errors,
        )
        

        
    