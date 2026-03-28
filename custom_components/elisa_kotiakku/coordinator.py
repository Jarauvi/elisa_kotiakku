"""DataUpdateCoordinator for Elisa Kotiakku."""

import holidays
try:
    from holidays.countries.finland import Finland
except ImportError:
    pass
import logging
import traceback
from datetime import datetime, timedelta, time

from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    DOMAIN, 
    CONF_API_KEY, 
    CONF_URL,
    DEFAULT_URL,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL, 
    CONF_POWER_UNIT, 
    DEFAULT_POWER_UNIT, 
    UNIT_W, 
    CONF_BATTERY_CAPACITY, 
    DEFAULT_BATTERY_CAPACITY,
    CONF_POWER_DECIMALS,
    SECTION_API_SETTINGS,
    SECTION_BATTERY_SETTINGS,
    SECTION_CURRENCY_SETTINGS,
    CONF_TRANSFER_PRICING,
    DEFAULT_TRANSFER_PRICING,
    CONF_FIXED_TRANSFER_PRICE,
    DEFAULT_FIXED_TRANSFER_PRICE,
    CONF_VAT_PERCENTAGE,
    DEFAULT_VAT_PERCENTAGE,
    CONF_ADD_VAT,
    DEFAULT_ADD_VAT,
    CONF_DAY_PRICE,
    DEFAULT_DAY_PRICE,
    CONF_DAY_START,
    DEFAULT_DAY_START,
    CONF_NIGHT_PRICE,
    DEFAULT_NIGHT_PRICE,
    CONF_NIGHT_START,
    DEFAULT_NIGHT_START,
    CONF_WINTER_DAY_PRICE,
    DEFAULT_WINTER_DAY_PRICE,
    CONF_OTHER_PRICE,
    DEFAULT_OTHER_PRICE,
    CONF_SUMMER_START_MONTH,
    DEFAULT_SUMMER_START_MONTH,
    CONF_WINTER_START_MONTH,
    DEFAULT_WINTER_START_MONTH,
    TRANSFER_FIXED,
    TRANSFER_DAY_NIGHT,
    TRANSFER_IGNORE,
    TRANSFER_SEASONAL,
    CONF_ADD_ELECTRICITY_TAX,
    DEFAULT_ADD_ELECTRICITY_TAX,
    CONF_ADD_EXPORT_TRANSFER_FEE,
    DEFAULT_ADD_EXPORT_TRANSFER_FEE,
    CONF_ELECTRICITY_TAX,
    DEFAULT_ELECTRICITY_TAX,
    CONF_EXPORT_TRANSFER_FEE,
    DEFAULT_EXPORT_TRANSFER_FEE,
    CONF_CHEAPER_HOLIDAY_RATE,
    DEFAULT_CHEAPER_HOLIDAY_RATE,
    CONF_CHEAPER_SUNDAY_RATE,
    DEFAULT_CHEAPER_SUNDAY_RATE,
    CONF_ADD_SPOT_PRICE_MARGIN,
    DEFAULT_ADD_SPOT_PRICE_MARGIN,
    CONF_SPOT_PRICE_MARGIN,
    DEFAULT_SPOT_PRICE_MARGIN,
    get_config_parameter
)
_LOGGER = logging.getLogger(__name__)

class KotiakkuDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Elisa Kotiakku API."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.api_url = get_config_parameter(entry, SECTION_API_SETTINGS, CONF_URL, DEFAULT_URL)
        self.api_key = get_config_parameter(entry, SECTION_API_SETTINGS, CONF_API_KEY, "")
        self._holiday_cache = {}
        scan_interval = get_config_parameter(entry, SECTION_API_SETTINGS, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        self.last_soc = 0
        self.stored_price = 0

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_get_fi_holidays(self, year):
        """Fetch holidays from cache or create new ones in executor."""
        if year not in self._holiday_cache:
            # We use a lambda to ensure the call is wrapped properly
            self._holiday_cache[year] = await self.hass.async_add_executor_job(
                lambda: holidays.Finland(years=year)
            )
        return self._holiday_cache[year]

    async def _async_update_data(self):
        """Fetch data from API endpoint.
        
        This is the core method that HA calls automatically based on 
        the update_interval.
        """
        headers = {
            "x-api-key": self.api_key,
            "accept": "application/json"
        }
        
        try:
            # We use the hass-provided helper for aiohttp sessions
            session = async_get_clientsession(self.hass)
            
            async with session.get(self.api_url, headers=headers, timeout=10) as response:
                if response.status == 401:
                    raise UpdateFailed("Invalid API Key - Authentication failed")
                
                response.raise_for_status()
                raw_data = await response.json()
                
                data = raw_data[0] if isinstance(raw_data, list) and len(raw_data) > 0 else raw_data
                if not data:
                    raise UpdateFailed("API returned empty data")
                
                power_unit_pref = get_config_parameter(self.entry, SECTION_BATTERY_SETTINGS, CONF_POWER_UNIT, DEFAULT_POWER_UNIT)
                power_display_multiplier = 1000.0 if power_unit_pref == "W" else 1.0
                data["power_display_unit"] = power_unit_pref
                data["power_decimals"] = 0 if power_unit_pref == UNIT_W else CONF_POWER_DECIMALS
                
                # Power values
                power_keys = [
                    "battery_power_kw", 
                    "solar_power_kw", 
                    "grid_power_kw",
                    "house_power_kw",
                    "solar_to_house_kw",
                    "solar_to_battery_kw",
                    "solar_to_grid_kw",
                    "grid_to_house_kw",
                    "grid_to_battery_kw",
                    "battery_to_house_kw",
                    "battery_to_grid_kw"
                ]
                other_keys = [
                    "spot_price_cents_per_kwh",
                    "state_of_charge_percent",
                    "battery_temperature_celsius"
                ]
                
                for key in power_keys:
                    if key in data:
                        if data.get(key) is not None:
                            data[f"{key}_display"] = round(data[key] * power_display_multiplier, data["power_decimals"])
                        else:
                            _LOGGER.error(f"Null value received for: {key}")
                    else:
                        _LOGGER.error(f"Data field missing: {key}")
                        
                for key in other_keys:
                    if key in data:
                        if data.get(key) is None:
                            _LOGGER.error(f"Null value received for: {key}")
                    else:
                        _LOGGER.error(f"Data field missing: {key}")
                
                # Power sums
                if data.get("solar_to_battery_kw") is not None and data.get("grid_to_battery_kw") is not None:
                    data["battery_charge_total_kw"] = data.get("solar_to_battery_kw", 0) + data.get("grid_to_battery_kw", 0)
                    data["battery_charge_total_kw_display"] = round(data.get("solar_to_battery_kw_display", 0) + data.get("grid_to_battery_kw_display", 0), CONF_POWER_DECIMALS)
                else: 
                    data["battery_charge_total_kw"] = None
                    data["battery_charge_total_kw_display"] = None
                    
                if data.get("battery_to_house_kw") is not None and data.get("battery_to_grid_kw") is not None:
                    data["battery_discharge_total_kw"] = data.get("battery_to_house_kw", 0) + data.get("battery_to_grid_kw", 0)
                    data["battery_discharge_total_kw_display"] = round(data.get("battery_to_house_kw_display", 0) + data.get("battery_to_grid_kw_display", 0), CONF_POWER_DECIMALS)
                else:
                    data["battery_discharge_total_kw"] = None
                    data["battery_discharge_total_kw_display"] = None
                    
                if data.get("grid_to_house_kw") is not None and data.get("grid_to_battery_kw") is not None:
                    data["total_grid_import_kw"] = data.get("grid_to_house_kw", 0) + data.get("grid_to_battery_kw", 0)
                    data["total_grid_import_kw_display"] = round(data.get("total_grid_import_kw", 0) * power_display_multiplier, CONF_POWER_DECIMALS)
                else:
                    data["total_grid_import_kw"] = None
                    data["total_grid_import_kw_display"] = None
                    
                if data.get("battery_to_grid_kw") is not None and data.get("solar_to_grid_kw") is not None:
                    data["total_grid_export_kw"] = data.get("battery_to_grid_kw", 0) + data.get("solar_to_grid_kw", 0)
                    data["total_grid_export_kw_display"] = round(data.get("total_grid_export_kw", 0) * power_display_multiplier, CONF_POWER_DECIMALS)
                else:
                    data["total_grid_export_kw"] = None
                    data["total_grid_export_kw_display"] = None
                              
                # Loss power
                
                try:
                    battery_power = data.get("battery_power_kw", 0)
                    
                    loss = 0
                    if battery_power < 0:
                        charge_input = data.get("solar_to_battery_kw", 0) + data.get("grid_to_battery_kw", 0)
                        stored = abs(battery_power)
                        loss = charge_input - stored
                    elif battery_power > 0:
                        delivered = data.get("battery_to_house_kw", 0) + data.get("battery_to_grid_kw", 0)
                        loss = battery_power - delivered
                    
                    data["battery_loss_kw"] = max(loss, 0)
                    data["battery_loss_kw_display"] = round(data.get("battery_loss_kw", 0) * power_display_multiplier, CONF_POWER_DECIMALS)
                except TypeError:
                    data["battery_loss_kw"] = None
                    data["battery_loss_kw_display"] = None
                    
                    
                # Savings
                try:
                    price_eur_kwh = data.get("spot_price_cents_per_kwh", 0) / 100
                    transfer_fee_eur_kwh = await self.get_transfer_fee(self.entry) / 100
                    spot_price_margin = await self.get_spot_price_margin(self.entry) / 100
                
                    vat_mult = 1.0
                    if get_config_parameter(self.entry, SECTION_CURRENCY_SETTINGS, CONF_ADD_VAT, DEFAULT_ADD_VAT):
                        vat_mult = (1 + (get_config_parameter(self.entry, SECTION_CURRENCY_SETTINGS, CONF_VAT_PERCENTAGE, DEFAULT_VAT_PERCENTAGE)/100))
                    
                    buy_rate = (price_eur_kwh + spot_price_margin + transfer_fee_eur_kwh) * vat_mult
                    solar_savings = data.get("solar_to_house_kw", 0) * buy_rate
                    battery_savings = data.get("battery_to_house_kw", 0) * buy_rate

                    export_fee = 0
                    if get_config_parameter(self.entry, SECTION_CURRENCY_SETTINGS, CONF_ADD_EXPORT_TRANSFER_FEE, DEFAULT_ADD_EXPORT_TRANSFER_FEE):
                        export_fee = get_config_parameter(self.entry, SECTION_CURRENCY_SETTINGS, CONF_EXPORT_TRANSFER_FEE, DEFAULT_EXPORT_TRANSFER_FEE)
                    
                    sell_rate = price_eur_kwh + spot_price_margin - export_fee
                    export_income = (data.get("solar_to_grid_kw", 0) + data.get("battery_to_grid_kw", 0)) * sell_rate
                    charging_cost = data.get("grid_to_battery_kw", 0) * buy_rate
                    
                    data["net_savings_rate"] = solar_savings + battery_savings + export_income - charging_cost
                    data["total_price_cents_per_kwh"] = (price_eur_kwh + spot_price_margin + transfer_fee_eur_kwh) * 100 * vat_mult
                    
                except TypeError:
                    data["net_savings_rate"] = None
                    data["total_price_cents_per_kwh"] = None
                    
                try:
                    current_soc = data.get("state_of_charge_percent", 0)
                    if not hasattr(self, "last_soc"):
                        self.last_soc = current_soc
                        self.stored_price = buy_rate * 100
                    
                    battery_power = data.get("battery_power_kw", 0)
                    
                    if battery_power < 0 and current_soc > self.last_soc:
                        added_soc = current_soc - self.last_soc
                        new_total_cost = (self.last_soc * self.stored_price) + (added_soc * buy_rate * 100)
                        self.stored_price = new_total_cost / current_soc
                    
                    self.last_soc = current_soc
                    data["battery_stored_energy_price"] = round(self.stored_price, 2)
                    
                except (TypeError, ZeroDivisionError):
                    data["battery_stored_energy_price"] = 0
                    
                # Charge efficiency
                try:
                    solar = data.get("solar_to_battery_kw", 0)
                    grid = data.get("grid_to_battery_kw", 0)
                    battery_power = data.get("battery_power_kw")

                    charge_input = solar + grid
                    stored_power = abs(min(0, float(battery_power)))

                    eff = 0
                    if charge_input > 0:
                        eff = (stored_power / charge_input) * 100
                        
                    data["battery_charge_efficiency"] = round(min(eff, 100), 1)
                    
                except TypeError:
                    data["battery_charge_efficiency"] = None
                  
                # Discharge efficiency  
                try:
                    house = data.get("battery_to_house_kw", 0)
                    grid = data.get("battery_to_grid_kw", 0)
                    battery_power = data.get("battery_power_kw")

                    battery_output = max(0, float(battery_power))
                    delivered = house + grid

                    eff = 0
                    if battery_output > 0:
                        eff = (delivered / battery_output) * 100
                        
                    data["battery_discharge_efficiency"] = round(min(eff, 100), 1)
                except TypeError:
                    data["battery_discharge_efficiency"] = None
                        
                # Time-to-target sensors
                try:
                    battery_capacity = get_config_parameter(self.entry, SECTION_BATTERY_SETTINGS, CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)

                    # Time to 90% charge
                    data["time_to_90_percent"] = self.calculate_target_time(
                        data.get("state_of_charge_percent", 0),
                        battery_power,
                        90,
                        battery_capacity
                    )
                except TypeError:
                    data["time_to_90_percent"] = None
                
                # Time to 15% discharge
                try:
                    data["time_to_15_percent"] = self.calculate_target_time(
                        data.get("state_of_charge_percent", 0),
                        battery_power,
                        15,
                        battery_capacity
                    )
                except TypeError:
                    data["time_to_15_percent"] = None
    
                _LOGGER.debug("Kotiakku data received: %s", data)

                return data

        except Exception as err:
            _LOGGER.error("Full Traceback: %s", traceback.format_exc())
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        
    def calculate_target_time(self, current_soc, power_kw, target_soc, battery_capacity):
        if abs(current_soc - target_soc) < 0.5:
            return "-"

        if (target_soc > current_soc and power_kw >= 0) or \
        (target_soc < current_soc and power_kw <= 0):
            if abs(current_soc - target_soc) < 0.5:
                return "-"
            
        is_charging = power_kw < 0
        is_discharging = power_kw > 0
        
        moving_to_target = (target_soc > current_soc and is_charging) or \
                        (target_soc < current_soc and is_discharging)

        if not moving_to_target or abs(power_kw) < 0.05:
            return "-"

        target_energy = battery_capacity * (target_soc / 100.0)
        current_energy = battery_capacity * (current_soc / 100.0)
        energy_diff = abs(target_energy - current_energy)
        
        hours_remaining = energy_diff / abs(power_kw)
        if hours_remaining is None or hours_remaining == 0:
            return "-"

        total_minutes = int(hours_remaining * 60)
        hours, mins = divmod(total_minutes, 60)

        if hours > 0:
            return f"{hours}h {mins}m"
        return f"{mins}m"

    async def get_spot_price_margin(self, entry):
        add_margin = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ADD_SPOT_PRICE_MARGIN, DEFAULT_ADD_SPOT_PRICE_MARGIN)
        if add_margin:            
            return get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ELECTRICITY_TAX, DEFAULT_ELECTRICITY_TAX)
        
        return 0.0
        
    async def get_transfer_fee(self, entry):
        mode = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_TRANSFER_PRICING, DEFAULT_TRANSFER_PRICING)
        add_electricity_tax = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ADD_ELECTRICITY_TAX, DEFAULT_ADD_ELECTRICITY_TAX)
        now = datetime.now()
        is_sunday = now.weekday() == 6
        is_holiday = await self.is_billing_holiday(now.date())
        current_time = now.time()
        current_month = now.month
        price = 0

        if mode == TRANSFER_FIXED:
            price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_FIXED_TRANSFER_PRICE, DEFAULT_FIXED_TRANSFER_PRICE)
            if add_electricity_tax:
                price += get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ELECTRICITY_TAX, DEFAULT_ELECTRICITY_TAX)

        if mode == TRANSFER_DAY_NIGHT:
            day_start = datetime.strptime(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_START, DEFAULT_DAY_START), "%H:%M:%S").time()
            night_start = datetime.strptime(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_START, DEFAULT_NIGHT_START), "%H:%M:%S").time()

            
            if is_sunday or is_holiday:
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_PRICE, DEFAULT_DAY_PRICE)
                
            if self.is_within_time_range(current_time, day_start, night_start):
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_PRICE, DEFAULT_DAY_PRICE)
            else:
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_PRICE, DEFAULT_NIGHT_PRICE)
            if add_electricity_tax:
                price += get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ELECTRICITY_TAX, DEFAULT_ELECTRICITY_TAX)

        if mode == TRANSFER_SEASONAL:
            winter_start = int(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_WINTER_START_MONTH, DEFAULT_WINTER_START_MONTH))
            summer_start = int(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_SUMMER_START_MONTH, DEFAULT_SUMMER_START_MONTH))
            day_start = datetime.strptime(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_DAY_START, DEFAULT_DAY_START), "%H:%M:%S").time()
            night_start = datetime.strptime(get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_NIGHT_START, DEFAULT_NIGHT_START), "%H:%M:%S").time()
            cheaper_sunday_rate = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_CHEAPER_SUNDAY_RATE, DEFAULT_CHEAPER_SUNDAY_RATE)
            cheaper_holiday_rate = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_CHEAPER_HOLIDAY_RATE, DEFAULT_CHEAPER_HOLIDAY_RATE)

            is_winter = current_month >= winter_start or current_month < summer_start
            is_day = self.is_within_time_range(current_time, day_start, night_start)
            
            if (cheaper_sunday_rate and is_sunday) or (cheaper_holiday_rate and is_holiday):
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_OTHER_PRICE, DEFAULT_OTHER_PRICE)
            elif is_winter and is_day:
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_WINTER_DAY_PRICE, DEFAULT_WINTER_DAY_PRICE)
            else:
                price = get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_OTHER_PRICE, DEFAULT_OTHER_PRICE)

            if add_electricity_tax:
                price += get_config_parameter(entry, SECTION_CURRENCY_SETTINGS, CONF_ELECTRICITY_TAX, DEFAULT_ELECTRICITY_TAX)

        
        return price

    def is_within_time_range(self, current_time, start_time, end_time):
        """Check if current time is within a range, handling midnight wrap-around."""
        
        if start_time <= end_time:
            return start_time <= current_time < end_time
        else:
            return current_time >= start_time or current_time < end_time
        
    async def is_billing_holiday(self, check_date):
        """Check if the date is a Finnish public holiday."""
        fi_holidays = await self._async_get_fi_holidays(check_date.year)
        
        extra_holidays = [
            "Midsummer Eve", 
            "Christmas Eve"
        ]
        
        is_official = check_date in fi_holidays
        is_extra = fi_holidays.get(check_date) in extra_holidays
        
        return is_official or is_extra