"""Tests for the provider manager."""
import pytest
from unittest.mock import MagicMock, patch
from schwarm.events.event_types import EventType
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base import BaseProvider
from schwarm.provider.base import BaseProviderConfig
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.provider_manager import ProviderManager, ProviderInitError


class TestProvider(BaseProvider):
    """Test provider implementation."""
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestEventProvider(BaseEventHandleProvider):
    """Test event provider implementation."""
    priority: int = 0
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestConfig(BaseProviderConfig):
    """Test provider configuration."""
    def __init__(self, **data):
        data.update({
            "provider_name": data.get("provider_name", "test_provider"),
            "provider_type": "test",
            "provider_class": "tests.test_provider_manager.TestProvider",
            "scope": data.get("scope", "scoped")
        })
        super().__init__(**data)


class TestEventConfig(BaseProviderConfig):
    """Test event provider configuration."""
    def __init__(self, **data):
        data.update({
            "provider_name": data.get("provider_name", "test_event_provider"),
            "provider_type": "event",
            "provider_class": "tests.test_provider_manager.TestEventProvider",
            "scope": data.get("scope", "scoped")
        })
        super().__init__(**data)


@pytest.fixture
def manager():
    """Create a fresh provider manager instance."""
    # Reset the singleton instance
    ProviderManager._instance = None
    return ProviderManager()


def test_singleton_pattern():
    """Test provider manager singleton pattern."""
    manager1 = ProviderManager()
    manager2 = ProviderManager()
    assert manager1 is manager2


def test_initialize_singleton_provider(manager):
    """Test initialization of singleton provider."""
    config = TestConfig(scope="singleton")
    provider = manager.initialize_provider("test_agent", config)
    
    assert provider.config == config
    assert manager._global_providers[config.provider_name] is provider
    
    # Should return same instance for different agent
    provider2 = manager.initialize_provider("other_agent", config)
    assert provider is provider2


def test_initialize_scoped_provider(manager):
    """Test initialization of scoped provider."""
    config = TestConfig(scope="scoped")
    provider = manager.initialize_provider("test_agent", config)
    
    assert provider.config == config
    assert manager._agent_providers["test_agent"][config.provider_name] is provider
    
    # Should create new instance for different agent
    provider2 = manager.initialize_provider("other_agent", config)
    assert provider is not provider2


def test_initialize_ephemeral_provider(manager):
    """Test initialization of ephemeral provider."""
    config = TestConfig(scope="jit")
    provider1 = manager.initialize_provider("test_agent", config)
    provider2 = manager.initialize_provider("test_agent", config)
    
    # Should create new instance each time
    assert provider1 is not provider2


def test_get_provider(manager):
    """Test provider retrieval."""
    config = TestConfig()
    provider = manager.initialize_provider("test_agent", config)
    
    # Should find provider by name
    assert manager.get_provider("test_agent", config.provider_name) is provider
    
    # Should return None for non-existent provider
    assert manager.get_provider("test_agent", "non_existent") is None


def test_get_provider_by_class(manager):
    """Test provider retrieval by class."""
    config = TestConfig()
    provider = manager.initialize_provider("test_agent", config)
    
    # Should find provider by class
    assert manager.get_provider_by_class("test_agent", TestProvider) is provider
    
    # Should raise error for non-existent provider class
    with pytest.raises(ValueError):
        manager.get_provider_by_class("test_agent", BaseProvider)


def test_disabled_provider(manager):
    """Test handling of disabled provider."""
    config = TestConfig(enabled=False)
    
    with pytest.raises(ProviderInitError):
        manager.initialize_provider("test_agent", config)


def test_provider_init_error(manager):
    """Test handling of provider initialization error."""
    config = TestConfig()
    config.provider_class = "non.existent.Provider"
    
    with pytest.raises(ProviderInitError):
        manager.initialize_provider("test_agent", config)


def test_get_event_providers(manager):
    """Test retrieval of event providers."""
    # Create both regular and event providers
    regular_config = TestConfig(scope="singleton")
    event_config = TestEventConfig(scope="singleton")
    
    manager.initialize_provider("test_agent", regular_config)
    event_provider = manager.initialize_provider("test_agent", event_config)
    
    event_providers = manager.get_event_providers("test_agent")
    assert len(event_providers) == 1
    assert event_providers[0] is event_provider


def test_get_all_providers_as_dict(manager):
    """Test provider dictionary generation."""
    # Create providers with different scopes
    singleton_config = TestConfig(scope="singleton", provider_name="singleton_provider")
    scoped_config = TestConfig(scope="scoped", provider_name="scoped_provider")
    
    manager.initialize_provider("test_agent", singleton_config)
    manager.initialize_provider("test_agent", scoped_config)
    
    providers_dict = manager.get_all_providers_as_dict()
    
    assert "global" in providers_dict
    assert "test_agent" in providers_dict
    assert len(providers_dict["global"]) == 1
    assert len(providers_dict["test_agent"]) == 1
    assert providers_dict["global"][0].provider_name == "singleton_provider"
    assert providers_dict["test_agent"][0].provider_name == "scoped_provider"


def test_trigger_event(manager):
    """Test event triggering across providers."""
    # Create event providers with different priorities
    config1 = TestEventConfig(provider_name="event1")
    config2 = TestEventConfig(provider_name="event2")
    
    provider1 = manager.initialize_provider("test_agent", config1)
    provider2 = manager.initialize_provider("test_agent", config2)
    
    # Mock the providers and context
    mock_context = MagicMock(spec=ProviderContext)
    mock_context.current_agent.name = "test_agent"
    
    # Trigger event
    manager.trigger_event(EventType.START, mock_context)
    
    # Providers should be sorted by priority
    event_providers = manager.get_event_providers("test_agent")
    assert len(event_providers) == 2
    assert event_providers[0].config.provider_name == "event2"  # Higher priority
    assert event_providers[1].config.provider_name == "event1"  # Lower priority
