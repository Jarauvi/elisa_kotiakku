"""Tests for Elisa Kotiakku sensors."""
import pytest
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import (
    UnitOfEnergy, 
    UnitOfPower, 
    UnitOfTemperature, 
    PERCENTAGE
)
from homeassistant.util import dt as dt_util
from datetime import timedelta

from custom_components.elisa_kotiakku.const import CONF_POWER_UNIT, UNIT_W, UNIT_KW
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
        (KotiakkuEnergySensor, "solar_energy_kwh", UnitOfEnergy.KILO_WATT_HOUR, SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING),
        (KotiakkuPowerSensor, "solar_power_kw", UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, SensorStateClass.MEASUREMENT),
        (KotiakkuTemperatureSensor, "battery_temperature_c", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
        (KotiakkuBatterySensor, "state_of_charge_percent", PERCENTAGE, SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
        (KotiakkuPriceSensor, "spot_price_cents_per_kwh", "c/kWh", None, SensorStateClass.MEASUREMENT),
    ],
)
async def test_sensor_metadata(
    hass, mock_coordinator, mock_config_entry, 
    sensor_class, key, expected_unit, expected_device_class, expected_state_class
):
    """Test that all sensor types have the correct metadata."""
    # 1. Register the entry so async_update_entry works
    if mock_config_entry.entry_id not in hass.config_entries._entries:
        mock_config_entry.add_to_hass(hass)

    # 2. Update via the official API
    hass.config_entries.async_update_entry(
        mock_config_entry, 
        options={CONF_POWER_UNIT: UNIT_KW}
    )
    
    device_id, device_slug = "Test Battery", "test_battery"
    
    if sensor_class == KotiakkuEnergySensor:
        sensor = sensor_class(mock_coordinator, key, "solar_power_kw", device_id, device_slug, mock_config_entry)
    else:
        sensor = sensor_class(mock_coordinator, key, device_id, device_slug, mock_config_entry)

    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.device_class == expected_device_class
    assert sensor.state_class == expected_state_class

async def test_power_sensor_watt_conversion(hass, mock_coordinator, mock_config_entry):
    """Test that Power sensor correctly converts kW to W."""
    # Register the entry
    mock_config_entry.add_to_hass(hass)

    # Update options correctly
    hass.config_entries.async_update_entry(
        mock_config_entry, 
        options={CONF_POWER_UNIT: UNIT_W}
    )
    
    mock_coordinator.data = {"solar_power_kw": 1.5}
    
    sensor = KotiakkuPowerSensor(
        mock_coordinator, "solar_power_kw", "Test", "test", mock_config_entry
    )

    assert sensor.native_unit_of_measurement == UnitOfPower.WATT
    assert sensor.native_value == 1500.0
    assert sensor.entity_id == "sensor.test_solar_power_w"

async def test_energy_sensor_riemann_sum_calculation(hass, mock_coordinator, mock_config_entry):
    """Test that the Energy sensor correctly integrates Power over time."""
    now = dt_util.utcnow()
    mock_coordinator.last_update_success = now
    mock_coordinator.data = {"solar_power_kw": 10.0}
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "solar_energy_kwh", "solar_power_kw", 
        "Test", "test", mock_config_entry
    )

    assert sensor.native_value == 0.0

    future_time = now + timedelta(hours=1)
    mock_coordinator.last_update_success = future_time
    assert sensor.native_value == 10.0