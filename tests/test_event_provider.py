"""Tests for the event-based provider system."""
import pytest
from typing import Any, Dict, List
from schwarm.events.event_types import EventType
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base import BaseProviderConfig

class TestConfig(BaseProviderConfig):
    """Test configuration."""
    def __init__(self, **data):
        data.update({
            "provider_name": "test_provider",
            "provider_type": "test",
            "provider_class": "tests.test_event_provider.TestEventProvider",
            "scope": "scoped"
        })
        super().__init__(**data)

class TestEventProvider(BaseEventHandleProvider):

    async def initialize(self) -> None:
        """Initialize the provider."""
        pass
    """Test event-based provider."""
    def __init__(self, config: TestConfig):
        super().__init__(config)
        self.event_log: List[str] = []
        
    def set_up(self) -> None:
        """Set up test event handlers."""
        self.external_use = True
        self.internal_use = {
            EventType.START: [self.on_start],
            EventType.TOOL_EXECUTION: [self.on_tool]
        }
        
    def on_start(self, **kwargs: Dict[str, Any]) -> None:
        """Handle start event."""
        self.event_log.append("start")
        
    def on_tool(self, **kwargs: Dict[str, Any]) -> str:
        """Handle tool execution event."""
        self.event_log.append("tool")
        return "tool_result"

    def complete(self, messages: List[str]) -> str:
        """Test completion method."""
        return "test_completion"

@pytest.fixture
def provider():
    """Create a test provider instance."""
    config = TestConfig()
    provider = TestEventProvider(config)
    provider.set_up()
    return provider

def test_provider_initialization(provider):
    """Test provider initialization."""
    assert provider.external_use is True
    assert EventType.START in provider.internal_use
    assert EventType.TOOL_EXECUTION in provider.internal_use
    assert len(provider.internal_use) == 2

def test_event_handling(provider):
    """Test event handling."""
    # Test START event
    provider.handle_event(EventType.START)
    assert provider.event_log == ["start"]
    
    # Test TOOL_EXECUTION event
    result = provider.handle_event(EventType.TOOL_EXECUTION)
    assert result == "tool_result"
    assert provider.event_log == ["start", "tool"]

def test_unknown_event(provider):
    """Test handling of unknown event."""
    result = provider.handle_event(EventType.MESSAGE_COMPLETION)
    assert result is None
    assert provider.event_log == []

def test_external_use(provider):
    """Test external use through complete method."""
    result = provider.complete(["test message"])
    assert result == "test_completion"

def test_provider_config():
    """Test provider configuration."""
    config = TestConfig()
    assert config.provider_name == "test_provider"
    assert config.provider_type == "test"
    assert config.scope == "scoped"
