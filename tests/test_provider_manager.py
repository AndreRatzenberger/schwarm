"""Tests for the provider manager."""
import pytest
from unittest.mock import MagicMock, patch
from schwarm.events.event_types import EventType
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base import BaseProvider
from schwarm.provider.base import BaseProviderConfig
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.provider_manager import ProviderManager, ProviderInitError
from typing import Any


class TestProvider(BaseProvider):
    """Test provider implementation."""
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestProvider2(BaseProvider):
    """Another test provider implementation for testing class lookup."""
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestEventProvider(BaseEventHandleProvider):
    """Test event provider implementation."""
    def __init__(self, config):
        super().__init__(config)
        self.priority = 0 if config.provider_name == "event1" else 1  # event2 has higher priority
    
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass


class TestConfig(BaseProviderConfig):
    """Test provider configuration."""
    provider_class: type[BaseProvider] | str

    def __init__(self, **data):
        data.update({
            "provider_name": data.get("provider_name", "test_provider"),
            "provider_type": "test",
            "provider_class": TestProvider,  # Use class directly instead of string
            "scope": data.get("scope", "scoped")
        })
        super().__init__(**data)

    def get_provider_class(self) -> type[BaseProvider]:
        """Get the provider class."""
        if isinstance(self.provider_class, str):
            # Handle string case for test_provider_init_error
            module_path, class_name = self.provider_class.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        return self.provider_class


class TestEventConfig(BaseProviderConfig):
    """Test event provider configuration."""
    provider_class: type[BaseProvider] | str

    def __init__(self, **data):
        data.update({
            "provider_name": data.get("provider_name", "test_event_provider"),
            "provider_type": "event",
            "provider_class": TestEventProvider,  # Use class directly instead of string
            "scope": data.get("scope", "scoped")
        })
        super().__init__(**data)

    def get_provider_class(self) -> type[BaseProvider]:
        """Get the provider class."""
        if isinstance(self.provider_class, str):
            module_path, class_name = self.provider_class.rsplit(".", 1)
            module = __import__(module_path, fromlist=[class_name])
            return getattr(module, class_name)
        return self.provider_class


@pytest.fixture
def manager():
    """Create a fresh provider manager instance."""
    # Reset the global instance
    ProviderManager._instance = None
    return ProviderManager()


def test_global_pattern():
    """Test provider manager global pattern."""
    manager1 = ProviderManager()
    manager2 = ProviderManager()
    assert manager1 is manager2


@pytest.mark.asyncio
async def test_initialize_global_provider(manager):
    """Test initialization of global provider."""
    config = TestConfig(scope="global")
    provider = manager.initialize_provider("test_agent", config)
    await provider.initialize()  # Properly await initialization
    
    assert provider.config == config
    assert provider in manager._providers["global"]
    
    # Should return same instance for different agent
    provider2 = manager.initialize_provider("other_agent", config)
    assert provider is provider2


@pytest.mark.asyncio
async def test_initialize_scoped_provider(manager):
    """Test initialization of scoped provider."""
    config = TestConfig(scope="scoped")
    provider = manager.initialize_provider("test_agent", config)
    await provider.initialize()  # Properly await initialization
    
    assert provider.config == config
    assert provider in manager._providers["test_agent"]
    
    # Should create new instance for different agent
    provider2 = manager.initialize_provider("other_agent", config)
    await provider2.initialize()  # Properly await initialization
    assert provider is not provider2


@pytest.mark.asyncio
async def test_initialize_ephemeral_provider(manager):
    """Test initialization of ephemeral provider."""
    config = TestConfig(scope="jit")
    provider1 = manager.initialize_provider("test_agent", config)
    await provider1.initialize()  # Properly await initialization
    provider2 = manager.initialize_provider("test_agent", config)
    await provider2.initialize()  # Properly await initialization
    
    # Should create new instance each time
    assert provider1 is not provider2


