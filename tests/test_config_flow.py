"""Tests for Elisa Kotiakku config flow."""
import aiohttp
from unittest.mock import patch
from aioresponses import aioresponses
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.elisa_kotiakku.config_flow import validate
from custom_components.elisa_kotiakku.config_flow import ElisaKotiakkuConfigFlow
from custom_components.elisa_kotiakku.const import (
    DOMAIN, 
    CONF_POWER_UNIT, 
    UNIT_W, 
    UNIT_KW,
    CONF_SCAN_INTERVAL,
    CONF_API_KEY,
    CONF_URL,
    SECTION_API_SETTINGS,
    SECTION_BATTERY_SETTINGS,
    SECTION_CURRENCY_SETTINGS,
    CONF_TRANSFER_PRICING,
    TRANSFER_IGNORE,
    TRANSFER_FIXED, 
    TRANSFER_DAY_NIGHT, 
    TRANSFER_SEASONAL
)

# --- Config Flow Tests ---

async def test_flow_user_init(hass: HomeAssistant):
    """Test the initial user step form presentation."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"

async def test_flow_user_success(hass: HomeAssistant):
    """Test successful configuration flow completion."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Patch validate to simulate successful API check
    with patch(
        "custom_components.elisa_kotiakku.config_flow.validate",
        return_value=None,
    ):
        user_input = {
            SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_W},
            SECTION_API_SETTINGS: {CONF_URL: "http://test/api", CONF_API_KEY: "valid_key"},
            SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
        }
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input,
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Battery"
    assert result2["data"][SECTION_BATTERY_SETTINGS][CONF_POWER_UNIT] == UNIT_W

