"""Sensors for Elisa Kotiakku integration."""

from homeassistant.util import dt as dt_util
from homeassistant.components.sensor import (
    SensorEntity,
    RestoreEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    UnitOfPower,
    UnitOfTemperature,
    UnitOfEnergy,
    PERCENTAGE,
)

from homeassistant.const import UnitOfTime
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from .const import DOMAIN, MANUFACTURER, MODEL, CONF_NAME, DEFAULT_NAME, CONF_POWER_UNIT, DEFAULT_POWER_UNIT, UNIT_W, CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY

# Mapping of sensor keys to Material Design Icons (MDI)
# If a key is not here or set to None, HA will fall back to DeviceClass defaults
ICON_MAP = {
    "battery_power_kw": "mdi:home-battery",
    "battery_temperature_c": None,
    "state_of_charge_percent": None,
    "solar_power_kw": "mdi:solar-power",
    "grid_power_kw": "mdi:transmission-tower",
    "house_power_kw": "mdi:home-lightning-bolt",
    "solar_to_house_kw": "mdi:solar-power-variant",
    "solar_to_battery_kw": "mdi:solar-power-variant",
    "solar_to_grid_kw": "mdi:solar-power-variant",
    "grid_to_house_kw": "mdi:transmission-tower-export",
    "grid_to_battery_kw": "mdi:transmission-tower-export",
    "battery_to_house_kw": "mdi:home-battery",
    "battery_to_grid_kw": "mdi:home-battery",
    "battery_energy_kwh": "mdi:home-battery",
    "solar_energy_kwh": "mdi:solar-power-variant",
    "grid_energy_kwh": "mdi:transmission-tower-export",
    "house_energy_kwh": "mdi:home-lightning-bolt",
    "solar_to_house_kwh": "mdi:solar-power-variant",
    "solar_to_battery_kwh": "mdi:solar-power-variant",
    "solar_to_grid_kwh": "mdi:solar-power-variant",
    "grid_to_house_kwh": "mdi:transmission-tower-export",
    "grid_to_battery_kwh": "mdi:transmission-tower-export",
    "battery_to_house_kwh": "mdi:home-battery",
    "battery_to_grid_kwh": "mdi:home-battery",
    "total_battery_charge_kwh": "mdi:battery-charging",
    "total_grid_export_kwh": "mdi:transmission-tower-import",
    "spot_price_cents_per_kwh":  "mdi:cash-fast",
    "battery_efficiency_ratio": "mdi:percent"
    }

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor platform from a ConfigEntry.
    
    This is called by Home Assistant during integration startup. 
    It initializes all sensor entities and adds them to the system.
    """
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Identify the device - using entry.title (set during config) or defaults
    device_id = entry.title or entry.data.get(CONF_NAME, DEFAULT_NAME)
    device_slug = slugify(device_id)
    battery_capacity = entry.data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)

    sensors = [
        # Power Sensors (kW) - Instantaneous flow measurements
        KotiakkuPowerSensor(coordinator, "battery_power_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "solar_power_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "grid_power_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "house_power_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "solar_to_house_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "solar_to_grid_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "grid_to_house_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "grid_to_battery_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "battery_to_house_kw", device_id, device_slug, entry),
        KotiakkuPowerSensor(coordinator, "battery_to_grid_kw", device_id, device_slug, entry),
        
        # Energy Sensors (kWh) - Calculated totals using Riemann sum integration
        # These take a Power sensor key as input to calculate the Energy over time
        KotiakkuEnergySensor(coordinator, "solar_energy_kwh", "solar_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_house_kwh", "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_battery_kwh", "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_grid_kwh", "solar_to_grid_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_house_kwh", "grid_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_battery_kwh", "grid_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_house_kwh", "battery_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_grid_kwh", "battery_to_grid_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "house_energy_kwh", "house_power_kw", device_id, device_slug, entry),

        KotiakkuSumEnergySensor(coordinator, "total_battery_charge_kwh", ["solar_to_battery_kwh", "grid_to_battery_kwh"], device_id, device_slug, entry),
        KotiakkuSumEnergySensor(coordinator, "total_battery_discharge_kwh", ["battery_to_house_kwh", "battery_to_grid_kwh"], device_id, device_slug, entry),
        KotiakkuSumEnergySensor(coordinator, "total_grid_import_kwh", ["grid_to_house_kwh", "grid_to_battery_kwh"], device_id, device_slug, entry),
        KotiakkuSumEnergySensor(coordinator, "total_grid_export_kwh", ["solar_to_grid_kwh", "battery_to_grid_kwh"], device_id, device_slug, entry),

        # Specialized Sensors
        KotiakkuTemperatureSensor(coordinator, "battery_temperature_celsius", device_id, device_slug, entry),
        KotiakkuBatterySensor(coordinator, "state_of_charge_percent", device_id, device_slug, entry),
        KotiakkuPriceSensor(coordinator, "spot_price_cents_per_kwh", device_id, device_slug, entry),
        KotiakkuChargeEfficiencySensor(coordinator, "battery_charge_efficiency", device_id, device_slug, entry),
        KotiakkuDischargeEfficiencySensor(coordinator, "battery_discharge_efficiency", device_id, device_slug, entry),
        KotiakkuBatteryLossSensor(coordinator, "battery_loss_kw", device_id, device_slug, entry),
        KotiakkuEfficiencySensor(
            coordinator,
            "battery_efficiency_ratio",
            "total_battery_discharge_kwh",
            "total_battery_charge_kwh",
            device_id,
            device_slug,
            entry
        ),
        KotiakkuTimeTargetSensor(
            coordinator, "time_to_90_percent", 90, battery_capacity, 
            device_id, device_slug, entry
        ),
        KotiakkuTimeTargetSensor(
            coordinator, "time_to_15_percent", 15, battery_capacity, 
            device_id, device_slug, entry
        ),
        KotiakkuNetSavingsRateSensor(coordinator, "net_savings_rate", device_id, device_slug, entry),
        KotiakkuCycleCounterSensor(
            coordinator, 
            "battery_cycle_count", 
            "total_battery_discharge_kwh", 
            battery_capacity, 
            device_id, 
            device_slug, 
            entry
        ),
        KotiakkuBatteryStateSensor(coordinator, "battery_state", device_id, device_slug, entry)

    ]

    # Register entities in HA
    async_add_entities(sensors)

class KotiakkuSensor(CoordinatorEntity, SensorEntity):
    """Base sensor class for Elisa Kotiakku.
    
    Inherits from CoordinatorEntity to handle automatic data updates from the API
    and SensorEntity for standard Home Assistant sensor behavior.
    """

    _attr_has_entity_name = True  # Ensures 'name' comes from translation files
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator, key, device_name, device_slug, entry):
        """Initialize the base sensor with shared properties."""
        super().__init__(coordinator)
        self.key = key
        self._device_name = device_name
        self._entry = entry
        
        # Unique ID prevents duplicate entities and allows UI renaming
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        
        # Link to translations and state tracking
        self._attr_translation_key = key
        #self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Apply custom icon if defined in ICON_MAP
        if ICON_MAP.get(key) != None:
            self._attr_icon = ICON_MAP.get(key)

        self.entity_id = f"sensor.{device_slug}_{key}"
        

    @property
    def device_info(self):
        """Link this entity to the 'Elisa Kotiakku' device in the UI."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._device_name,
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }

    @property
    def native_value(self):
        """Return the current value from the coordinator's cached data."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get(self.key)

    @property
    def _unit_pref(self):
        return self._entry.options.get(
            CONF_POWER_UNIT, 
            self._entry.data.get(CONF_POWER_UNIT, DEFAULT_POWER_UNIT)
        )

class KotiakkuEnergySensor(KotiakkuSensor, RestoreEntity):
    """Calculates Energy (kWh) from Power (kW) via Riemann sum.
    
    Inherits RestoreEntity to ensure energy totals are saved across HA restarts.
    This class performs a mathematical integration of power over time.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, key, power_key, device_id, device_slug, entry, direction=None):
        """Initialize energy sensor with a reference to its source power key."""
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._power_key = power_key
        self._state = None
        self._last_run = None
        self._restored = False
        self._direction = direction

    async def async_added_to_hass(self):
        """Called when entity is added to HA. Restores previous state from database."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None and state.state not in ("unknown", "unavailable"):
            try:
                self._state = float(state.state)
            except ValueError:
                self._state = 0.0
        else:
            self._state = 0.0
    
        if self._state is not None:
            self._restored = True
            self._last_run = dt_util.utcnow()
            self.async_write_ha_state()

    @property
    def native_value(self):
        """Calculate and return the cumulative energy total.
        
        Uses the time difference between the current update and the last update
        to add (Power * Time) to the total state.
        """

        if not self._restored:
            return None

        # Get the timestamp of the last successful API update
        now = dt_util.utcnow()

        if self.coordinator.data is None:
            return round(self._state, 3) if self._state is not None else 0.0

        power_val = self.coordinator.data.get(self._power_key)
        
        # Apply Directional Filter

        if self._direction == "pos":
            # Only count positive power (discharging/exporting)
            power_val = max(0, power_val)
        elif self._direction == "neg":
            # Only count negative power (charging/importing)
            power_val = abs(min(0, power_val))
        else:
            # Fallback to absolute if no direction specified
            power_val = abs(power_val)

        # Initial run sets the timestamp without adding energy
        if self._last_run is None:
            self._last_run = now
            return round(self._state, 3)

        # Calculate time delta in hours (for kWh)
        diff = (now - self._last_run).total_seconds() / 3600
        
        if diff > 0:
            new_state = (self._state or 0.0) + (power_val * diff)
            if self._state is None or new_state > self._state:
                self._state = new_state
            self._last_run = now
            
        return round(self._state, 3)
        
class KotiakkuSumEnergySensor(KotiakkuEnergySensor):
    """Sums multiple ENERGY entities (kWh), not power."""
    def __init__(self, coordinator, key, source_keys, device_id, device_slug, entry):
        # We don't use power_key here, so we pass None to parent
        super().__init__(coordinator, key, None, device_id, device_slug, entry)
        self._source_keys = source_keys
        self._device_slug = device_slug

    @property
    def native_value(self):
        total = 0.0
        for k in self._source_keys:
            # We look for the already calculated energy entities in the state machine
            state = self.hass.states.get(f"sensor.{self._device_slug}_{k}")
            if state and state.state not in ("unknown", "unavailable"):
                total += float(state.state)
        return round(total, 3)

class KotiakkuPowerSensor(KotiakkuSensor):
    """Sensor for Power (kW) measurements."""
    _attr_device_class = SensorDeviceClass.POWER

    @property
    def suggested_display_precision(self) -> int:
        """Return 0 decimals for Watts, 3 decimals for kiloWatts."""
        return 0 if self._unit_pref == UNIT_W else 3

    @property
    def native_unit_of_measurement(self):
        """Return W or kW based on user preference."""
        return UnitOfPower.WATT if self._unit_pref == UNIT_W else UnitOfPower.KILO_WATT

    @property
    def native_value(self):
        """Return the value, converted to Watts if necessary."""
        val = super().native_value
        if val is None:
            return None
            
        if self._unit_pref == UNIT_W:
            return round(float(val) * 1000)
        return round(val, 3)

class KotiakkuTemperatureSensor(KotiakkuSensor):
    """Sensor for Temperature (C) measurements."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