@pytest.mark.asyncio
async def test_get_provider(manager):
    """Test provider retrieval."""
    config = TestConfig()
    provider = manager.create_provider_and_register("test_agent", config)
    await provider.initialize()  # Properly await initialization
    
    # Should find provider by name
    assert manager.get_provider_by_id("test_agent", provider._provider_id) is provider
    
    # Should return None for non-existent provider
    assert manager.get_provider("test_agent", "non_existent") is None


@pytest.mark.asyncio
async def test_get_provider_by_class(manager):
    """Test provider retrieval by class."""
    config = TestConfig()
    provider = manager.initialize_provider("test_agent", config)
    await provider.initialize()  # Properly await initialization
    
    # Should find provider by class
    assert manager.get_provider_by_class("test_agent", TestProvider) is provider
    
    # Should raise error for non-existent provider class
    with pytest.raises(ValueError):
        manager.get_provider_by_class("test_agent", TestProvider2)


def test_disabled_provider(manager):
    """Test handling of disabled provider."""
    config = TestConfig(enabled=False)
    
    with pytest.raises(ProviderInitError):
        manager.initialize_provider("test_agent", config)


def test_provider_init_error(manager):
    """Test handling of provider initialization error."""
    config = TestConfig()
    config.provider_class = "non.existent.Provider"
    
    with pytest.raises(ProviderInitError) as exc_info:
        manager.initialize_provider("test_agent", config)
    assert "Failed to initialize provider" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_event_providers(manager):
    """Test retrieval of event providers."""
    # Create both regular and event providers
    regular_config = TestConfig(scope="global")
    event_config = TestEventConfig(scope="global")
    
    regular_provider = manager.initialize_provider("test_agent", regular_config)
    await regular_provider.initialize()  # Properly await initialization
    event_provider = manager.initialize_provider("test_agent", event_config)
    await event_provider.initialize()  # Properly await initialization
    
    event_providers = manager.get_event_providers("test_agent")
    assert len(event_providers) == 1
    assert event_providers[0] is event_provider


@pytest.mark.asyncio
async def test_get_all_providers_as_dict(manager):
    """Test provider dictionary generation."""
    # Create providers with different scopes
    global_config = TestConfig(scope="global", provider_name="global_provider")
    scoped_config = TestConfig(scope="scoped", provider_name="scoped_provider")
    
    global_provider = manager.initialize_provider("test_agent", global_config)
    await global_provider.initialize()  # Properly await initialization
    scoped_provider = manager.initialize_provider("test_agent", scoped_config)
    await scoped_provider.initialize()  # Properly await initialization
    
    providers_dict = manager.get_all_providers_as_dict()
    
    assert "global" in providers_dict
    assert "test_agent" in providers_dict
    assert len(providers_dict["global"]) == 1
    assert len(providers_dict["test_agent"]) == 1
    assert providers_dict["global"][0].provider_name == "global_provider"
    assert providers_dict["test_agent"][0].provider_name == "scoped_provider"


@pytest.mark.asyncio
async def test_trigger_event(manager):
    """Test event triggering across providers."""
    # Create event providers with different priorities
    config1 = TestEventConfig(provider_name="event1")
    config2 = TestEventConfig(provider_name="event2")
    
    provider1 = manager.initialize_provider("test_agent", config1)
    await provider1.initialize()  # Properly await initialization
    provider2 = manager.initialize_provider("test_agent", config2)
    await provider2.initialize()  # Properly await initialization
    
    # Mock the providers and context
    mock_context = MagicMock(spec=ProviderContext)
    mock_agent = MagicMock()
    mock_agent.name = "test_agent"
    mock_context.current_agent = mock_agent
    
    # Trigger event
    manager.trigger_event(EventType.START, mock_context)
    
    # Providers should be sorted by priority
    event_providers = manager.get_event_providers("test_agent")
    assert len(event_providers) == 2
    assert event_providers[0].config.provider_name == "event2"  # Higher priority
    assert event_providers[1].config.provider_name == "event1"  # Lower priority
