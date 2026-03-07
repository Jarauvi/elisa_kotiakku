"""Tests for Elisa Kotiakku sensors."""

import pytest
from datetime import timedelta
from unittest.mock import MagicMock

from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    UnitOfEnergy, 
    UnitOfPower, 
    UnitOfTemperature, 
    PERCENTAGE
)
from homeassistant.util import dt as dt_util

from custom_components.elisa_kotiakku.const import (
    CONF_POWER_UNIT, 
    UNIT_W, 
    UNIT_KW,
    CONF_BATTERY_CAPACITY
)
from custom_components.elisa_kotiakku.sensor import (
    KotiakkuSensor,
    KotiakkuEnergySensor,
    KotiakkuPowerSensor,
    KotiakkuTemperatureSensor,
    KotiakkuBatterySensor,
    KotiakkuPriceSensor,
    KotiakkuBatteryStateSensor,
    KotiakkuCycleCounterSensor,
    KotiakkuTimeTargetSensor,
    KotiakkuNetSavingsRateSensor,
    KotiakkuEfficiencySensor
)

@pytest.mark.parametrize(
    "sensor_class, key, expected_unit, expected_device_class, expected_state_class",
    [
        (KotiakkuEnergySensor, "solar_energy_kwh", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        (KotiakkuPowerSensor, "solar_power_kw", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        (KotiakkuBatterySensor, "state_of_charge_percent", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
        (KotiakkuBatteryStateSensor, "battery_state", None, None, None), # String sensor
        (KotiakkuCycleCounterSensor, "battery_cycle_count", "cycles", None, SensorStateClass.TOTAL_INCREASING),
    ],
)
async def test_sensor_metadata(
    hass, mock_coordinator, mock_config_entry, 
    sensor_class, key, expected_unit, expected_device_class, expected_state_class
):
    """Test that all sensor types have the correct metadata and classes."""
    # Setup for complex sensors
    if sensor_class == KotiakkuEnergySensor:
        sensor = sensor_class(mock_coordinator, key, "solar_power_kw", "Test", "test", mock_config_entry)
    elif sensor_class == KotiakkuCycleCounterSensor:
        sensor = sensor_class(mock_coordinator, key, "total_discharge_kwh", 10.0, "Test", "test", mock_config_entry)
    else:
        sensor = sensor_class(mock_coordinator, key, "Test", "test", mock_config_entry)

    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.device_class == expected_device_class
    assert sensor.state_class == expected_state_class

async def test_battery_state_logic(hass, mock_coordinator, mock_config_entry):
    """Test localized state strings (charging/discharging/idle) with deadzone."""
    sensor = KotiakkuBatteryStateSensor(mock_coordinator, "battery_state", "Test", "test", mock_config_entry)
    
    # Test Charging
    mock_coordinator.data = {"battery_power_kw": -0.5}
    assert sensor.native_value == "charging"
    
    # Test Discharging
    mock_coordinator.data = {"battery_power_kw": 0.5}
    assert sensor.native_value == "discharging"
    
    # Test Idle (Within deadzone)
    mock_coordinator.data = {"battery_power_kw": 0.02}
    assert sensor.native_value == "idle"

async def test_cycle_counter_math(hass, mock_coordinator, mock_config_entry):
    """Test cycle count calculation: Total Discharge / Capacity."""
    # 10kWh battery capacity
    sensor = KotiakkuCycleCounterSensor(
        mock_coordinator, "battery_cycle_count", "total_discharge_kwh", 10.0, "Test", "test", mock_config_entry
    )
    
    # Discharged 25kWh total / 10kWh capacity = 2.5 cycles
    mock_coordinator.data = {"total_discharge_kwh": 25.0}
    assert sensor.native_value == 2.5

async def test_time_target_estimation(hass, mock_coordinator, mock_config_entry):
    """Test the time-to-90% calculation."""
    # 10kWh battery
    sensor = KotiakkuTimeTargetSensor(
        mock_coordinator, "time_to_90_percent", 90, 10.0, "Test", "test", mock_config_entry
    )
    
    # Current SoC 50%, Target 90% = Need 4kWh. 
    # Charging at 2kW -> 4kWh / 2kW = 2 hours = 120 minutes.
    mock_coordinator.data = {
        "state_of_charge_percent": 50,
        "battery_power_kw": -2.0  # Negative is charging
    }
    assert sensor.native_value == 120

async def test_net_savings_calculation(hass, mock_coordinator, mock_config_entry):
    """Test net savings: (Discharge * Price) - (Grid Charge * Price)."""
    sensor = KotiakkuNetSavingsRateSensor(mock_coordinator, "net_savings", "Test", "test", mock_config_entry)
    
    mock_coordinator.data = {
        "spot_price_cents_per_kwh": 10.0, # 0.10 €
        "battery_to_house_kw": 2.0,      # Earning 0.20 €/h
        "grid_to_battery_kw": 1.0        # Costing 0.10 €/h
    }
    # Net: 0.20 - 0.10 = 0.10 €/h
    assert sensor.native_value == 0.10

async def test_power_sensor_watt_conversion(hass, mock_coordinator, mock_config_entry):
    """Test kW to W scaling based on entry options."""
    # 1. Add entry to HASS so async_update_entry can find it
    mock_config_entry.add_to_hass(hass)
    
    # 2. Update options using the official API
    hass.config_entries.async_update_entry(
        mock_config_entry, 
        options={CONF_POWER_UNIT: UNIT_W}
    )
    
    mock_coordinator.data = {"solar_power_kw": 1.234}
    
    # 3. Initialize the sensor
    sensor = KotiakkuPowerSensor(
        mock_coordinator, "solar_power_kw", "Test", "test", mock_config_entry
    )

    # 4. Assertions
    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.native_value == 1234
    assert sensor.suggested_display_precision == 0

async def test_energy_sensor_riemann_sum(hass, mock_coordinator, mock_config_entry, freezer):
    """Test Riemann sum integration (Power * Time)."""
    now = dt_util.utcnow()
    freezer.move_to(now)
    
    mock_coordinator.data = {"battery_power_kw": 2.0}
    mock_coordinator.last_update_success = now
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "test_energy", "battery_power_kw", "Test", "test", mock_config_entry, direction="pos"
    )
    sensor._restored = True
    sensor._state = 10.0
    sensor._last_run = now

    # Advance 30 mins (0.5h) -> 10.0 + (2kW * 0.5h) = 11.0
    future = now + timedelta(minutes=30)
    freezer.move_to(future)
    mock_coordinator.last_update_success = future

    assert sensor.native_value == 11.0

async def test_energy_sensor_restore_invalid(hass, mock_coordinator, mock_config_entry):
    """Test restoration when the last state is garbage."""
    from unittest.mock import patch, MagicMock
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "total_charge", "battery_power_kw", "Test", "test", mock_config_entry
    )
    
    # 1. Attach hass
    sensor.hass = hass
    
    # 2. Patch both the state restoration AND the state writing
    # We patch async_write_ha_state to prevent the "translation key" error
    with patch("homeassistant.helpers.restore_state.RestoreEntity.async_get_last_state", 
               return_value=MagicMock(state="unknown")), \
         patch.object(sensor, "async_write_ha_state"):
        
        await sensor.async_added_to_hass()
        
        # 5. Assertions - check the internal _state variable
        assert sensor._state == 0.0
        assert sensor._restored is True

async def test_efficiency_clamping(hass, mock_coordinator, mock_config_entry):
    """Test that efficiency doesn't exceed 100% or go below 0%."""
    sensor = KotiakkuEfficiencySensor(
        mock_coordinator, "eff", "discharge", "charge", 10.0, "Test", "test", mock_config_entry
    )
    
    # Setup initial state
    sensor._prev_charge = 10.0
    sensor._prev_discharge = 10.0
    sensor._prev_soc = 50.0
    
    # Simulate data that would result in >100% efficiency
    mock_coordinator.data = {
        "charge": 11.0,      # 1kWh input
        "discharge": 12.0,   # 2kWh output (impossible!)
        "state_of_charge_percent": 50.0
    }
    assert sensor.native_value <= 100.0

async def test_time_target_zero_power(hass, mock_coordinator, mock_config_entry):
    """Test that time estimation handles zero power safely (Idle)."""
    sensor = KotiakkuTimeTargetSensor(
        mock_coordinator, "time_to_90", 90, 10.0, "Test", "test", mock_config_entry
    )
    mock_coordinator.data = {"state_of_charge_percent": 50, "battery_power_kw": 0.0}
    # Should return 0 or None based on your logic, but NOT crash
    assert sensor.native_value == 0

async def test_energy_sensor_none_coordination(hass, mock_coordinator, mock_config_entry):
    """Test energy sensor when coordinator data is missing."""
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "total_charge", "battery_power_kw", "Test", "test", mock_config_entry
    )
    
    # Pre-set internal state to simulate a previously known value
    sensor._state = 5.55555
    sensor._restored = True
    
    # Trigger the "None" scenario
    mock_coordinator.data = None
    
    # Should return the rounded internal state without crashing
    assert sensor.native_value == 5.556