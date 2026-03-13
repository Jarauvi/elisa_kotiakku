import pytest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    UnitOfEnergy, 
    UnitOfPower, 
    PERCENTAGE
)
from homeassistant.util import dt as dt_util
from homeassistant.helpers import entity_registry as er

from custom_components.elisa_kotiakku.sensor import (
    KotiakkuEnergySensor,
    KotiakkuPowerSensor,
    KotiakkuBatterySensor,
    KotiakkuBatteryStateSensor,
    KotiakkuCycleCounterSensor,
    KotiakkuTimeTargetSensor,
    KotiakkuNetSavingsRateSensor,
    KotiakkuEfficiencySensor,
    KotiakkuTotalSavingsSensor
)

@pytest.mark.parametrize(
    "sensor_class, key, expected_unit, expected_device_class, expected_state_class",
    [
        (KotiakkuEnergySensor, "solar_energy_kwh", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        (KotiakkuPowerSensor, "solar_power_kw", None, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        (KotiakkuBatterySensor, "state_of_charge_percent", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    ],
)
async def test_sensor_metadata(
    hass, mock_coordinator, mock_config_entry, 
    sensor_class, key, expected_unit, expected_device_class, expected_state_class
):
    """Test that all sensor types have the correct metadata and classes."""
    if sensor_class == KotiakkuEnergySensor:
        sensor = sensor_class(mock_coordinator, key, "solar_power_kw", "Test", "test", mock_config_entry)
    else:
        sensor = sensor_class(mock_coordinator, key, "Test", "test", mock_config_entry)

    assert sensor.device_class == expected_device_class
    assert sensor.state_class == expected_state_class
    if expected_unit:
        assert sensor.native_unit_of_measurement == expected_unit

async def test_battery_state_logic(hass, mock_coordinator, mock_config_entry):
    """Test battery state logic (charging/discharging/idle) based on power."""
    sensor = KotiakkuBatteryStateSensor(mock_coordinator, "battery_state", "Test", "test", mock_config_entry)
    
    # Test Charging (Negative power)
    mock_coordinator.data = {"battery_power_kw": -0.5}
    assert sensor.native_value == "charging"
    
    # Test Discharging (Positive power)
    mock_coordinator.data = {"battery_power_kw": 0.5}
    assert sensor.native_value == "discharging"
    
    # Test Idle (Within 50W deadzone)
    mock_coordinator.data = {"battery_power_kw": 0.02}
    assert sensor.native_value == "idle"

async def test_cycle_counter_math(hass, mock_coordinator, mock_config_entry):
    """Test cycle count calculation using Registry lookup."""
    registry = er.async_get(hass)
    entry_id = mock_config_entry.entry_id
    
    # Mock the source discharge energy sensor
    registry.async_get_or_create(
        "sensor", "elisa_kotiakku", f"{entry_id}_total_battery_discharge_kwh",
        suggested_object_id="test_total_battery_discharge_kwh"
    )
    hass.states.async_set("sensor.test_total_battery_discharge_kwh", "25.0")

    # 10kWh capacity
    sensor = KotiakkuCycleCounterSensor(
        mock_coordinator, "battery_cycle_count", "total_battery_discharge_kwh", 10.0, "Test", "test", mock_config_entry
    )
    sensor.hass = hass
    sensor._entry_id = entry_id # Match the manual ID setup in your sensor.py

    # 25kWh / 10kWh = 2 cycles (it returns int)
    assert sensor.native_value == 2

async def test_efficiency_clamping(hass, mock_coordinator, mock_config_entry):
    """Test efficiency calculation and 100% clamping."""
    registry = er.async_get(hass)
    entry_id = mock_config_entry.entry_id
    
    registry.async_get_or_create("sensor", "elisa_kotiakku", f"{entry_id}_charge", suggested_object_id="t_charge")
    registry.async_get_or_create("sensor", "elisa_kotiakku", f"{entry_id}_discharge", suggested_object_id="t_discharge")

    sensor = KotiakkuEfficiencySensor(mock_coordinator, "eff", "discharge", "charge", "Test", "test", mock_config_entry)
    sensor.hass = hass

    # Scenario: 11kWh discharged for 10kWh charged (Impossible 110%)
    hass.states.async_set("sensor.t_charge", "10.0")
    hass.states.async_set("sensor.t_discharge", "11.0")

    assert sensor.native_value == 100.0

async def test_energy_sensor_riemann_sum(hass, mock_coordinator, mock_config_entry, freezer):
    """Test energy accumulation (Power * Time)."""
    now = dt_util.utcnow()
    freezer.move_to(now)
    
    mock_coordinator.data = {"solar_power_kw": 2.0}
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "solar_energy_kwh", "solar_power_kw", "Test", "test", mock_config_entry
    )
    sensor.hass = hass
    sensor.platform = MagicMock()  # <--- Add this line to bypass the ValueError
    sensor._restored = True
    sensor._state = 10.0
    sensor._last_run = now

    # Move 30 mins (0.5h) -> 10.0 + (2kW * 0.5h) = 11.0
    future = now + timedelta(minutes=30)
    freezer.move_to(future)
    
    sensor._handle_coordinator_update()

    assert sensor.native_value == 11.0
    
async def test_total_savings_riemann_sum(hass, mock_coordinator, mock_config_entry, freezer):
    """Test currency accumulation (Savings Rate * Time)."""
    now = dt_util.utcnow()
    freezer.move_to(now)
    
    # 2.0 €/h savings rate
    mock_coordinator.data = {"net_savings_rate": 2.0}
    
    sensor = KotiakkuTotalSavingsSensor(
        mock_coordinator, "total_savings_eur", "net_savings_rate", "Test", "test", mock_config_entry
    )
    sensor.hass = hass
    sensor.platform = MagicMock()  # <--- Add this line to bypass the ValueError
    sensor._restored = True
    sensor._state = 5.0
    sensor._last_run = now

    # Move 1 hour -> 5.0 + (2.0€/h * 1h) = 7.0
    future = now + timedelta(hours=1)
    freezer.move_to(future)
    
    sensor._handle_coordinator_update()

    assert sensor.native_value == 7.0

async def test_power_sensor_display_passthrough(hass, mock_coordinator, mock_config_entry):
    """Test that power sensors show the coordinator's prepared display value."""
    # Your code looks for 'key_display' in coordinator data
    mock_coordinator.data = {"solar_power_kw_display": 1234}
    
    sensor = KotiakkuPowerSensor(
        mock_coordinator, "solar_power_kw", "Test", "test", mock_config_entry
    )
    
    assert sensor.native_value == 1234