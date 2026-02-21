"""Tests for Elisa Kotiakku diagnostics."""
from custom_components.elisa_kotiakku.diagnostics import async_get_config_entry_diagnostics

async def test_diagnostics_redaction(hass, mock_config_entry, mock_coordinator):
    """Verify that sensitive information is redacted in diagnostics."""
    mock_coordinator.data = {"battery_power_kw": 1.0, "api_key": "SECRET_KEY_123"}
    hass.data["elisa_kotiakku"] = {mock_config_entry.entry_id: mock_coordinator}

    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    # Check that 'api_key' is now '**REDACTED**'
    assert diag["data"]["api_key"] == "**REDACTED**"