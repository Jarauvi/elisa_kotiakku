"""Constants for the Elisa Kotiakku integration."""
from homeassistant.const import Platform

# The unique domain identifier for this integration
# This matches the folder name and is used throughout the code to group entities and data
DOMAIN = "elisa_kotiakku"

# This list tells Home Assistant which files (sensor.py, binary_sensor.py, etc.)
# to load during setup and dismantle during unload.
PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

# === API ===
SECTION_API_SETTINGS = "api_settings"
CONF_API_KEY = "api_key"
CONF_URL = "url"
DEFAULT_URL = "https://residential.gridle.com/api/public/measurements"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 300

# === BATTERY ===
SECTION_BATTERY_SETTINGS = "battery_settings"
CONF_POWER_UNIT = "power_unit"
CONF_POWER_DECIMALS = 3
UNIT_W = "W"
UNIT_KW = "kW"
DEFAULT_POWER_UNIT = UNIT_KW
CONF_BATTERY_CAPACITY = "battery_capacity"
DEFAULT_BATTERY_CAPACITY = 21.0
MIN_BATTERY_CAPACITY = 14.0
MAX_BATTERY_CAPACITY = 42.0

# Hardware Metadata
MANUFACTURER = "Huawei (Elisa)"
MODEL = "FusionSolar LUNA2000"
DEFAULT_NAME = "Kotiakku"

# === CURRENCY ===
SECTION_CURRENCY_SETTINGS = "currency_settings"
CONF_ADD_TAX = "add_tax"
DEFAULT_ADD_TAX = False
CONF_TAX_PERCENTAGE = "tax_percentage"
DEFAULT_TAX_PERCENTAGE = 25.5
CONF_TRANSFER_PRICING = "transfer_pricing"
TRANSFER_IGNORE = "ignore_transfer"
TRANSFER_FIXED = "fixed_transfer"
TRANSFER_SEASONAL = "seasonal_transfer"
TRANSFER_DAY_NIGHT = "day_night_transfer"
DEFAULT_TRANSFER_PRICING = TRANSFER_IGNORE
CONF_FIXED_TRANSFER_PRICE = "transfer_price"
DEFAULT_FIXED_TRANSFER_PRICE = 4.5
CONF_DAY_START = "day_start"
DEFAULT_DAY_START = "07:00:00"
CONF_NIGHT_START = "night_start"
DEFAULT_NIGHT_START = "22:00:00"
CONF_DAY_PRICE = "day_price"
DEFAULT_DAY_PRICE = 7.0
CONF_NIGHT_PRICE = "night_price"
DEFAULT_NIGHT_PRICE = 3.0
CONF_WINTER_START_MONTH = "winter_start_month"
DEFAULT_WINTER_START_MONTH = 10
CONF_SUMMER_START_MONTH = "summer_start_month"
DEFAULT_SUMMER_START_MONTH = 5
CONF_WINTER_DAY_PRICE = "winter_day_price"
DEFAULT_WINTER_DAY_PRICE = 7.0
CONF_WINTER_NIGHT_PRICE = "winter_night_price"
DEFAULT_WINTER_NIGHT_PRICE = 5.0
CONF_SUMMER_DAY_PRICE = "summer_day_price"
DEFAULT_SUMMER_DAY_PRICE = 7.0
CONF_SUMMER_NIGHT_PRICE = "summer_night_price"
DEFAULT_SUMMER_NIGHT_PRICE = 5.0

def get_config_parameter(config_entry, section, key, fallback):
    """
    Look up a value in config_entry.options first (nested),
    then config_entry.data (nested), then fallback.
    """
    if section in config_entry.options:
        if key in config_entry.options[section]:
            return config_entry.options[section][key]
            
    if section in config_entry.data:
        if key in config_entry.data[section]:
            return config_entry.data[section][key]
            
    return fallback