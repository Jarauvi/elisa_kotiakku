"""Global fixtures for Elisa Kotiakku tests."""
import pytest
from unittest.mock import MagicMock
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.elisa_kotiakku.const import DOMAIN

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield

@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Kotiakku",
        data={
            "name": "Kotiakku",
            "url": "http://127.0.0.1:8000/api/v1/status",
            "api_key": "test_key",
        },
        entry_id="test_entry_id",
    )

@pytest.fixture
def mock_coordinator():
    """Return a mock coordinator."""
    coordinator = MagicMock()
    coordinator.data = {}
    coordinator.last_update_success = None
    return coordinator