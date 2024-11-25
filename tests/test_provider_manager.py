"""Tests for the provider manager."""
import pytest
from unittest.mock import MagicMock, patch
from schwarm.events.event import Event, EventType

from schwarm.models.provider_context import ProviderContextModel
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.provider_manager import ProviderManager, ProviderInitError
from schwarm.telemetry.telemetry_manager import TelemetryManager
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter
from typing import Any


class TestProvider(BaseProvider):
    """Test provider implementation."""
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestProvider2(BaseProvider):
    """Another test provider implementation for testing class lookup."""
    def __init__(self, config, **data):
        super().__init__(config, **data)
        self.priority = 1 
        
    def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestEventProvider(BaseEventHandleProvider):
    """Test event provider implementation."""
    def __init__(self, config, **data):
        super().__init__(config, **data)
        self.priority = 0 
    
    def initialize(self) -> None:
        """Initialize the provider."""
        pass
    
    def handle_event(self, event: Event, span=None) -> None:
        """Handle the given event."""
        pass


class TestConfig(BaseProviderConfig):
    """Test provider configuration."""


class TestEventConfig(BaseEventHandleProviderConfig):
    """Test event provider configuration."""


@pytest.fixture
def telemetry_manager(tmp_path):
    """Create a TelemetryManager instance for testing."""
    exporter = SqliteTelemetryExporter(db_path=str(tmp_path / "test_events.db"))
    return TelemetryManager(telemetry_exporters=[exporter], enabled_providers=["all"])


@pytest.fixture()
def manager(telemetry_manager):
    """Create a fresh provider manager instance."""
    # Reset the global instance
    ProviderManager._instance = None
    # Create new instance with telemetry
    return ProviderManager(telemetry_manager=telemetry_manager)


def test_global_pattern(telemetry_manager):
    """Test provider manager global pattern."""
    # Reset singleton for this test
    ProviderManager._instance = None
    manager1 = ProviderManager(telemetry_manager=telemetry_manager)
    manager2 = ProviderManager(telemetry_manager=telemetry_manager)
    assert manager1 is manager2


def test_initialize_global_provider(manager: ProviderManager):
    """Test initialization of global provider."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig(scope="global")
    provider = manager.create_provider("test_agent", config)
    
    assert provider.config == config
    assert provider in manager._providers["global"]
    
    provider2 = manager.create_provider("other_agent", config)
    assert provider2 in manager._providers["global"]


def test_initialize_scoped_provider(manager: ProviderManager):
    """Test initialization of scoped provider."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig(scope="scoped")
    provider = manager.create_provider("test_agent", config)
    
    assert provider.config == config
    assert provider in manager._providers["test_agent"]
    
    # Should create new instance for different agent
    provider2 = manager.create_provider("other_agent", config)
    assert provider is not provider2


def test_initialize_ephemeral_provider(manager: ProviderManager):
    """Test initialization of ephemeral provider."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig(scope="jit")
    provider1 = manager.create_provider("test_agent", config)
    provider2 = manager.create_provider("test_agent", config)
    
    # Should create new instance each time
    assert provider1 is not provider2


def test_get_provider(manager: ProviderManager):
    """Test provider retrieval."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig()
    provider = manager.create_provider("test_agent", config)
    
    # Should find provider by name
    assert manager.get_provider_by_name("test_agent", provider._provider_id) is provider
    
    # Should return None for non-existent provider
    assert manager.get_provider_by_name("test_agent", "non_existent") is None


def test_get_providers_by_class(manager: ProviderManager):
    """Test provider retrieval by class."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig()
    provider = manager.create_provider("test_agent", config)
    
    p_list = manager.get_providers_by_class(TestProvider)
    assert provider in p_list
    assert len(manager.get_providers_by_class(TestProvider2)) == 0


def test_provider_init_error(manager: ProviderManager):
    """Test handling of provider initialization error."""
    class NonExistentConfig(BaseProviderConfig):
        """Non-existent provider class."""
        pass
    
    config = NonExistentConfig()
    
    with pytest.raises(ProviderInitError) as exc_info:
        manager.create_provider("test_agent", config)
    assert "No provider implementation found" in str(exc_info.value)


def test_get_event_providers(manager: ProviderManager):
    """Test retrieval of event providers."""
    # Register provider classes
    manager._config_to_provider_map[TestConfig] = TestProvider
    manager._config_to_provider_map[TestEventConfig] = TestEventProvider
    
    # Create both regular and event providers
    regular_config = TestConfig(scope="global")
    event_config = TestEventConfig(scope="global")
    
    regular_provider = manager.create_provider("test_agent", regular_config)
    event_provider = manager.create_provider("test_agent", event_config)
    
    event_providers = manager.get_event_providers("global")
    assert len(event_providers) == 1
    assert event_providers[0] is event_provider


def test_get_all_providers_as_dict(manager: ProviderManager):
    """Test provider dictionary generation."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    # Create providers with different scopes
    global_config = TestConfig(scope="global")
    scoped_config = TestConfig(scope="scoped")
    
    global_provider = manager.create_provider("test_agent", global_config)
    global_provider._provider_id = "global_provider"
    scoped_provider = manager.create_provider("test_agent", scoped_config)
    scoped_provider._provider_id = "scoped_provider"
    
    providers_dict = manager._providers
    
    assert "global" in providers_dict
    assert "test_agent" in providers_dict
    assert len(providers_dict["global"]) == 1
    assert len(providers_dict["test_agent"]) == 1
    assert providers_dict["global"][0]._provider_id == "global_provider"
    assert providers_dict["test_agent"][0]._provider_id == "scoped_provider"


def test_trigger_event(manager: ProviderManager):
    """Test event triggering across providers."""
    # Register provider class
    manager._config_to_provider_map[TestEventConfig] = TestEventProvider
    
    # Create event providers with different priorities
    config1 = TestEventConfig()
    config2 = TestEventConfig()
    
    provider1 = manager.create_provider("test_agent", config1)
    provider2 = manager.create_provider("test_agent", config2)
    
    # Mock the providers and context
    mock_context = MagicMock(spec=ProviderContextModel)
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_context.current_agent = mock_agent
    event = Event(type=str(EventType.START), context=mock_context, agent_name="test_agent", timestamp="2021-01-01T00:00:00Z")
    
    # Trigger event
    result = manager.trigger_event(event)
    
    # Providers should be sorted by priority
    event_providers = manager.get_event_providers("test_agent")
    assert len(result) == len(event_providers)


def test_telemetry_integration(manager: ProviderManager):
    """Test telemetry integration with providers."""
    # Register provider class
    manager._config_to_provider_map[TestConfig] = TestProvider
    
    config = TestConfig(scope="global")
    provider = manager.create_provider("test_agent", config)
    
    # Verify provider has tracer
    assert hasattr(provider, "_tracer")
    assert provider._tracer is not None
