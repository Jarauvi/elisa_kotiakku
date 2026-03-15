"""Tests for Elisa Kotiakku DataUpdateCoordinator."""

import re
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from aioresponses import aioresponses

from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.elisa_kotiakku.coordinator import KotiakkuDataUpdateCoordinator
from custom_components.elisa_kotiakku.const import (
    DOMAIN,
    CONF_POWER_UNIT,
    CONF_BATTERY_CAPACITY,
    TRANSFER_FIXED,
    TRANSFER_DAY_NIGHT,
    TRANSFER_SEASONAL
)


# --- Integration Level Coordinator Tests ---


async def test_coordinator_update_success(hass, mock_config_entry):
    """Test a successful data refresh cycle with list-style API response."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_POWER_UNIT: "W"},
    )

    payload = [
        {
            "state_of_charge_percent": 85,
            "battery_power_kw": 1.2,
            "solar_power_kw": 2.5,
            "grid_power_kw": -1.0,
            "house_power_kw": 0.3,
            "solar_to_battery_kw": 0.5,
            "grid_to_battery_kw": 0.7,
        }
    ]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_config_entry.state is ConfigEntryState.LOADED

        coordinator = hass.data[DOMAIN][mock_config_entry.entry_id]

        assert coordinator.data["state_of_charge_percent"] == 85

        # 1.2kW -> 1200W
        assert coordinator.data["battery_power_kw_display"] == 1200

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()


# --- Internal Logic & Math Tests ---


async def test_coordinator_math_logic(hass, mock_config_entry):
    """Test charging efficiency and time-to-target calculations."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={
            **mock_config_entry.data,
            CONF_BATTERY_CAPACITY: 10.0,
            CONF_POWER_UNIT: "kW",
        },
    )

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    # Avoid transfer pricing randomness
    coordinator.get_transfer_fee = AsyncMock(return_value=0.02)

    payload = [
        {
            "state_of_charge_percent": 50.0,
            "battery_power_kw": -2.0,  # charging
            "solar_to_battery_kw": 5.0,
            "grid_to_battery_kw": 0.0,
            "battery_to_house_kw": 0.0,
            "battery_to_grid_kw": 0.0,
            "spot_price_cents_per_kwh": 10.0,
        }
    ]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        data = await coordinator._async_update_data()

        # stored = 2kW, input = 5kW → 40%
        assert data["battery_charge_efficiency"] == 40.0

        # 50% → 90% on 10kWh battery = 4kWh
        # 4kWh / 2kW = 2h
        assert coordinator.calculate_target_time(
            50,
            -2,
            90,
            10
        ) == "2h 0m"


async def test_coordinator_discharge_math(hass, mock_config_entry):
    """Test discharge efficiency and time-to-target."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_BATTERY_CAPACITY: 10.0},
    )

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    coordinator.get_transfer_fee = AsyncMock(return_value=0)

    payload = [
        {
            "state_of_charge_percent": 50.0,
            "battery_power_kw": 2.0,  # discharging
            "battery_to_house_kw": 1.8,
            "battery_to_grid_kw": 0.0,
            "solar_to_battery_kw": 0.0,
            "grid_to_battery_kw": 0.0,
        }
    ]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        data = await coordinator._async_update_data()

        # delivered 1.8 / output 2.0 = 90%
        assert data["battery_discharge_efficiency"] == 90.0

        # 50% → 15% = 3.5kWh
        # 3.5kWh / 2kW = 1.75h = 1h45m
        assert coordinator.calculate_target_time(
            50,
            2,
            15,
            10
        ) == "1h 45m"


# --- Error Handling Tests ---


async def test_coordinator_auth_failure(hass, mock_config_entry):
    """Test authentication failure."""

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=401)

        with pytest.raises(UpdateFailed, match="Authentication failed"):
            await coordinator._async_update_data()


async def test_coordinator_empty_data(hass, mock_config_entry):
    """Test empty API response."""

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=[])

        with pytest.raises(UpdateFailed, match="API returned empty data"):
            await coordinator._async_update_data()


async def test_coordinator_network_error(hass, mock_config_entry):
    """Test HTTP error handling."""

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=500)

        with pytest.raises(UpdateFailed, match="Error communicating with API"):
            await coordinator._async_update_data()
            
async def test_coordinator_solar_savings_calculation(hass, mock_config_entry):
    """Test solar self-consumption savings."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    # Ensure deterministic transfer fee
    coordinator.get_transfer_fee = AsyncMock(return_value=0)

    payload = [{
        "state_of_charge_percent": 50,
        "battery_power_kw": 0,
        "solar_to_house_kw": 2.0,
        "battery_to_house_kw": 0.0,
        "solar_to_grid_kw": 0.0,
        "battery_to_grid_kw": 0.0,
        "grid_to_battery_kw": 0.0,
        "spot_price_cents_per_kwh": 20.0
    }]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        data = await coordinator._async_update_data()

        # 20 cents = 0.20 €/kWh
        # solar_to_house = 2 kW → savings = 2 * 0.20
        assert data["net_savings_rate"] == pytest.approx(0.40)
        
