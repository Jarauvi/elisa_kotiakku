"""
Setup and integration logic for Elisa Kotiakku.
This file initializes the integration and manages the DataUpdateCoordinator.
"""

import logging
import asyncio
from datetime import timedelta
import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import UpdateFailed
from .coordinator import KotiakkuDataUpdateCoordinator
from .const import (
    DOMAIN, 
    PLATFORMS,
    CONF_NAME, 
    CONF_API_KEY, 
    CONF_URL, 
    CONF_SCAN_INTERVAL,
    CONF_POWER_UNIT,
    CONF_BATTERY_CAPACITY, 
    CONF_ADD_VAT,
    CONF_VAT_PERCENTAGE,
    CONF_TRANSFER_PRICING,
    DEFAULT_ADD_VAT,
    DEFAULT_VAT_PERCENTAGE,
    DEFAULT_TRANSFER_PRICING,
    SECTION_BATTERY_SETTINGS,
    SECTION_API_SETTINGS,
    SECTION_CURRENCY_SETTINGS,
    DEFAULT_URL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_POWER_UNIT,
    DEFAULT_BATTERY_CAPACITY,
    TRANSFER_IGNORE
)

# Define the logger for this integration using the module name
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    """Set up Elisa Kotiakku from a config entry."""
    
    # Initialize the CUSTOM coordinator that has the list-unwrapping logic
    coordinator = KotiakkuDataUpdateCoordinator(hass, entry)
    device_slug = entry.data.get("device_slug", "kotiakku")
    
    # Fetch initial data before finishing setup
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forwarding to PLATFORMS (currently just ["sensor"])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.
    
    This is called when a user deletes the integration or disables it.
    It ensures all sensors are removed and background tasks are killed.
    """
    # 1. Tell all platforms (sensor, etc.) to remove their entities
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # 2. If platforms unloaded successfully, clean up our local data
    if unload_ok:
        # This removes the coordinator from memory
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        
        # If your coordinator or API client has a close method, call it here:
        # await coordinator.api.async_close_session()

    # 3. If there are no more entries for this domain, remove the domain key
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return unload_ok

async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entries."""
    _LOGGER.debug("Migrating config entry from version %s", config_entry.version)

    if config_entry.version == 1:
        new_data = {
            SECTION_API_SETTINGS: {
                CONF_URL: config_entry.data.get(CONF_URL, DEFAULT_URL),
                CONF_API_KEY: config_entry.data.get(CONF_API_KEY, ""),
                CONF_SCAN_INTERVAL: config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            },
            SECTION_BATTERY_SETTINGS: {
                CONF_NAME: config_entry.data.get(CONF_NAME, DEFAULT_NAME),
                CONF_POWER_UNIT: config_entry.data.get(CONF_POWER_UNIT, DEFAULT_POWER_UNIT),
                CONF_BATTERY_CAPACITY: config_entry.data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY),
            }
        }
        
        new_data.setdefault(SECTION_CURRENCY_SETTINGS, {})
        new_data[SECTION_CURRENCY_SETTINGS].setdefault(CONF_ADD_VAT, False)
        new_data[SECTION_CURRENCY_SETTINGS].setdefault(CONF_TRANSFER_PRICING, TRANSFER_IGNORE)
        new_data[SECTION_API_SETTINGS].setdefault(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        hass.config_entries.async_update_entry(
            config_entry,
            data=new_data,
            version=2,
        )

        _LOGGER.info("Migration to version 2 successful")

    return True

async def update_listener(hass, entry):
    """
    Handle configuration options updates.
    Reloads the entire integration when the user saves new settings.
    """
    await hass.config_entries.async_reload(entry.entry_id)