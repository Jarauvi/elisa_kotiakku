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
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from .const import DOMAIN, MANUFACTURER, MODEL, CONF_NAME, DEFAULT_NAME

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
      "spot_price_cents_per_kwh":  "mdi:cash-fast"
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
        KotiakkuEnergySensor(coordinator, "battery_energy_kwh", "battery_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_energy_kwh", "solar_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_energy_kwh", "grid_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "house_energy_kwh", "house_power_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_house_kwh", "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_battery_kwh", "solar_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "solar_to_grid_kwh", "solar_to_grid_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_house_kwh", "grid_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "grid_to_battery_kwh", "grid_to_battery_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_house_kwh", "battery_to_house_kw", device_id, device_slug, entry),
        KotiakkuEnergySensor(coordinator, "battery_to_grid_kwh", "battery_to_grid_kw", device_id, device_slug, entry),

        # Combined Energy Sensors - Sum multiple power flows before calculating energy
        KotiakkuSumEnergySensor(
            coordinator, 
            "total_battery_charge_kwh", 
            ["solar_to_battery_kwh", "grid_to_battery_kwh"], 
            device_id, device_slug, entry
        ),

        KotiakkuSumEnergySensor(
            coordinator, 
            "total_grid_export_kwh", 
            ["solar_to_grid_kwh", "battery_to_grid_kwh"], 
            device_id, device_slug, entry
        ),

        # Specialized Sensors - Binary, Temperature, and Percentages
        KotiakkuTemperatureSensor(coordinator, "battery_temperature_c", device_id, device_slug, entry),
        KotiakkuBatterySensor(coordinator, "state_of_charge_percent", device_id, device_slug, entry),
        KotiakkuPriceSensor(coordinator, "spot_price_cents_per_kwh", device_id, device_slug, entry),
    ]

    # Register entities in HA
    async_add_entities(sensors)

class KotiakkuSensor(CoordinatorEntity, SensorEntity):
    """Base sensor class for Elisa Kotiakku.
    
    Inherits from CoordinatorEntity to handle automatic data updates from the API
    and SensorEntity for standard Home Assistant sensor behavior.
    """

    _attr_has_entity_name = True  # Ensures 'name' comes from translation files

    def __init__(self, coordinator, key, device_name, device_slug, entry):
        """Initialize the base sensor with shared properties."""
        super().__init__(coordinator)
        self.key = key
        self._device_name = device_name
        self._entry = entry
        
        # Unique ID prevents duplicate entities and allows UI renaming
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        
        # Standardized entity_id (e.g., sensor.mybattery_solar_power_kw)
        self.entity_id = f"sensor.{device_slug}_{key}"
        
        # Link to translations and state tracking
        self._attr_translation_key = key
        self._attr_state_class = SensorStateClass.MEASUREMENT
        
        # Apply custom icon if defined in ICON_MAP
        if ICON_MAP.get(key) != None:
            self._attr_icon = ICON_MAP.get(key)

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

class KotiakkuEnergySensor(KotiakkuSensor, RestoreEntity):
    """Calculates Energy (kWh) from Power (kW) via Riemann sum.
    
    Inherits RestoreEntity to ensure energy totals are saved across HA restarts.
    This class performs a mathematical integration of power over time.
    """

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, key, power_key, device_id, device_slug, entry):
        """Initialize energy sensor with a reference to its source power key."""
        super().__init__(coordinator, key, device_id, device_slug, entry)
        self._power_key = power_key
        self._state = 0.0
        self._last_run = None

    async def async_added_to_hass(self):
        """Called when entity is added to HA. Restores previous state from database."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            try:
                self._state = float(state.state)
            except ValueError:
                self._state = 0.0
    
    @property
    def native_value(self):
        """Calculate and return the cumulative energy total.
        
        Uses the time difference between the current update and the last update
        to add (Power * Time) to the total state.
        """
        # Get the timestamp of the last successful API update
        now = self.coordinator.last_update_success or dt_util.utcnow()

        if self.coordinator.data is None:
            return round(self._state, 4)

        power = self.coordinator.data.get(self._power_key)
        
        if power is None:
            return round(self._state, 4)

        # Initial run sets the timestamp without adding energy
        if self._last_run is None:
            self._last_run = now
            return round(self._state, 4)

        # Calculate time delta in hours (for kWh)
        diff = (now - self._last_run).total_seconds() / 3600
        
        # Accumulate energy if time has elapsed
        if diff > 0:
            self._state += float(power) * diff
            self._last_run = now
            
        return round(self._state, 4)

class KotiakkuSumEnergySensor(KotiakkuEnergySensor):
    """Calculates Energy (kWh) by summing multiple power sources.
    
    Useful for 'Total Grid Export' where multiple power flows contribute 
    to a single energy total.
    """

    def __init__(self, coordinator, key, power_keys, device_id, device_slug, entry):
        """Initialize with a list of power keys to be summed."""
        # Initialize parent with the first key in the list as a placeholder
        super().__init__(coordinator, key, power_keys[0], device_id, device_slug, entry)
        self._power_keys = power_keys 

    @property
    def native_value(self):
        """Sum all configured power sources and integrate over time."""
        now = self.coordinator.last_update_success or dt_util.utcnow()

        if self.coordinator.data is None:
            return round(self._state, 4)

        # Sum values from all source keys, defaulting to 0 if missing
        total_power = sum(
            float(self.coordinator.data.get(k, 0) or 0) for k in self._power_keys
        )

        if self._last_run is None:
            self._last_run = now
            return round(self._state, 4)

        diff = (now - self._last_run).total_seconds() / 3600
        
        if diff > 0:
            self._state += total_power * diff
            self._last_run = now
            
        return round(self._state, 4)

# --- Subclasses for Specific Measurement Types ---
# These define the 'Device Class' which tells HA how to display the sensor
# and which icons/graphs to use automatically.

class KotiakkuPowerSensor(KotiakkuSensor):
    """Sensor for Power (kW) measurements."""
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.KILO_WATT

class KotiakkuTemperatureSensor(KotiakkuSensor):
    """Sensor for Temperature (C) measurements."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

class KotiakkuBatterySensor(KotiakkuSensor):
    """Sensor for Battery State of Charge (%)."""
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE

class KotiakkuPriceSensor(KotiakkuSensor):
    """Sensor for Electricity Spot Price."""
    _attr_native_unit_of_measurement = "c/kWh"