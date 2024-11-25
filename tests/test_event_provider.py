"""Tests for the event-based provider system."""
from datetime import datetime
from unittest.mock import MagicMock
import pytest
from schwarm.events.event import Event, EventType
from schwarm.models.provider_context import ProviderContextModel
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig

from schwarm.models.message import Message


class TestConfig(BaseEventHandleProviderConfig):
    """Test configuration."""
    pass


class TestEventProvider(BaseEventHandleProvider):
    """Test event-based provider."""
    
    def initialize(self) -> None:
        """Initialize the provider."""
        pass

    def handle_event(self, event: Event, span=None) -> ProviderContextModel | None:
        """Handle an event."""
        super().handle_event(event, span)  # Log the event
        
        # Return None for most events
        if event.type == EventType.TOOL_EXECUTION:
            return ProviderContextModel(
                current_agent=event.context.current_agent,
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
    context = MagicMock(spec=ProviderContextModel)
    context.current_agent = MagicMock()
    context.current_agent.name = "test_agent"
    context.message_history = []
    context.context_variables = {}
    return context


@pytest.fixture
def mock_span():
    """Create a mock span for telemetry."""
    return MagicMock()


def test_provider_initialization(provider, config):
    """Test provider initialization."""
    assert isinstance(provider.config, BaseEventHandleProviderConfig)
    assert provider.config.scope == "scoped"
    assert provider.event_log == []


def test_event_logging(provider, mock_context, mock_span):
    """Test that events are properly logged."""
    # Create test events
    start_event = Event(
        type=str(EventType.START),
        context=mock_context,
        agent_name="test_agent",
        timestamp=datetime.now().isoformat()
    )
    
    tool_event = Event(
        type=str(EventType.TOOL_EXECUTION),
        context=mock_context,
        agent_name="test_agent",
        timestamp=datetime.now().isoformat()
    )
    
    # Handle events
    provider.handle_event(start_event, mock_span)
    provider.handle_event(tool_event, mock_span)
    
    # Verify events were logged
    assert len(provider.event_log) == 2
    assert provider.event_log[0] == start_event
    assert provider.event_log[1] == tool_event


def test_tool_execution_return_value(provider, mock_context, mock_span):
    """Test that tool execution returns a context."""
    event = Event(
        type=str(EventType.TOOL_EXECUTION),
        context=mock_context,
        agent_name="test_agent",
        timestamp=datetime.now().isoformat()
    )
    
    result = provider.handle_event(event, mock_span)
    
    assert isinstance(result, ProviderContextModel)
    assert result.current_agent == mock_context.current_agent


def test_non_tool_execution_return_value(provider, mock_context, mock_span):
    """Test that non-tool events return None."""
    event = Event(
        type=str(EventType.START),
        context=mock_context,
        agent_name="test_agent",
        timestamp=datetime.now().isoformat()
    )
    
    result = provider.handle_event(event, mock_span)
    
    assert result is None
    assert len(provider.event_log) == 1


def test_provider_config():
    """Test provider configuration."""
    config = TestConfig(scope="scoped")
    assert config.scope == "scoped"
    assert isinstance(config, BaseEventHandleProviderConfig)


def test_handle_event_without_span(provider, mock_context):
    """Test that handle_event works when span is not provided."""
    event = Event(
        type=str(EventType.START),
        context=mock_context,
        agent_name="test_agent",
        timestamp=datetime.now().isoformat()
    )
    
    # Should not raise error when span is None
    result = provider.handle_event(event)
    assert result is None
    assert len(provider.event_log) == 1
