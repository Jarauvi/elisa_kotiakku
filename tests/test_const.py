"""Tests for Elisa Kotiakku constants."""
from custom_components.elisa_kotiakku import const

def test_constants():
    """Verify that essential constants remain unchanged."""
    # Ensure the DOMAIN matches the folder name (crucial for HACS/HA)
    assert const.DOMAIN == "elisa_kotiakku"
    
    # Verify Manufacturer and Model for Device Registry consistency
    assert const.MANUFACTURER == "Huawei (Elisa)"
    assert const.MODEL == "FusionSolar LUNA2000"

def test_scan_intervals():
    """Verify that scan intervals are within safe limits."""
    # Ensure the default isn't faster than the minimum
    assert const.DEFAULT_SCAN_INTERVAL >= const.MIN_SCAN_INTERVAL
    
    # Safety check: Ensure the minimum interval is at least 2 minutes (120s)
    # This prevents accidental API hammering during development.
    assert const.MIN_SCAN_INTERVAL >= 120

def test_config_keys():
    """Verify configuration keys are correctly named."""
    # These must match your strings.json and config_flow.py keys
    assert const.CONF_API_KEY == "api_key"
    assert const.CONF_URL == "url"
    assert const.CONF_SCAN_INTERVAL == "scan_interval"