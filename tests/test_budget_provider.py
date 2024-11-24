"""Tests for the budget provider."""
import os
import pytest
from unittest.mock import MagicMock, patch
from schwarm.events.event import Event, EventType
from schwarm.models.message import Message, MessageInfo

from schwarm.models.provider_context import ProviderContextModel
from schwarm.models.types import Agent
from schwarm.provider.budget_provider import BudgetConfig, BudgetProvider


class TestBudgetProvider(BudgetProvider):
    """Test implementation of BudgetProvider."""
    def initialize(self) -> None:
        """Initialize the provider."""
        pass
    
    def handle_event(self, event, span=None):
        return None


@pytest.fixture
def mock_context():
    """Create a mock provider context."""
    context = MagicMock(spec=ProviderContextModel)
    context.current_agent = MagicMock(spec=Agent)
    context.current_agent.name = "test_agent"
    context.message_history = []
    return context


@pytest.fixture
def config():
    """Create a test budget provider config."""
    return BudgetConfig(
        max_spent=10.0,
        max_tokens=1000,
        save_budget=True,
        effect_on_exceed="warning"
    )


@pytest.fixture
def provider(config, mock_context):
    """Create a test budget provider instance."""
    provider = TestBudgetProvider(config=config)
    provider.context = mock_context
    return provider


def test_provider_initialization(provider, config):
    """Test basic provider initialization."""
    assert provider.config == config
    assert provider.current_spent == 0.0
    assert provider.current_tokens == 0


def test_handle_message_completion(provider, mock_context):
    """Test budget tracking through message completion."""
    # Create a test message with cost info
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=1.5,
            token_counter=100
        )
    )
    mock_context.message_history.append(message)

    # Handle the message completion
    provider.handle_post_message_completion(mock_context)

    # Verify budget tracking updated
    assert provider.current_spent == 1.5
    assert provider.current_tokens == 100


@patch('schwarm.provider.budget_provider.os.makedirs')
def test_handle_start(mock_makedirs, provider):
    """Test start handler creates log directory."""
    provider.handle_start()
    mock_makedirs.assert_called_once()


def test_budget_warning(provider, mock_context):
    """Test warning when budget exceeded."""
    # Set up a message that will exceed budget
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=15.0,  # Exceeds max_spent of 10.0
            token_counter=100
        )
    )
    mock_context.message_history.append(message)

    # Should log warning but not raise error
    provider.handle_post_message_completion(mock_context)
    assert provider.current_spent == 15.0


def test_budget_error(provider, mock_context):
    """Test error when budget exceeded with error effect."""
    provider.config.effect_on_exceed = "error"
    
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=15.0,  # Exceeds max_spent of 10.0
            token_counter=100
        )
    )
    mock_context.message_history.append(message)

    # Should raise ValueError
    with pytest.raises(ValueError, match="Budget exceeded"):
        provider.handle_post_message_completion(mock_context)


@patch('schwarm.provider.budget_provider.csv.writer')
def test_save_to_csv(mock_csv_writer, provider, mock_context):
    """Test budget saving to CSV."""
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=1.5,
            token_counter=100
        )
    )
    mock_context.message_history.append(message)

    # Handle message completion which should trigger CSV save
    with patch('schwarm.provider.budget_provider.open') as mock_open:
        provider.handle_post_message_completion(mock_context)
        mock_open.assert_called_once()
        mock_csv_writer.assert_called()


def test_handle_handoff(provider, mock_context):
    """Test budget state transfer during handoff."""
    # Set up some initial budget state
    provider.current_spent = 5.0
    provider.current_tokens = 500

    # Create next agent with budget provider
    next_agent = MagicMock(spec=Agent)
    next_agent.name = "next_agent"
    next_budget_config = BudgetConfig()
    next_agent.provider_configurations = [next_budget_config]

    # Create handoff event with proper ProviderContext
    handoff_context = ProviderContextModel(
        current_agent=next_agent,
        message_history=[],
        context_variables={}
    )
    event = Event(
        type=str(EventType.HANDOFF),
        context=handoff_context,
        agent_name="test_agent",
        timestamp="2021-01-01T00:00:00Z"
    )

    # Handle handoff
    result = provider.handle_handoff(event)

    # Verify budget state transferred
    assert result == next_agent
    assert next_budget_config.current_spent == 5.0
    assert next_budget_config.current_tokens == 500


def test_handle_empty_message_history(provider, mock_context):
    """Test handling empty message history."""
    mock_context.message_history = []
    # Should not raise error
    provider.handle_post_message_completion(mock_context)
    assert provider.current_spent == 0.0
    assert provider.current_tokens == 0


def test_handle_invalid_message(provider, mock_context):
    """Test handling message without cost info."""
    message = Message(role="assistant", content="Test message")  # No info
    mock_context.message_history.append(message)
    
    # Should not raise error or update budget
    provider.handle_post_message_completion(mock_context)
    assert provider.current_spent == 0.0
    assert provider.current_tokens == 0


def test_token_limit_exceeded(provider, mock_context):
    """Test handling token limit exceeded."""
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=1.0,
            token_counter=1500  # Exceeds max_tokens of 1000
        )
    )
    mock_context.message_history.append(message)

    # Should log warning
    provider.handle_post_message_completion(mock_context)
    assert provider.current_tokens == 1500


def test_disabled_budget_saving(provider, mock_context):
    """Test when budget saving is disabled."""
    provider.config.save_budget = False
    
    message = Message(
        role="assistant",
        content="Test message",
        info=MessageInfo(
            completion_cost=1.0,
            token_counter=100
        )
    )
    mock_context.message_history.append(message)

    # Should not attempt to save to CSV
    with patch('schwarm.provider.budget_provider.open') as mock_open:
        provider.handle_post_message_completion(mock_context)
        mock_open.assert_not_called()
