"""Tests for Elisa Kotiakku config flow.

This module tests the setup, validation, and options flows for the 
Elisa Kotiakku custom integration, ensuring users can configure 
their battery devices correctly.
"""

from unittest.mock import patch
from aioresponses import aioresponses

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.elisa_kotiakku.config_flow import validate_input
from custom_components.elisa_kotiakku.const import (
    DOMAIN, 
    CONF_POWER_UNIT, 
    UNIT_W, 
    UNIT_KW,
    CONF_SCAN_INTERVAL,
    CONF_API_KEY,
    CONF_URL
)

# --- Config Flow Tests ---

async def test_flow_user_init(hass: HomeAssistant):
    """Test the initial user step form presentation.
    
    Verifies that the integration starts with the 'user' step when 
    manually added via the UI.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

async def test_flow_user_success(hass: HomeAssistant):
    """Test successful configuration flow completion.
    
    Verifies that valid user input results in a successful entry creation
    with the correct data and options preserved.
    """
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Patch validation to simulate a successful connection check
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
                CONF_POWER_UNIT: UNIT_W,
                "scan_interval": 300,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Battery"
    assert result2["data"][CONF_POWER_UNIT] == UNIT_W

async def test_flow_user_invalid_auth(hass: HomeAssistant):
    """Test flow behavior when API key validation fails.
    
    Ensures that the user is returned to the form with the appropriate 
    error message when authentication is rejected.
    """
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
                CONF_POWER_UNIT: UNIT_KW,
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"

# --- Input Validation Tests ---

async def test_validate_input_success(hass: HomeAssistant):
    """Test the internal validate_input function with successful API response."""
    data = {CONF_API_KEY: "valid_key", CONF_URL: "https://api.elisa.fi/battery"}
    
    with aioresponses() as mock:
        mock.get(data[CONF_URL], status=200)
        result = await validate_input(hass, data)
        assert result is None

async def test_validate_input_invalid_auth(hass: HomeAssistant):
    """Test validation failure when receiving a 401 Unauthorized status."""
    data = {CONF_API_KEY: "wrong_key", CONF_URL: "https://api.elisa.fi/battery"}
    
    with aioresponses() as mock:
        mock.get(data[CONF_URL], status=401)
        result = await validate_input(hass, data)
        assert result == "invalid_auth"

async def test_validate_input_cannot_connect(hass: HomeAssistant):
    """Test validation failure when the server is unreachable or errors out."""
    data = {CONF_API_KEY: "any_key", CONF_URL: "https://api.elisa.fi/battery"}
    
    with aioresponses() as mock:
        # Simulate a generic server-side error (500)
        mock.get(data[CONF_URL], status=500)
        result = await validate_input(hass, data)
        assert result == "cannot_connect"