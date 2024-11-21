"""Tests for the event-based provider system."""
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from schwarm.events.event_data import Event, EventType
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.provider_context import ProviderContext
from schwarm.models.message import Message


class TestConfig(BaseEventHandleProviderConfig):
    """Test configuration."""
    pass


class TestEventProvider(BaseEventHandleProvider):
    """Test event-based provider."""
    
    def initialize(self) -> None:
        """Initialize the provider."""
        pass

    def handle_event(self, event: Event) -> ProviderContext | None:
        """Handle an event."""
        super().handle_event(event)  # Log the event
        
        # Return None for most events
        if event.type == EventType.TOOL_EXECUTION:
            return ProviderContext(
                current_agent=event.payload.current_agent,
                message_history=[],
                context_variables={}
            )
        return None


@pytest.fixture
def config():
    """Create a test configuration."""
    return TestConfig(scope="scoped")


@pytest.fixture
def provider(config):
    """Create a test provider instance."""
    return TestEventProvider(config=config)


@pytest.fixture
def mock_context():
    """Create a mock provider context."""
    context = MagicMock(spec=ProviderContext)
    context.current_agent = MagicMock()
    context.current_agent.name = "test_agent"
    context.message_history = []
    context.context_variables = {}
    return context


def test_provider_initialization(provider, config):
    """Test provider initialization."""
    assert isinstance(provider.config, BaseEventHandleProviderConfig)
    assert provider.config.scope == "scoped"
    assert provider.event_log == []


def test_event_logging(provider, mock_context):
    """Test that events are properly logged."""
    # Create test events
    start_event = Event(
        type=EventType.START,
        payload=mock_context,
        agent_id="test_agent",
        datetime=datetime.now().isoformat()
    )
    
    tool_event = Event(
        type=EventType.TOOL_EXECUTION,
        payload=mock_context,
        agent_id="test_agent",
        datetime=datetime.now().isoformat()
    )
    
    # Handle events
    provider.handle_event(start_event)
    provider.handle_event(tool_event)
    
    # Verify events were logged
    assert len(provider.event_log) == 2
    assert provider.event_log[0] == start_event
    assert provider.event_log[1] == tool_event


def test_tool_execution_return_value(provider, mock_context):
    """Test that tool execution returns a context."""
    event = Event(
        type=EventType.TOOL_EXECUTION,
        payload=mock_context,
        agent_id="test_agent",
        datetime=datetime.now().isoformat()
    )
    
    result = provider.handle_event(event)
    
    assert isinstance(result, ProviderContext)
    assert result.current_agent == mock_context.current_agent


def test_non_tool_execution_return_value(provider, mock_context):
    """Test that non-tool events return None."""
    event = Event(
        type=EventType.START,
        payload=mock_context,
        agent_id="test_agent",
        datetime=datetime.now().isoformat()
    )
    
    result = provider.handle_event(event)
    
    assert result is None
    assert len(provider.event_log) == 1


def test_provider_config():
    """Test provider configuration."""
    config = TestConfig(scope="scoped")
    assert config.scope == "scoped"
    assert isinstance(config, BaseEventHandleProviderConfig)
