import re
import pytest
from aioresponses import aioresponses
from unittest.mock import patch, MagicMock
from homeassistant.config_entries import ConfigEntryState
from custom_components.elisa_kotiakku.const import DOMAIN

PATCH_TARGET = "custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator._async_update_data"

async def test_setup_entry_success(hass, mock_config_entry):
    """Test successful setup by mocking the network response."""
    mock_config_entry.add_to_hass(hass)
    
    # aioresponses intercepts any call made via aiohttp (even from HA's shared session)
    with aioresponses() as m:
        # We use a regex to match any URL so we don't have to worry about the exact string
        m.get(re.compile(r".*"), status=200, payload={
            "battery_power_kw": 1.5, 
            "soc": 85,
            "solar_power_kw": 2.0
        })

        # Trigger the setup
        result = await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify everything went green
        assert result is True
        assert mock_config_entry.state is ConfigEntryState.LOADED
        assert DOMAIN in hass.data
        
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.data["soc"] == 85

    # Crucial cleanup to close the session and avoid the "Unclosed client session" error
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

async def test_setup_entry_auth_failure(hass, mock_config_entry):
    from homeassistant.helpers.update_coordinator import UpdateFailed
    mock_config_entry.add_to_hass(hass)
    
    with patch(PATCH_TARGET, side_effect=UpdateFailed("Auth Error")):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
        
        # Check the state instead of a blind assert
        assert mock_config_entry.state in [ConfigEntryState.SETUP_ERROR, ConfigEntryState.SETUP_RETRY]

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()