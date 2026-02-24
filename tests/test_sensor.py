"""Tests for Elisa Kotiakku sensors.

This module covers the sensor platform, including metadata validation, 
unit conversion logic for power sensors, and the integration (Riemann sum) 
calculations for energy sensors.
"""

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

from custom_components.elisa_kotiakku.sensor import KotiakkuSensor
from custom_components.elisa_kotiakku.coordinator import KotiakkuDataUpdateCoordinator
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
    """Test that all sensor types have the correct metadata and classes.
    
    Verifies that device classes and state classes are correctly assigned 
    to ensure proper behavior in the Home Assistant Energy dashboard and UI.
    """
    if mock_config_entry.entry_id not in hass.config_entries._entries:
        mock_config_entry.add_to_hass(hass)

    # Ensure the configuration options are set to a known state
    hass.config_entries.async_update_entry(
        mock_config_entry, 
        options={CONF_POWER_UNIT: UNIT_KW}
    )
    
    device_id, device_slug = "Test Battery", "test_battery"
    
    # Energy sensors require an additional power_key for integration calculations
    if sensor_class == KotiakkuEnergySensor:
        sensor = sensor_class(mock_coordinator, key, "solar_power_kw", device_id, device_slug, mock_config_entry)
    else:
        sensor = sensor_class(mock_coordinator, key, device_id, device_slug, mock_config_entry)

    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.device_class == expected_device_class
    assert sensor.state_class == expected_state_class

async def test_power_sensor_watt_conversion(hass, mock_coordinator, mock_config_entry):
    """Test that Power sensor correctly converts kW from the API to W if configured.
    
    This verifies the scaling logic (kW * 1000) and the dynamic entity_id 
    naming based on the selected unit.
    """
    mock_config_entry.add_to_hass(hass)
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
    """Test that the Energy sensor correctly integrates Power over time.
    
    Verifies the Riemann sum: Energy = Power * Time. 
    A 10kW load for 1 hour should result in 10kWh.
    """
    now = dt_util.utcnow()
    mock_coordinator.last_update_success = now
    mock_coordinator.data = {"solar_power_kw": 10.0}
    
    sensor = KotiakkuEnergySensor(
        mock_coordinator, "solar_energy_kwh", "solar_power_kw", 
        "Test", "test", mock_config_entry
    )

    assert sensor.native_value == 0.0

    # Simulate 1 hour passing
    future_time = now + timedelta(hours=1)
    mock_coordinator.last_update_success = future_time
    assert sensor.native_value == 10.0

async def test_sensor_native_value_coordinator_data_none(hass, mock_config_entry):
    """Test native_value returns None when coordinator data is missing.
    
    Ensures sensors don't crash and return a clean 'None' state if the 
    coordinator fails to fetch data from the API.
    """
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    sensor = KotiakkuSensor(
        coordinator=coordinator,
        key="soc",
        device_name="Test Battery",
        device_slug="test_battery",
        entry=mock_config_entry
    )
    
    coordinator.data = None
    assert sensor.native_value is None

async def test_energy_sensor_native_value_none_data(hass, mock_config_entry):
    """Test native_value returns rounded internal state when coordinator data is None.
    
    Ensures that if the API fetch fails, the energy sensor returns its 
    last known cumulative value instead of resetting to zero.
    """
    mock_coordinator = MagicMock()
    mock_coordinator.data = None
    mock_coordinator.last_update_success = None
    
    sensor = KotiakkuEnergySensor(
        coordinator=mock_coordinator,
        device_id="test_device_id",
        device_slug="kotiakku",
        entry=mock_config_entry,
        key="total_discharged",
        power_key="battery_power"
    )
    
    sensor._state = 12.345678
    # native_value should return the rounded internal _state
    assert sensor.native_value == 12.3457

async def test_energy_sensor_calculation(hass, mock_config_entry, freezer):
    """Test that energy increments correctly based on power and time passage.
    
    Uses freezer to simulate a 30-minute interval with a 2kW load, 
    expecting a 1kWh increase in the energy total.
    """
    freezer.move_to("2026-02-15 12:00:00+00:00")
    now = dt_util.utcnow()
    
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"battery_power": 2.0}
    mock_coordinator.last_update_success = now
    
    sensor = KotiakkuEnergySensor(
        coordinator=mock_coordinator,
        device_id="test_id",
        device_slug="kotiakku",
        entry=mock_config_entry,
        key="total_discharged",
        power_key="battery_power"
    )
    sensor._state = 10.0
    sensor._last_run = now

    # Advance time by 0.5 hours
    future_now = now + timedelta(minutes=30)
    freezer.move_to(future_now)
    mock_coordinator.last_update_success = future_now

    # Math: 10.0 + (2.0kW * 0.5h) = 11.0
    assert sensor.native_value == 11.0
    assert sensor._last_run == future_now

async def test_energy_sensor_no_time_passed(hass, mock_config_entry):
    """Test that energy does not increment if the time delta is zero.
    
    Prevents duplicate increments if the coordinator update logic triggers 
    without a timestamp change.
    """
    now = dt_util.utcnow()
    mock_coordinator = MagicMock()
    mock_coordinator.data = {"battery_power": 5.0}
    mock_coordinator.last_update_success = now
    
    sensor = KotiakkuEnergySensor(
        coordinator=mock_coordinator,
        device_id="test_id",
        device_slug="kotiakku",
        entry=mock_config_entry,
        key="total_discharged",
        power_key="battery_power"
    )
    
    sensor._state = 10.0
    sensor._last_run = now 
    
    # diff will be 0, total should remain 10.0
    assert sensor.native_value == 10.0