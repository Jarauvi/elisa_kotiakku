"""Tests for Elisa Kotiakku DataUpdateCoordinator.

This module ensures that data fetching logic is robust, handling both
successful API responses and various failure modes like authentication
issues and network timeouts.
"""

import re
import pytest
from aioresponses import aioresponses

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.elisa_kotiakku.config_flow import validate_input
from custom_components.elisa_kotiakku.coordinator import KotiakkuDataUpdateCoordinator
from custom_components.elisa_kotiakku.const import DOMAIN, CONF_API_KEY, CONF_URL

# --- Integration Level Coordinator Tests ---

async def test_coordinator_update_success(hass, mock_config_entry):
    """Test a successful data refresh cycle.
    
    Verifies that the coordinator correctly parses API JSON and stores 
    it in the coordinator.data attribute.
    """
    mock_config_entry.add_to_hass(hass)
    
    with aioresponses() as m:
        # Mock the API call that happens during async_setup_entry
        m.get(re.compile(r".*"), status=200, payload={"soc": 85, "battery_power_kw": 1.2})

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED
        
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.data["soc"] == 85

    # Cleanup to prevent lingering aiohttp sessions in tests
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

# --- Internal Method Unit Tests ---

async def test_coordinator_auth_failure(hass, mock_config_entry):
    """Test coordinator behavior when the API returns 401 Unauthorized.
    
    Ensures that Authentication errors are caught and re-raised as UpdateFailed
    with a clear descriptive message.
    """
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    
    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=401)
        
        with pytest.raises(UpdateFailed, match="Authentication failed"):
            await coordinator._async_update_data()

async def test_coordinator_network_error(hass, mock_config_entry):
    """Test coordinator behavior during server-side errors (500).
    
    Verifies that generic network or server issues trigger the appropriate
    communication error handling.
    """
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    
    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=500)
        
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()

# --- Validation Logic Tests ---

async def test_validate_input_success(hass):
    """Test that valid configuration input passes the connection check."""
    data = {CONF_API_KEY: "valid_key", CONF_URL: "https://api.elisa.fi/battery"}
    with aioresponses() as mock:
        mock.get(data[CONF_URL], status=200)
        result = await validate_input(hass, data)
        assert result is None

async def test_validate_input_invalid_auth(hass):
    """Test that validate_input identifies incorrect credentials."""
    data = {CONF_API_KEY: "wrong_key", CONF_URL: "https://api.elisa.fi/battery"}
    with aioresponses() as mock:
        mock.get(data[CONF_URL], status=401)
        result = await validate_input(hass, data)
        assert result == "invalid_auth"

async def test_validate_input_cannot_connect(hass):
    """Test that validate_input handles server timeouts or generic errors."""
    data = {CONF_API_KEY: "any_key", CONF_URL: "https://api.elisa.fi/battery"}
    with aioresponses() as mock:
        # 500 status triggers the 'cannot_connect' logic in config_flow.py
        mock.get(data[CONF_URL], status=500)
        result = await validate_input(hass, data)
        assert result == "cannot_connect"