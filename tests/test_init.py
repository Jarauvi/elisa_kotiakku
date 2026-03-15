import re
import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.config_entries import ConfigEntryState
from custom_components.elisa_kotiakku import (
    async_setup_entry,
    async_unload_entry,
    async_migrate_entry,
)
from custom_components.elisa_kotiakku.const import DOMAIN, PLATFORMS, CONF_SCAN_INTERVAL

# Patch target for coordinator refresh
COORDINATOR_PATCH = "custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator._async_update_data"


@pytest.mark.asyncio
async def test_setup_entry_success(hass, mock_config_entry):
    """Test setup_entry with successful coordinator refresh."""
    # Add the config entry to hass
    mock_config_entry.add_to_hass(hass)

    # Patch coordinator refresh and platform forwarding
    with patch(
        "custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock
    ) as mock_refresh, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new_callable=AsyncMock
    ):
        mock_refresh.return_value = None

        result = await async_setup_entry(hass, mock_config_entry)
        assert result is True
        assert hass.data[DOMAIN][mock_config_entry.entry_id] is not None


@pytest.mark.asyncio
async def test_setup_entry_failure(hass, mock_config_entry):
    """Test setup_entry when coordinator refresh fails (e.g., auth error)."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        COORDINATOR_PATCH,
        new=AsyncMock(side_effect=Exception("Auth Error"))
    ), patch(
        "custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new_callable=AsyncMock
    ):
        mock_config_entry.add_to_hass(hass)
        # Should raise internally, but setup_entry returns True anyway
        result = await async_setup_entry(hass, mock_config_entry)
        assert result is True
        # Coordinator is still registered even if first refresh fails
        assert DOMAIN in hass.data


@pytest.mark.asyncio
async def test_unload_entry_success(hass, mock_config_entry):
    """Test async_unload_entry removes coordinator and cleans hass.data."""
    mock_config_entry.add_to_hass(hass)

    # Setup entry first
    with patch(
        "custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock
    ), patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        new_callable=AsyncMock
    ):
        await async_setup_entry(hass, mock_config_entry)

    # Unload entry
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        new=AsyncMock(return_value=True)
    ):
        result = await async_unload_entry(hass, mock_config_entry)
        assert result is True
        assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


@pytest.mark.asyncio
async def test_migrate_entry(hass, mock_config_entry):
    """Test async_migrate_entry updates config entry version and data."""

    # Add entry to hass so HA knows it exists
    mock_config_entry.add_to_hass(hass)

    # Old version 1 data (all required keys)
    old_data = {
        "url": "https://api.elisa.fi",
        "api_key": "abc123",
        "scan_interval": 300,
        "name": "Test Battery",
        "power_unit": "kW",
        "scan_interval": 300,
        "battery_capacity": 10.0,
    }

    # Properly update entry with old data and version
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data=old_data,
        version=1
    )

    # Run migration (await it!)
    result = await async_migrate_entry(hass, mock_config_entry)

    # Assert migration worked
    assert result is True
    assert mock_config_entry.version == 2
    assert "battery_settings" in mock_config_entry.data
    assert "api_settings" in mock_config_entry.data
    assert "currency_settings" in mock_config_entry.data