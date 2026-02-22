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

# Configuration keys used in the ConfigFlow (Step 1 setup)
# These keys match the 'data' keys in your config_flow.py and strings.json
CONF_API_KEY = "api_key"
CONF_URL = "url"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

#These are for selecting the power unit (W or kW)
CONF_POWER_UNIT = "power_unit"
UNIT_W = "W"
UNIT_KW = "kW"
DEFAULT_POWER_UNIT = UNIT_KW

# Hardware Metadata
# These are displayed in the 'Device Info' panel in Home Assistant
MANUFACTURER = "Huawei (Elisa)"
MODEL = "FusionSolar LUNA2000"

# Default configuration values
DEFAULT_NAME = "Kotiakku"

# Scan Interval settings (in seconds)
# DEFAULT_SCAN_INTERVAL: The default polling rate if the user doesn't specify one (5 minutes)
# MIN_SCAN_INTERVAL: The safety floor to prevent overwhelming the Elisa API/Huawei cloud
DEFAULT_SCAN_INTERVAL = 300
MIN_SCAN_INTERVAL = 120