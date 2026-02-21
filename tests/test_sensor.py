"""Tests for Elisa Kotiakku sensors."""
import pytest
from unittest.mock import MagicMock
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    UnitOfEnergy, 
    UnitOfPower, 
    UnitOfTemperature, 
    PERCENTAGE
)
from homeassistant.util import dt as dt_util
from datetime import timedelta

from custom_components.elisa_kotiakku.sensor import (
    KotiakkuEnergySensor,
    KotiakkuPowerSensor,
    KotiakkuTemperatureSensor,
    KotiakkuBatterySensor,
    KotiakkuPriceSensor
)

@pytest.mark.parametrize(
    "sensor_class, key, expected_unit, expected_device_class, expected_state_class",
    [
        # Energy Sensors: Crucial for the Energy Dashboard
        (KotiakkuEnergySensor, "solar_energy_kwh", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        (KotiakkuEnergySensor, "grid_to_house_kwh", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        
        # Power Sensors: Real-time flow
        (KotiakkuPowerSensor, "solar_power_kw", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        (KotiakkuPowerSensor, "battery_power_kw", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        
        # Environmental and Battery Status
        (KotiakkuTemperatureSensor, "battery_temperature_c", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        (KotiakkuBatterySensor, "state_of_charge_percent", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
        
        # Financial: Spot pricing
        (KotiakkuPriceSensor, "spot_price_cents_per_kwh", "c/kWh", None, SensorStateClass.MEASUREMENT),
    ],
)
async def test_sensor_metadata(
    hass, mock_coordinator, mock_config_entry, 
    sensor_class, key, expected_unit, expected_device_class, expected_state_class
):
    """Test that all sensor types have the correct metadata assigned via inheritance."""
    device_id = "Test Battery"
    device_slug = "test_battery"
    
    # Initialize the specific sensor class
    # Energy sensors take an extra 'power_key' argument for the Riemann Sum
    if sensor_class == KotiakkuEnergySensor:
        sensor = sensor_class(mock_coordinator, key, "solar_power_kw", device_id, device_slug, mock_config_entry)
    else:
        sensor = sensor_class(mock_coordinator, key, device_id, device_slug, mock_config_entry)

    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.device_class == expected_device_class
    assert sensor.state_class == expected_state_class
    assert sensor.unique_id == f"test_entry_id_{key}"

async def test_energy_sensor_riemann_sum_calculation(hass, mock_coordinator, mock_config_entry):
    """Test that the Energy sensor correctly integrates Power over time."""
    now = dt_util.utcnow()
    mock_coordinator.last_update_success = now
    mock_coordinator.data = {"solar_power_kw": 10.0} # 10kW steady flow
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "solar_energy_kwh", "solar_power_kw", 
        "Test", "test", mock_config_entry
    )

    # Initial state is 0
    assert sensor.native_value == 0.0

    # Simulate 1 hour passing (10kW * 1h = 10kWh)
    future_time = now + timedelta(hours=1)
    mock_coordinator.last_update_success = future_time
    
    # The second access triggers the calculation
    assert sensor.native_value == 10.0
    
    # Simulate another 30 minutes at 5kW (10kWh + (5kW * 0.5h) = 12.5kWh)
    mock_coordinator.data = {"solar_power_kw": 5.0}
    mock_coordinator.last_update_success = future_time + timedelta(minutes=30)
    
    assert sensor.native_value == 12.5