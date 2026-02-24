"""DataUpdateCoordinator for Elisa Kotiakku."""

import logging
from datetime import timedelta
import aiohttp

from homeassistant.core import HomeAssistant

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_API_KEY, CONF_URL, DEFAULT_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class KotiakkuDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Elisa Kotiakku API."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize the coordinator."""
        self.entry = entry
        self.api_url = entry.data[CONF_URL]
        self.api_key = entry.data[CONF_API_KEY]
        
        # Pull scan interval from config or use default
        scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint.
        
        This is the core method that HA calls automatically based on 
        the update_interval.
        """
        headers = {"X-API-KEY": self.api_key}
        
        try:
            # We use the hass-provided helper for aiohttp sessions
            session = async_get_clientsession(self.hass)
            
            async with session.get(self.api_url, headers=headers, timeout=10) as response:
                if response.status == 401:
                    raise UpdateFailed("Invalid API Key - Authentication failed")
                
                response.raise_for_status()
                data = await response.json()
                
                _LOGGER.debug("Kotiakku data received: %s", data)
                
                return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err