class KotiakkuBatterySensor(KotiakkuSensor):
    """Sensor for Battery State of Charge (%)."""
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 0

class KotiakkuPriceSensor(KotiakkuSensor):
    """Sensor for Electricity Spot Price."""
    _attr_native_unit_of_measurement = "c/kWh"

    @property
    def native_value(self):
        val = super().native_value
        if val is None:
            return None
        return round(float(val), 3)
    
class KotiakkuEfficiencySensor(KotiakkuSensor):
    """Calculates the Round Trip Efficiency (%) of the battery system.
    
    Formula: (Total Discharge kWh / Total Charge kWh) * 100
    """
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:percent"

    def __init__(self, coordinator, key, discharge_key, charge_key, device_id, device_slug, entry):
        """Initialize with keys for discharge and charge energy entities."""
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._discharge_key = discharge_key
        self._charge_key = charge_key
        self._device_slug = device_slug

    @property
    def native_value(self):
        """Calculate efficiency using the current states of Energy entities."""
        # Use the slugified entity IDs to pull directly from the HA state machine
        charge_state = self.hass.states.get(f"sensor.{self._device_slug}_{self._charge_key}")
        discharge_state = self.hass.states.get(f"sensor.{self._device_slug}_{self._discharge_key}")

        # Guard: If entities aren't ready yet, return None
        if not charge_state or not discharge_state:
            return None
            
        try:
            c = float(charge_state.state)
            d = float(discharge_state.state)
            
            # Avoid Division by Zero if the battery hasn't charged yet
            if c <= 0:
                return None
                
            # Efficiency calculation
            efficiency = (d / c) * 100
            
            # Cap at 100% to prevent weird spikes if sensors desync
            return round(min(efficiency, 100.0), 1)
            
        except (ValueError, TypeError):
            # Handles 'unknown' or 'unavailable' strings in the state machine
            return None
    
