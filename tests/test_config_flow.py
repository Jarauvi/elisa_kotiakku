"""Tests for Elisa Kotiakku config flow."""
from unittest.mock import patch
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.elisa_kotiakku.const import DOMAIN

async def test_flow_user_init(hass: HomeAssistant):
    """Test the initial user step form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

async def test_flow_user_success(hass: HomeAssistant):
    """Test successful configuration flow."""
    # 1. Initialize the flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # 2. Mock a successful API response (status 200)
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
                "scan_interval": 120,
            },
        )
        await hass.async_block_till_done()

    # 3. Verify the entry was created
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Battery"
    assert result2["data"]["api_key"] == "valid_key"

async def test_flow_user_invalid_auth(hass: HomeAssistant):
    """Test flow when API key is incorrect."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Mock validation returning an auth error
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
            },
        )

    # Verify form is shown again with errors
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"

async def test_options_flow(hass: HomeAssistant, mock_config_entry):
    """Test updating options (scan interval)."""
    mock_config_entry.add_to_hass(hass)

    # 1. Start the options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # 2. Change the scan interval
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={"scan_interval": 200},
    )

    # 3. Verify it saved
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options.get("scan_interval") == 200