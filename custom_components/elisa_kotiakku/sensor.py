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

from homeassistant.helpers import entity_registry as er
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
    "battery_efficiency_ratio": "mdi:percent",
    "battery_charge_efficiency": "mdi:battery-charging-70",
    "battery_discharge_efficiency": "mdi:battery-arrow-down",
    "battery_loss_kw": "mdi:heat-wave",
    "time_to_90_percent": "mdi:clock-outline",
    "time_to_15_percent": "mdi:clock-outline",
    "net_savings_rate": "mdi:calculator",
    "battery_loss_kwh": "mdi:heat-wave"
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
    battery_capacity = entry.options.get(CONF_BATTERY_CAPACITY, entry.data.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY))

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
        KotiakkuPowerSensor(coordinator, "battery_loss_kw", device_id, device_slug, entry),
        
        # Energy Sensors (kWh) - Calculated totals using Riemann sum integration
        # These take a Power sensor key as input to calculate the Energy over time
        KotiakkuEnergySensor(coordinator, "solar_energy_kwh", "solar_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_house_kwh", "solar_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_battery_kwh", "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_grid_kwh", "solar_to_grid_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_house_kwh", "grid_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_battery_kwh", "grid_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_house_kwh", "battery_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_grid_kwh", "battery_to_grid_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "house_energy_kwh", "house_power_kw", device_id, device_slug, entry),

        KotiakkuEnergySensor(coordinator, "total_battery_charge_kwh", "battery_charge_total_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "total_battery_discharge_kwh", "battery_discharge_total_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "total_grid_import_kwh", "total_grid_import_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "total_grid_export_kwh", "total_grid_export_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_loss_kwh", "battery_loss_kw", device_id, device_slug, entry),


        #KotiakkuSumEnergySensor(coordinator, "total_battery_charge_kwh", ["solar_to_battery_kwh", "grid_to_battery_kwh"], device_id, device_slug, entry),
        #KotiakkuSumEnergySensor(coordinator, "total_battery_discharge_kwh", ["battery_to_house_kwh", "battery_to_grid_kwh"], device_id, device_slug, entry),
        #KotiakkuSumEnergySensor(coordinator, "total_grid_import_kwh", ["grid_to_house_kwh", "grid_to_battery_kwh"], device_id, device_slug, entry),
        #KotiakkuSumEnergySensor(coordinator, "total_grid_export_kwh", ["solar_to_grid_kwh", "battery_to_grid_kwh"], device_id, device_slug, entry),

        # Specialized Sensors
        KotiakkuTemperatureSensor(coordinator, "battery_temperature_celsius", device_id, device_slug, entry),
        KotiakkuBatterySensor(coordinator, "state_of_charge_percent", device_id, device_slug, entry),
        KotiakkuPriceSensor(coordinator, "spot_price_cents_per_kwh", device_id, device_slug, entry),
        KotiakkuChargeEfficiencySensor(coordinator, "battery_charge_efficiency", device_id, device_slug, entry),
        KotiakkuDischargeEfficiencySensor(coordinator, "battery_discharge_efficiency", device_id, device_slug, entry),
        KotiakkuEfficiencySensor(
            coordinator,
            "battery_efficiency_ratio",
            "total_battery_discharge_kwh",
            "total_battery_charge_kwh",
            device_id,
            device_slug,
            entry
        ),
        KotiakkuTimeTargetSensor(coordinator, "time_to_90_percent", device_id, device_slug, entry),
        KotiakkuTimeTargetSensor(coordinator, "time_to_15_percent", device_id, device_slug, entry),
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
        KotiakkuBatteryStateSensor(coordinator, "battery_state", device_id, device_slug, entry),
        KotiakkuTotalSavingsSensor(
            coordinator, 
            "total_savings_eur", 
            "net_savings_rate", 
            device_id, 
            device_slug, 
            entry
        ),

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

class KotiakkuEnergySensor(RestoreEntity, KotiakkuSensor):
    """Calculates Energy (kWh) from Power (kW) via Riemann sum.
    
    Inherits RestoreEntity to ensure energy totals are saved across HA restarts.
    This class performs a mathematical integration of power over time.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_last_reset = None

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
    
        self._restored = True
        self._last_run = dt_util.utcnow()
        
    def _handle_coordinator_update(self) -> None:
        """Calculate and return the cumulative energy total.
        
        Uses the time difference between the current update and the last update
        to add (Power * Time) to the total state.
        """

        if not self._restored:
            return

        # Get the timestamp of the last successful API update
        now = dt_util.utcnow()

        if self.coordinator.data is None:
            return

        power_val = self.coordinator.data.get(self._power_key)
        if power_val is None:
            return
        power_val = abs(power_val)

        # Initial run sets the timestamp without adding energy
        if self._last_run is None:
            self._last_run = now
            return

        # Calculate time delta in hours (for kWh)
        diff = (now - self._last_run).total_seconds() / 3600
        
        if 2.0 > diff > 0:
            new_state = (self._state or 0.0) + (power_val * diff)
            if self._state is None or new_state > self._state:
                self._state = new_state
        
        self._last_run = now
        super()._handle_coordinator_update()
    
    @property
    def native_value(self):
        if not self._restored:
            return None
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
        return self.coordinator.data.get("power_decimals", 3)

    @property
    def suggested_unit_of_measurement(self):
        return self.coordinator.data.get("power_display_unit", "kW")

    @property
    def native_unit_of_measurement(self):
        """Return W or kW based on user preference."""
        return self.coordinator.data.get("power_display_unit", "kW")

    @property
    def native_value(self):
        # Point to the '_display' version created in the coordinator
        return self.coordinator.data.get(f"{self.key}_display")

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
    
class KotiakkuEfficiencySensor(KotiakkuSensor):
    """Calculates the Round Trip Efficiency (%) of the battery system.
    
    Formula: (Total Discharge kWh / Total Charge kWh) * 100
    """
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, key, discharge_unique_suffix, charge_unique_suffix, device_id, device_slug, entry):
        """Initialize with keys for discharge and charge energy entities."""
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._discharge_suffix = discharge_unique_suffix
        self._charge_suffix = charge_unique_suffix
        self._entry_id = entry.entry_id

    @property
    def native_value(self):
        """Calculate efficiency using the current states of Energy entities."""
        # Use the slugified entity IDs to pull directly from the HA state machine
        ent_reg = er.async_get(self.hass)
        charge_uid = f"{self._entry_id}_{self._charge_suffix}"
        discharge_uid = f"{self._entry_id}_{self._discharge_suffix}"
        charge_entity_id = ent_reg.async_get_entity_id("sensor", "elisa_kotiakku", charge_uid)
        discharge_entity_id = ent_reg.async_get_entity_id("sensor", "elisa_kotiakku", discharge_uid)

        if not charge_entity_id or not discharge_entity_id:
            return None
        
        charge_state = self.hass.states.get(charge_entity_id)
        discharge_state = self.hass.states.get(discharge_entity_id)

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
    
class KotiakkuDischargeEfficiencySensor(KotiakkuSensor):
    """Instantaneous battery discharge efficiency."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_suggested_display_precision = 1
    
class KotiakkuTimeTargetSensor(KotiakkuSensor):
    """Estimates time remaining to reach a specific SoC target."""
    _attr_suggested_display_precision = 0
    _attr_device_class = None
    _attr_state_class = None 
    _attr_unit_of_measurement = None
    _attr_suggested_display_precision = None

class KotiakkuNetSavingsRateSensor(KotiakkuSensor):
    """Real-time net savings rate in €/h (Earnings minus Charging Costs)."""
    _attr_native_unit_of_measurement = "€/h"
    _attr_suggested_display_precision = 3

class KotiakkuCycleCounterSensor(KotiakkuSensor):
    """Calculates total battery cycles (Total Discharge / Rated Capacity)."""
    _attr_translation_key = "battery_cycle_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_suggested_display_precision = 2
    _attr_icon = "mdi:sync"

    def __init__(self, coordinator, key, discharge_energy_key, capacity, device_id, device_slug, entry):
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._discharge_suffix = discharge_energy_key
        self._entry_id = entry.entry_id
        self._capacity = float(capacity)

    @property
    def suggested_display_precision(self) -> int:
        return 0

    @property
    def native_value(self):
        ent_reg = er.async_get(self.hass)
        discharge_uid = f"{self._entry_id}_{self._discharge_suffix}"
        discharge_entity_id = ent_reg.async_get_entity_id("sensor", "elisa_kotiakku", discharge_uid)

        if not discharge_entity_id:
            return None
        
        discharge_state = self.hass.states.get(discharge_entity_id)
        
        if discharge_state is None or discharge_state.state in ("unknown", "unavailable") or self._capacity <= 0:
            return None
        
        cycles = float(discharge_state.state) / self._capacity
        return int(cycles)
    
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

class KotiakkuTotalSavingsSensor(KotiakkuSensor, RestoreEntity):
    """Integrates Net Savings Rate (€/h) into Total Savings (€) using Riemann sum."""

    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = "€"
    _attr_icon = "mdi:cash-plus"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, key, rate_key, device_id, device_slug, entry):
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._rate_key = rate_key
        self._state = 0.0  # Initialize to 0.0
        self._last_run = None
        self._restored = False

    async def async_added_to_hass(self):
        """Restore previous savings total from the database."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None and state.state not in ("unknown", "unavailable"):
            try:
                self._state = float(state.state)
            except ValueError:
                self._state = 0.0
    
        self._restored = True
        self._last_run = dt_util.utcnow()
        # No need to write state here, the coordinator update will handle it
        
    def _handle_coordinator_update(self) -> None:
        """Calculate the new total exactly when the coordinator gets new data."""
        # 1. Check if we have data
        if self.coordinator.data is None:
            return

        rate_val = self.coordinator.data.get(self._rate_key)
        now = dt_util.utcnow()

        # 2. Skip if it's the very first run to establish a baseline time
        if self._last_run is None:
            self._last_run = now
            return

        # 3. Calculate the delta
        if rate_val is not None:
            diff = (now - self._last_run).total_seconds() / 3600
            if diff > 0:
                # The Math: Rate (€/h) * Time (h)
                self._state += float(rate_val) * diff
        
        # 4. Update the timestamp and tell HA to refresh the UI
        self._last_run = now
        super()._handle_coordinator_update() # IMPORTANT: Call the parent's update logic

    @property
    def native_value(self):
        # We just return the internal state that was calculated in the update handler
        if not self._restored:
            return None
        return round(self._state, 3)