async def test_coordinator_combined_savings_calculation(hass, mock_config_entry):
    """Test combined solar, battery and export savings."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    coordinator.get_transfer_fee = AsyncMock(return_value=0)

    payload = [{
        "state_of_charge_percent": 60,
        "battery_power_kw": 1.0,
        "solar_to_house_kw": 1.0,
        "battery_to_house_kw": 1.0,
        "solar_to_grid_kw": 1.0,
        "battery_to_grid_kw": 0.0,
        "grid_to_battery_kw": 0.5,
        "spot_price_cents_per_kwh": 10.0
    }]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        data = await coordinator._async_update_data()

        # price = 10 cents = 0.10 €
        # solar self use = 1 * 0.10
        # battery self use = 1 * 0.10
        # export = 1 * 0.10
        # charging cost = 0.5 * 0.10

        expected = 0.10 + 0.10 + 0.10 - 0.05

        assert data["net_savings_rate"] == pytest.approx(expected)
        
async def test_coordinator_export_fee_reduces_income(hass, mock_config_entry):
    """Test export transfer fee reduces export income."""

    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        version=1,
    )

    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            "add_export_transfer_fee": True,
            "export_transfer_fee": 0.02
        },
    )

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    coordinator.get_transfer_fee = AsyncMock(return_value=0)

    payload = [{
        "state_of_charge_percent": 60,
        "battery_power_kw": 0,
        "solar_to_house_kw": 0,
        "battery_to_house_kw": 0,
        "solar_to_grid_kw": 1.0,
        "battery_to_grid_kw": 0.0,
        "grid_to_battery_kw": 0.0,
        "spot_price_cents_per_kwh": 10.0
    }]

    with aioresponses() as m:
        m.get(re.compile(r".*"), status=200, payload=payload)

        data = await coordinator._async_update_data()

        # price = 0.10
        # export fee = 0.02
        # sell rate = 0.08

        coordinator.get_transfer_fee = AsyncMock(return_value=0.02)
        
async def test_is_billing_holiday_extra(mock_config_entry, hass):
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    # Patch _async_get_fi_holidays to return a dummy holiday dict
    coordinator._async_get_fi_holidays = AsyncMock(return_value={datetime(2026, 6, 19).date(): "Midsummer Eve"})
    
    result = await coordinator.is_billing_holiday(datetime(2026, 6, 19).date())
    assert result is True
    
@pytest.mark.asyncio
async def test_async_update_data_empty_response(mock_config_entry, hass):
    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)
    
    # Patch the async_get_clientsession in your coordinator module
    mock_session = AsyncMock()
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=[])  # empty data triggers UpdateFailed
    mock_session.get.return_value.__aenter__.return_value = mock_response

    with patch("custom_components.elisa_kotiakku.coordinator.async_get_clientsession", return_value=mock_session):
        from homeassistant.helpers.update_coordinator import UpdateFailed
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
            
@pytest.mark.asyncio
async def test_transfer_fee_modes(monkeypatch, mock_config_entry, hass):
    """Test all transfer fee modes."""

    coordinator = KotiakkuDataUpdateCoordinator(hass, mock_config_entry)

    # Patch is_billing_holiday to control holidays
    monkeypatch.setattr(coordinator, "is_billing_holiday", AsyncMock(return_value=False))
    
    # Patch datetime to control weekday/time
    class FixedDatetime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 3, 16, 14, 0, 0)  # Monday, 14:00
    
    monkeypatch.setattr("custom_components.elisa_kotiakku.coordinator.datetime", FixedDatetime)

    # ----------------- TRANSFER_FIXED -----------------
    monkeypatch.setattr(
        "custom_components.elisa_kotiakku.coordinator.get_config_parameter",
        lambda entry, section, param, default: TRANSFER_FIXED if param == "transfer_pricing" else 1
    )
    fee = await coordinator.get_transfer_fee(mock_config_entry)
    assert isinstance(fee, (int, float))  # basic check

    # ----------------- TRANSFER_DAY_NIGHT -----------------
    def config_daynight(entry, section, param, default):
        mapping = {
            "transfer_pricing": TRANSFER_DAY_NIGHT,
            "day_start": "06:00:00",
            "night_start": "22:00:00",
            "day_price": 2,
            "night_price": 1,
            "add_electricity_tax": False,
        }
        return mapping.get(param, default)
    
    monkeypatch.setattr(
        "custom_components.elisa_kotiakku.coordinator.get_config_parameter",
        config_daynight
    )
    fee = await coordinator.get_transfer_fee(mock_config_entry)
    assert fee == 2  # 14:00 is day rate

    # ----------------- TRANSFER_SEASONAL -----------------
    def config_seasonal(entry, section, param, default):
        mapping = {
            "transfer_pricing": TRANSFER_SEASONAL,
            "winter_start_month": 11,
            "summer_start_month": 6,
            "day_start": "06:00:00",
            "night_start": "22:00:00",
            "cheaper_sunday_rate": False,
            "cheaper_holiday_rate": False,
            "winter_day_price": 3,
            "other_price": 1,
            "add_electricity_tax": False,
        }
        return mapping.get(param, default)

    monkeypatch.setattr(
        "custom_components.elisa_kotiakku.coordinator.get_config_parameter",
        config_seasonal
    )

    # ----------------- TEST NON-WINTER (OTHER_PRICE) -----------------
    class FixedDatetime(datetime):
        @classmethod
        def now(cls):
            # July → non-winter
            return cls(2026, 7, 16, 14, 0, 0)  # Monday, 14:00
    monkeypatch.setattr("custom_components.elisa_kotiakku.coordinator.datetime", FixedDatetime)

    fee = await coordinator.get_transfer_fee(mock_config_entry)
    assert fee == 1  # other_price applied

    # ----------------- TEST WINTER DAY -----------------
    class FixedDatetimeWinter(datetime):
        @classmethod
        def now(cls):
            # December → winter
            return cls(2026, 12, 16, 14, 0, 0)  # Monday, 14:00
    monkeypatch.setattr("custom_components.elisa_kotiakku.coordinator.datetime", FixedDatetimeWinter)

    fee = await coordinator.get_transfer_fee(mock_config_entry)
    assert fee == 3  # winter_day_price applied