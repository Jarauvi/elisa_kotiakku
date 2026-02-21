import re
import pytest
from aioresponses import aioresponses
from homeassistant.config_entries import ConfigEntryState
from custom_components.elisa_kotiakku.const import DOMAIN

async def test_unload_entry(hass, mock_config_entry):
    """Test successful unloading of a config entry."""
    mock_config_entry.add_to_hass(hass)
    
    # 1. Mock the API call so setup actually SUCCEEDS
    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload={
            "battery_power_kw": 0, 
            "soc": 100,
            "solar_power_kw": 0
        })

        # Now setup will return True
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED

        # 2. Unload the entry
        assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # 3. Verify final state
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    if DOMAIN in hass.data:
            assert mock_config_entry.entry_id not in hass.data[DOMAIN]