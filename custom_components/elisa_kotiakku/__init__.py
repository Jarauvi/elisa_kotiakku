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
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS, CONF_API_KEY, CONF_URL, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL

# Define the logger for this integration using the module name
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry):
    """Set up Elisa Kotiakku from a config entry (UI setup)."""
    
    # Retrieve the polling interval from user config, defaulting to 300s if not set
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

    # Use a persistent session for API calls
    # Note: In a production version, it's recommended to use hass.helpers.aiohttp_client.async_get_clientsession(hass)
    session = aiohttp.ClientSession()
    
    async def async_get_data():
        """
        Fetch data from the Elisa API.
        This internal function is called by the Coordinator at every update_interval.
        """
        headers = {"X-API-KEY": entry.data[CONF_API_KEY]}
        try:
            # Fetch data with a 10-second timeout to prevent hanging the event loop
            async with session.get(entry.data[CONF_URL], headers=headers, timeout=10) as response:
                if response.status == 401:
                    # Specific error for authentication issues (triggers a re-auth flow in HA)
                    raise UpdateFailed("Invalid authentication")
                
                # Check for other HTTP errors (4xx or 5xx)
                response.raise_for_status()
                
                # Parse and return the JSON payload to the coordinator's .data property
                return await response.json()
        except Exception as err:
            # Catch network errors and log them as UpdateFailed to inform the UI
            raise UpdateFailed(f"Error communicating with API: {err}")

    # Initialize the DataUpdateCoordinator.
    # This centralizes data fetching so that 20+ sensors don't all hit the API at once.
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Kotiakku Coordinator",
        update_method=async_get_data,
        update_interval=timedelta(seconds=scan_interval),
    )

    # Perform the very first refresh. This blocks setup until data is received 
    # or it fails, ensuring entities aren't 'unknown' on boot.
    await coordinator.async_config_entry_first_refresh()
    
    # Store the coordinator in hass.data so sensor.py can access it via entry_id
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to the sensor platform (calls async_setup_entry in sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    # Register a listener to handle options changes (like changing the scan interval)
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

async def update_listener(hass, entry):
    """
    Handle configuration options updates.
    Reloads the entire integration when the user saves new settings.
    """
    await hass.config_entries.async_reload(entry.entry_id)