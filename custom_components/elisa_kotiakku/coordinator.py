"""DataUpdateCoordinator for Elisa Kotiakku."""

import logging
from datetime import timedelta
import aiohttp

from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, CONF_API_KEY, CONF_URL, DEFAULT_SCAN_INTERVAL, CONF_POWER_UNIT, DEFAULT_POWER_UNIT, UNIT_W, CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY

_LOGGER = logging.getLogger(__name__)

class KotiakkuDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Elisa Kotiakku API."""

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize the coordinator."""
        self.hass = hass
        self.entry = entry
        self.api_url = entry.data[CONF_URL]
        self.api_key = entry.data[CONF_API_KEY]
        self._primed = False
        
        self._solar_energy_kwh = 0.0
        self._solar_to_house_kwh = 0.0
        self._solar_to_battery_kwh = 0.0
        self._solar_to_grid_kwh = 0.0
        self._grid_to_house_kwh = 0.0
        self._grid_to_battery_kwh = 0.0
        self._battery_to_house_kwh = 0.0
        self._battery_to_grid_kwh = 0.0
        self._house_energy_kwh = 0.0
        self._total_battery_charge_kwh = 0.0
        self._total_battery_discharge_kwh = 0.0
        self._total_grid_import_kwh = 0.0
        self._total_grid_export_kwh = 0.0
        self._battery_loss_kwh = 0.0
        self._last_energy_run = None
        
        # Pull scan interval from config or use default
        scan_interval = entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval),
        )

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
                
                power_unit_pref = self.entry.options.get(CONF_POWER_UNIT, self.entry.data.get(CONF_POWER_UNIT, DEFAULT_POWER_UNIT))
                power_display_multiplier = 1000.0 if power_unit_pref == "W" else 1.0
                data["power_display_unit"] = power_unit_pref
                data["power_decimals"] = 0 if power_unit_pref == UNIT_W else 3
                
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
                for key in power_keys:
                    if key in data:
                        data[f"{key}_display"] = data[key] * power_display_multiplier 
                
                # Power sums
                data["battery_charge_total_kw"] = data.get("solar_to_battery_kw", 0) + data.get("grid_to_battery_kw", 0)
                data["battery_charge_total_kw_display"] = data.get("solar_to_battery_kw_display", 0) + data.get("grid_to_battery_kw_display", 0)
                data["battery_discharge_total_kw"] = data.get("battery_to_house_kw", 0) + data.get("battery_to_grid_kw", 0)
                data["battery_discharge_total_kw_display"] = data.get("battery_to_house_kw_display", 0) + data.get("battery_to_grid_kw_display", 0)
                data["total_grid_import_kw"] = data.get("grid_to_house_kw", 0) + data.get("grid_to_battery_kw", 0)
                data["total_grid_import_kw_display"] = data.get("total_grid_import_kw", 0) * power_display_multiplier 
                data["total_grid_export_kw"] = data.get("battery_to_grid_kw", 0) + data.get("solar_to_grid_kw", 0)
                data["total_grid_export_kw_display"] = data.get("total_grid_export_kw", 0) * power_display_multiplier 
                              
                # Loss power
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
                data["battery_loss_kw_display"] = data.get("battery_loss_kw", 0) * power_display_multiplier 
                
                # Costs
                price_eur_kwh = data.get("spot_price_cents_per_kwh", 0) / 100
                data["net_savings_rate"] = (data["battery_discharge_total_kw"] * price_eur_kwh) - (data.get("grid_to_battery_kw", 0) * price_eur_kwh)
                
                # Charge efficiency
                solar = data.get("solar_to_battery_kw", 0)
                grid = data.get("grid_to_battery_kw", 0)
                battery_power = data.get("battery_power_kw")

                charge_input = solar + grid
                stored_power = abs(min(0, float(battery_power)))

                eff = 0
                if charge_input > 0:
                    eff = (stored_power / charge_input) * 100
                    
                data["battery_charge_efficiency"] = round(min(eff, 100), 1)
                    
                # Discharge efficiency
                house = data.get("battery_to_house_kw", 0)
                grid = data.get("battery_to_grid_kw", 0)
                battery_power = data.get("battery_power_kw")

                battery_output = max(0, float(battery_power))
                delivered = house + grid

                eff = 0
                if battery_output > 0:
                    eff = (delivered / battery_output) * 100
                    
                data["battery_discharge_efficiency"] = round(min(eff, 100), 1)
                    
                # Time-to-target sensors
                battery_capacity = self.entry.options.get(CONF_BATTERY_CAPACITY, self.entry.data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY))

                # Time to 90% charge
                data["time_to_90_percent"] = self.calculate_target_time(
                    data.get("state_of_charge_percent", 0),
                    battery_power,
                    90,
                    battery_capacity
                )
                
                # Time to 15% discharge
                data["time_to_15_percent"] = self.calculate_target_time(
                    data.get("state_of_charge_percent", 0),
                    battery_power,
                    15,
                    battery_capacity
                )
    
                _LOGGER.debug("Kotiakku data received: %s", data)

                return data

        except Exception as err:
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
