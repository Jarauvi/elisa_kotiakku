import pytest
from asyncio import Future
from unittest.mock import patch, MagicMock
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from datetime import timedelta
from homeassistant.components.recorder import DATA_INSTANCE
from custom_components.elisa_kotiakku.const import (
    DOMAIN, 
    SERVICE_SET_MAX_FROM_HISTORY, 
    SERVICE_RESET_SENSORS
)

@pytest.fixture
async def setup_integration(hass, mock_config_entry):
    """Set up the integration and its sensors for testing."""
    mock_config_entry.add_to_hass(hass)
    
    # You might need to mock the coordinator data here if sensors 
    # need initial values to avoid 'unknown' states
    with patch("custom_components.elisa_kotiakku.coordinator.KotiakkuDataUpdateCoordinator._async_update_data", return_value={}):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    return mock_config_entry

async def test_reset_sensors_service(hass, setup_integration):
    """Test the reset sensors service sets values to 0."""
    # Use a sensor name that your integration actually creates
    entity_id = "sensor.kotiakku_solar_energy_kwh"
    
    # Ensure the entity exists and has an initial state
    hass.states.async_set(entity_id, "15.5")

    # Get the device_id from the entity registry
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)
    assert entry is not None

    # Call the reset service
    await hass.services.async_call(
        DOMAIN,
        SERVICE_RESET_SENSORS,
        {"device_id": entry.device_id},
        blocking=True,
    )

    # Verify the state is now 0.0
    state = hass.states.get(entity_id)
    assert float(state.state) == 0.0

async def test_set_max_from_history_service(hass, setup_integration):
    """Test the history repair service restores the maximum value."""
    
    entity_id = "sensor.kotiakku_solar_energy_kwh"
    
    ent_reg = er.async_get(hass)
    entry = ent_reg.async_get(entity_id)

    # 1. Create a mock for the recorder instance
    mock_recorder = MagicMock()
    
    # 2. Manually inject it into hass.data so get_instance(hass) succeeds
    hass.data[DATA_INSTANCE] = mock_recorder

    # Mocking the Recorder's history output
    mock_state = MagicMock()
    mock_state.state = "42.0"
    
    mock_history = {
        entity_id: [mock_state]
    }
    
    mock_future = Future()
    mock_future.set_result(mock_history)

    # Patch the history call and the executor job runner
    with patch(
        "homeassistant.components.recorder.history.get_significant_states",
        return_value=mock_history,
    ), patch.object(
        mock_recorder, 
        "async_add_executor_job", 
        return_value=mock_future  # Must return an awaitable
    ):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_MAX_FROM_HISTORY,
            {"device_id": entry.device_id, "lookback_days": 1},
            blocking=True,
        )

    # Verify the state was updated
    state = hass.states.get(entity_id)
    assert float(state.state) == 42.0