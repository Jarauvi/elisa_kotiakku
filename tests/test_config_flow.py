"""Tests for Elisa Kotiakku config flow."""
from unittest.mock import patch
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.elisa_kotiakku.const import (
    DOMAIN, 
    CONF_POWER_UNIT, 
    UNIT_W, 
    UNIT_KW,
    CONF_SCAN_INTERVAL
)

async def test_flow_user_init(hass: HomeAssistant):
    """Test the initial user step form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

async def test_flow_user_success(hass: HomeAssistant):
    """Test successful configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.elisa_kotiakku.config_flow.validate_input",
        return_value=None,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Test Battery",
                "url": "http://127.0.0.1:8000/api/v1/status",
                "api_key": "valid_key",
                CONF_POWER_UNIT: UNIT_W,  # Added required field
                "scan_interval": 120,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Battery"
    assert result2["data"][CONF_POWER_UNIT] == UNIT_W

async def test_flow_user_invalid_auth(hass: HomeAssistant):
    """Test flow when API key is incorrect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.elisa_kotiakku.config_flow.validate_input",
        return_value="invalid_auth",
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Test Battery",
                "url": "http://127.0.0.1:8000/api/v1/status",
                "api_key": "wrong_key",
                CONF_POWER_UNIT: UNIT_KW, # Added required field
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"

async def test_options_flow_power_unit(hass: HomeAssistant, mock_config_entry):
    """Test updating options flow."""
    # 1. Add to hass
    mock_config_entry.add_to_hass(hass)

    # 2. Use 120 to satisfy the "value must be at least 120" rule
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            CONF_SCAN_INTERVAL: 120,
            CONF_POWER_UNIT: UNIT_KW
        }
    )

    # 3. Initialize the options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # 4. Submit the change (again, using 120)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_POWER_UNIT: UNIT_W,
            CONF_SCAN_INTERVAL: 120,
        },
    )

    # 5. Verify
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options.get(CONF_POWER_UNIT) == UNIT_W
    
    await hass.async_block_till_done()