class KotiakkuChargeEfficiencySensor(KotiakkuSensor):
    """Instantaneous battery charge efficiency."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:battery-charging-70"
    _attr_translation_key = "battery_charge_efficiency"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return 0

        solar = data.get("solar_to_battery_kw", 0) or 0
        grid = data.get("grid_to_battery_kw", 0) or 0
        battery_power = data.get("battery_power_kw")

        if battery_power is None:
            return 0

        charge_input = solar + grid
        stored_power = abs(min(0, float(battery_power)))

        if charge_input <= 0:
            return 0

        eff = (stored_power / charge_input) * 100

        return round(min(eff, 100), 1)
    
class KotiakkuDischargeEfficiencySensor(KotiakkuSensor):
    """Instantaneous battery discharge efficiency."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    _attr_icon = "mdi:battery-arrow-down"
    _attr_translation_key = "battery_discharge_efficiency"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return 0

        house = data.get("battery_to_house_kw", 0) or 0
        grid = data.get("battery_to_grid_kw", 0) or 0
        battery_power = data.get("battery_power_kw")

        if battery_power is None:
            return 0

        battery_output = max(0, float(battery_power))
        delivered = house + grid

        if battery_output <= 0:
            return 0

        eff = (delivered / battery_output) * 100

        return round(min(eff, 100), 1)
    