async def test_flow_user_invalid_auth(hass: HomeAssistant):
    """Test flow behavior when API key validation fails."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    # Patch validate to simulate invalid auth
    with patch(
        "custom_components.elisa_kotiakku.config_flow.validate",
        return_value="invalid_auth",
    ):
        user_input = {
            SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_KW},
            SECTION_API_SETTINGS: {CONF_URL: "http://test/api", CONF_API_KEY: "bad_key"},
            SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
        }
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input,
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_auth"

# --- Input Validation Tests ---

async def test_validate_input_success(hass: HomeAssistant):
    """Test validate function with a 200 OK API response."""
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "valid_key", CONF_URL: "http://127.0.0.1/api"},
        SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }
    with aioresponses() as mock:
        mock.get(data[SECTION_API_SETTINGS][CONF_URL], status=200)
        result = await validate(hass, [], data)
        assert result is None

async def test_validate_input_invalid_auth(hass: HomeAssistant):
    """Test validate function when API returns 401 Unauthorized."""
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "bad_key", CONF_URL: "http://127.0.0.1/api"},
        SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }
    with aioresponses() as mock:
        mock.get(data[SECTION_API_SETTINGS][CONF_URL], status=401)
        result = await validate(hass, [], data)
        assert result == "invalid_auth"

async def test_validate_input_cannot_connect(hass: HomeAssistant):
    """Test validate function when API returns 500."""
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "any_key", CONF_URL: "http://127.0.0.1/api"},
        SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }
    with aioresponses() as mock:
        mock.get(data[SECTION_API_SETTINGS][CONF_URL], status=500)
        result = await validate(hass, [], data)
        assert result == "cannot_connect"
        
async def test_validate_device_already_configured(hass: HomeAssistant):
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "key1", CONF_URL: "http://api"},
        SECTION_BATTERY_SETTINGS: {"name": "Existing Device", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }

    with patch("custom_components.elisa_kotiakku.config_flow.async_get_device_registry") as mock_registry, \
         patch("custom_components.elisa_kotiakku.config_flow.async_get_clientsession") as mock_session:

        # Fake existing device with correct name attribute
        mock_device = MagicMock()
        mock_device.name = "Existing Device"
        mock_registry.return_value.devices = {"1": mock_device}

        # Fake HTTP session (to avoid real network)
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="")

        mock_get = AsyncMock()
        mock_get.__aenter__.return_value = mock_response
        mock_get.__aexit__.return_value = None
        mock_session.return_value.get = MagicMock(return_value=mock_get)

        result = await validate(hass, [], data)
        assert result == "device_already_configured"
        
async def test_validate_api_already_configured(hass: HomeAssistant):
    """Test validation fails if API key already exists in another entry."""
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "dup_key", CONF_URL: "http://api"},
        SECTION_BATTERY_SETTINGS: {"name": "New Device", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }

    # Simulate existing entry using same API key
    class DummyEntry:
        entry_id = "abc"
        data = {}
    existing_entry = DummyEntry()
    with patch("custom_components.elisa_kotiakku.config_flow.get_config_parameter", return_value="dup_key"):
        result = await validate(hass, [existing_entry], data)
        assert result == "api_already_configured"
  
from homeassistant.config_entries import SOURCE_USER
        
async def test_transfer_pricing_steps(hass: HomeAssistant):
    """Test that different transfer pricing flows are triggered."""
    fake_entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Battery1",
        data={SECTION_CURRENCY_SETTINGS: {}},
        options={},
        entry_id="fake",
        discovery_keys=set(),
        minor_version=1,
        source=SOURCE_USER,
        subentries_data=[],
        unique_id="fake_unique",
    )

    flow = ElisaKotiakkuConfigFlow()
    flow.hass = hass
    flow.config_entry = fake_entry

    base_input = {
        SECTION_API_SETTINGS: {CONF_URL: "http://api", CONF_API_KEY: "key"},
        SECTION_BATTERY_SETTINGS: {"name": "Battery1", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: None},
    }

    with patch("custom_components.elisa_kotiakku.config_flow.validate", return_value=None):
        # Fixed
        base_input[SECTION_CURRENCY_SETTINGS][CONF_TRANSFER_PRICING] = TRANSFER_FIXED
        result = await flow.async_step_user(base_input)
        assert result["step_id"] == "fixed_transfer"

        # Day/Night
        base_input[SECTION_CURRENCY_SETTINGS][CONF_TRANSFER_PRICING] = TRANSFER_DAY_NIGHT
        result = await flow.async_step_user(base_input)
        assert result["step_id"] == "day_night_transfer"

        # Seasonal
        base_input[SECTION_CURRENCY_SETTINGS][CONF_TRANSFER_PRICING] = TRANSFER_SEASONAL
        result = await flow.async_step_user(base_input)
        assert result["step_id"] == "seasonal_transfer"

async def test_validate_connection_error(hass: HomeAssistant):
    data = {
        SECTION_API_SETTINGS: {CONF_API_KEY: "key", CONF_URL: "http://badhost"},
        SECTION_BATTERY_SETTINGS: {"name": "Test Battery", CONF_POWER_UNIT: UNIT_W},
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_IGNORE},
    }

    with patch("custom_components.elisa_kotiakku.config_flow.async_get_clientsession") as mock_session:
        # Mock session.get to raise a generic OSError
        async def raise_oserror(*args, **kwargs):
            raise OSError("Connection refused")

        mock_session.return_value.get = AsyncMock(side_effect=raise_oserror)
        result = await validate(hass, [], data)
        assert result == "cannot_connect"
        
import pytest
from unittest.mock import patch, MagicMock
from homeassistant.config_entries import ConfigEntry
from custom_components.elisa_kotiakku.config_flow import ElisaKotiakkuConfigFlow
from custom_components.elisa_kotiakku.const import (
    DOMAIN,
    SECTION_BATTERY_SETTINGS,
    SECTION_API_SETTINGS,
    SECTION_CURRENCY_SETTINGS,
    CONF_POWER_UNIT,
    UNIT_W,
    CONF_API_KEY,
    CONF_URL,
    CONF_TRANSFER_PRICING,
    TRANSFER_IGNORE,
    TRANSFER_FIXED,
    TRANSFER_SEASONAL,
    TRANSFER_DAY_NIGHT,
)

