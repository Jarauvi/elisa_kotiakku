import re
import pytest
from aioresponses import aioresponses
from homeassistant.config_entries import ConfigEntryState
from custom_components.elisa_kotiakku.const import DOMAIN

async def test_coordinator_update_success(hass, mock_config_entry):
    """Test successful data update."""
    mock_config_entry.add_to_hass(hass)
    
    with aioresponses() as m:
        # 1. Mock the API call that happens DURING setup
        m.get(re.compile(r".*"), status=200, payload={"soc": 85, "battery_power_kw": 1.2})

        # 2. Setup the entry and wait for it to finish
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # 3. Verify it loaded correctly
        assert mock_config_entry.state is ConfigEntryState.LOADED
        
        # 4. Check the data
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.data["soc"] == 85

    # 5. Mandatory Cleanup to prevent "Unclosed client session"
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

async def test_coordinator_update_auth_failure(hass, mock_config_entry):
    """Test coordinator handles auth error."""
    mock_config_entry.add_to_hass(hass)
    
    with aioresponses() as m:
        # Mock 401 response for the initial setup check
        m.get(re.compile(r".*"), status=401, body="Invalid API Key")

        # Setup will now fail or trigger auth error logic
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # In HA, if setup fails due to auth, the state should reflect that
        assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR or \
               not hass.data.get(DOMAIN)

    # Cleanup
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()