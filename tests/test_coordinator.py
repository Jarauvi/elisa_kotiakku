"""Tests for Elisa Kotiakku DataUpdateCoordinator."""

import re
import pytest
from aioresponses import aioresponses

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.elisa_kotiakku.coordinator import KotiakkuDataUpdateCoordinator
from custom_components.elisa_kotiakku.const import (
    DOMAIN, 
    CONF_API_KEY, 
    CONF_URL, 
    CONF_POWER_UNIT, 
    CONF_BATTERY_CAPACITY
)

# --- Integration Level Coordinator Tests ---

async def test_coordinator_update_success(hass, mock_config_entry):
    """Test a successful data refresh cycle with the list-style response."""
    # 1. Add to registry first
    mock_config_entry.add_to_hass(hass)
    
    # 2. Now we can safely update it
    hass.config_entries.async_update_entry(
        mock_config_entry, 
        data={**mock_config_entry.data, CONF_POWER_UNIT: "W"}
    )
    
    payload = [{
        "state_of_charge_percent": 85,
        "battery_power_kw": 1.2,
        "solar_power_kw": 2.5,
        "grid_power_kw": -1.0,
        "house_power_kw": 0.3,
        "solar_to_battery_kw": 0.5,
        "grid_to_battery_kw": 0.7
    }]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        # 3. Setup the entry
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED
        
        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert coordinator.data["state_of_charge_percent"] == 85
        assert coordinator.data["battery_power_kw_display"] == 1200.0

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

# --- Internal Logic & Math Tests ---

async def test_coordinator_math_logic(hass, mock_config_entry):
    """Test internal calculations for efficiency and time-to-target."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={
            **mock_config_entry.data, 
            CONF_BATTERY_CAPACITY: 10.0,
            CONF_POWER_UNIT: "kW"
        }
    )
    
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    
    payload = [{
        "state_of_charge_percent": 50.0,
        "battery_power_kw": -2.0,  # Negative is charging
        "solar_to_battery_kw": 5.0,
        "grid_to_battery_kw": 0.0,
        "battery_to_house_kw": 0.0,
        "battery_to_grid_kw": 0.0,
        "spot_price_cents_per_kwh": 10.0
    }]

    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=200, payload=payload)
        data = await coordinator._async_update_data()

        assert data["battery_charge_efficiency"] == 40.0
        assert data["time_to_90_percent"] == "2h 0m"

async def test_coordinator_discharge_math(hass, mock_config_entry):
    """Test efficiency and time logic during discharge."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_BATTERY_CAPACITY: 10.0}
    )
    
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    
    payload = [{
        "state_of_charge_percent": 50.0,
        "battery_power_kw": 2.0,  # Positive is discharging
        "battery_to_house_kw": 1.8,
        "battery_to_grid_kw": 0.0,
        "solar_to_battery_kw": 0.0,
        "grid_to_battery_kw": 0.0
    }]

    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=200, payload=payload)
        data = await coordinator._async_update_data()

        assert data["battery_discharge_efficiency"] == 90.0
        assert data["time_to_15_percent"] == "1h 45m"

# --- Error Handling Tests ---

async def test_coordinator_auth_failure(hass, mock_config_entry):
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=401)
        with pytest.raises(UpdateFailed, match="Authentication failed"):
            await coordinator._async_update_data()

async def test_coordinator_empty_data(hass, mock_config_entry):
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=200, payload=[])
        with pytest.raises(UpdateFailed, match="API returned empty data"):
            await coordinator._async_update_data()

async def test_coordinator_network_error(hass, mock_config_entry):
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    with aioresponses() as m:
        m.get(mock_config_entry.data["url"], status=500)
        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()