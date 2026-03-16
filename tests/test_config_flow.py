"""Tests for Elisa Kotiakku config flow."""
import aiohttp
import pytest
from unittest.mock import patch
from aioresponses import aioresponses
from homeassistant.config_entries import ConfigEntry
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.elisa_kotiakku.config_flow import validate
from custom_components.elisa_kotiakku.config_flow import ElisaKotiakkuConfigFlow, ElisaKotiakkuOptionsFlow
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
    TRANSFER_SEASONAL,
    CONF_BATTERY_CAPACITY
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
        
# Test async_get_options_flow returns an instance
@pytest.mark.asyncio
async def test_async_get_options_flow_returns_instance():
    flow = ElisaKotiakkuConfigFlow()
    options_flow = flow.async_get_options_flow(None)
    assert isinstance(options_flow, ElisaKotiakkuOptionsFlow)

# Test fixed transfer step with user_input creates entry
@pytest.mark.asyncio
async def test_async_step_fixed_transfer_creates_entry(hass):
    flow = ElisaKotiakkuConfigFlow()
    flow.hass = hass
    flow._base_config = {"currency_settings": {}}
    user_input = {"fixed_transfer_price": 1.23}

    result = await flow.async_step_fixed_transfer(user_input=user_input)
    assert result["type"] == "create_entry"
    assert result["data"]["currency_settings"]["fixed_transfer_price"] == 1.23

# Test day/night transfer step with user_input creates entry
@pytest.mark.asyncio
async def test_async_step_day_night_transfer_creates_entry(hass):
    flow = ElisaKotiakkuConfigFlow()
    flow.hass = hass
    flow._base_config = {"currency_settings": {}}
    user_input = {"day_price": 1.11, "night_price": 0.99}

    result = await flow.async_step_day_night_transfer(user_input=user_input)
    assert result["type"] == "create_entry"
    assert result["data"]["currency_settings"]["day_price"] == 1.11
    assert result["data"]["currency_settings"]["night_price"] == 0.99

# Test seasonal transfer step with user_input creates entry
@pytest.mark.asyncio
async def test_async_step_seasonal_transfer_creates_entry(hass):
    flow = ElisaKotiakkuConfigFlow()
    flow.hass = hass
    flow._base_config = {"currency_settings": {}}
    user_input = {"winter_day_price": 2.0, "other_price": 1.5}

    result = await flow.async_step_seasonal_transfer(user_input=user_input)
    assert result["type"] == "create_entry"
    assert result["data"]["currency_settings"]["winter_day_price"] == 2.0
    assert result["data"]["currency_settings"]["other_price"] == 1.5

# Test OptionsFlow returns error if validate fails
@pytest.mark.asyncio

@pytest.mark.asyncio
async def test_options_flow_validate_error(hass):
    """OptionsFlow returns a form with an error if validate fails."""

    # 1️⃣ Create a ConfigEntry
    entry = ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="Test",
        data={},
        options={},
        entry_id="id123",
        discovery_keys=set(),
        minor_version=1,
        source="user",
        subentries_data=[],
        unique_id="uid123",
    )

    # 2️⃣ Register the entry using the HA API (await the coroutine!)
    await hass.config_entries.async_add(entry)
    await hass.async_block_till_done()

    # 3️⃣ Start the options flow for this entry
    flow_result = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = flow_result["flow_id"]

    user_input = {
        SECTION_CURRENCY_SETTINGS: {CONF_TRANSFER_PRICING: TRANSFER_FIXED},
        SECTION_API_SETTINGS: {CONF_URL: "https://example.com", CONF_API_KEY: "dummy"},
        SECTION_API_SETTINGS: {CONF_SCAN_INTERVAL: 300},
        SECTION_BATTERY_SETTINGS: {CONF_BATTERY_CAPACITY: 20.0}
    }

    # 4️⃣ Patch validate to simulate validation error
    with patch(
        "custom_components.elisa_kotiakku.config_flow.validate",
        return_value="api_already_configured",
    ):
        result = await hass.config_entries.options.async_configure(flow_id, user_input)

    # 5️⃣ Assert the flow returns a form with the expected error
    assert result["type"] == "form"
    assert result["errors"]["base"] == "api_already_configured"