class KotiakkuBatteryLossSensor(KotiakkuPowerSensor):
    """Instantaneous battery conversion loss."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_icon = "mdi:heat-wave"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        solar = data.get("solar_to_battery_kw", 0) or 0
        grid = data.get("grid_to_battery_kw", 0) or 0
        house = data.get("battery_to_house_kw", 0) or 0
        grid_out = data.get("battery_to_grid_kw", 0) or 0
        battery_power = data.get("battery_power_kw")

        if battery_power is None:
            return None

        battery_power = float(battery_power)

        if battery_power < 0:
            charge_input = solar + grid
            stored = abs(battery_power)
            loss = charge_input - stored

        elif battery_power > 0:
            delivered = house + grid_out
            loss = battery_power - delivered

        else:
            return 0

        val = max(loss, 0)
        if self._unit_pref == UNIT_W:
            return round(float(val) * 1000)
        return round(float(val), 3)
    
class KotiakkuTimeTargetSensor(KotiakkuSensor):
    """Estimates time remaining to reach a specific SoC target."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "min" 
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, key, target_soc, battery_capacity, device_id, device_slug, entry):
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._target_soc = target_soc
        self._battery_capacity = float(battery_capacity)

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        current_soc = float(data.get("state_of_charge_percent", 0))
        power_kw = float(data.get("battery_power_kw", 0))

        if (self._target_soc > current_soc and power_kw >= 0) or \
           (self._target_soc < current_soc and power_kw <= 0):
            if abs(current_soc - self._target_soc) < 0.5:
                return 0
            
        is_charging = power_kw < 0
        is_discharging = power_kw > 0
        
        moving_to_target = (self._target_soc > current_soc and is_charging) or \
                           (self._target_soc < current_soc and is_discharging)

        if not moving_to_target or abs(power_kw) < 0.05:
            return 0

        target_energy = self._battery_capacity * (self._target_soc / 100.0)
        current_energy = self._battery_capacity * (current_soc / 100.0)
        energy_diff = abs(target_energy - current_energy)
        
        hours_remaining = energy_diff / abs(power_kw)
        if hours_remaining is None:
            return None
        
        return round(hours_remaining * 60)

class KotiakkuNetSavingsRateSensor(KotiakkuSensor):
    """Real-time net savings rate in €/h (Earnings minus Charging Costs)."""
    _attr_native_unit_of_measurement = "€/h"
    _attr_suggested_display_precision = 3
    _attr_icon = "mdi:calculator"

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        price_eur_kwh = float(data.get("spot_price_cents_per_kwh", 0)) / 100

        discharge_kw = (data.get("battery_to_house_kw", 0) or 0) + (data.get("battery_to_grid_kw", 0) or 0)
        earnings = discharge_kw * price_eur_kwh

        grid_charge_kw = data.get("grid_to_battery_kw", 0) or 0
        costs = grid_charge_kw * price_eur_kwh

        return round(earnings - costs, 3)

class KotiakkuCycleCounterSensor(KotiakkuSensor):
    """Calculates total battery cycles (Total Discharge / Rated Capacity)."""
    _attr_translation_key = "battery_cycle_count"
    _attr_native_unit_of_measurement = "cycles"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator, key, discharge_energy_key, capacity, device_id, device_slug, entry):
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._discharge_key = discharge_energy_key
        self._capacity = float(capacity)

    @property
    def suggested_display_precision(self) -> int:
        return 0

    @property
    def native_value(self):
        discharge_entity = self.entity_id.replace("battery_cycle_count", self._discharge_key)
        discharge_state = self.hass.states.get(discharge_entity)
        
        if discharge_state is None or discharge_state.state in ("unknown", "unavailable") or self._capacity <= 0:
            return None
        
        cycles = float(discharge_state.state) / self._capacity
        return round(cycles, 0)
    
class KotiakkuBatteryStateSensor(KotiakkuSensor):
    """Shows the current state of the battery."""
    _attr_state_class = None
    _attr_native_unit_of_measurement = None
    _attr_suggested_display_precision = None

    @property
    def native_value(self):
        data = self.coordinator.data
        if not data:
            return None

        power_kw = float(data.get("battery_power_kw", 0))
        
        # Deadzone of 50W
        if power_kw < -0.05:
            return "charging"
        elif power_kw > 0.05:
            return "discharging"
        else:
            return "idle"

    @property
    def icon(self):
        state = self.native_value
        if state == "charging":
            return "mdi:battery-charging"
        elif state == "discharging":
            return "mdi:battery-arrow-down"
        return "mdi:battery"