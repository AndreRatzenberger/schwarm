"""Tests for the debug provider."""
import os
from unittest.mock import MagicMock, patch
import pytest
from pydantic import BaseModel
from schwarm.events.event import Event
from schwarm.models.message import Message, MessageInfo
from schwarm.models.provider_context import ProviderContextModel
from schwarm.models.types import Agent, Result

from schwarm.provider.information_provider import InformationProvider, InformationConfig
from schwarm.provider.budget_provider import BudgetConfig, BudgetProvider
from schwarm.provider.provider_manager import ProviderManager


# Initialize Agent for Result model
Agent.model_rebuild()
Result.model_rebuild()


class TestDebugProvider(InformationProvider):
    """Test implementation of DebugProvider."""
    def initialize(self) -> None:
        """Initialize the provider."""
        pass
    def handle_event(self, event):
        self.handle_start(event.context)


@pytest.fixture
def config():
    """Create a test debug provider config."""
    return InformationConfig(
        show_instructions=True,
        show_function_calls=True,
        show_budget=True,
        save_logs=True,
        max_length=100
    )


@pytest.fixture
def mock_context():
    """Create a mock provider context."""
    context = MagicMock(spec=ProviderContextModel)
    context.current_agent = MagicMock(spec=Agent)
    context.current_agent.name = "test_agent"
    context.current_agent.instructions = "Test instructions"
    context.message_history = []
    context.context_variables = {"test": "value"}
    return context


@pytest.fixture
def provider(config, mock_context, **data):
    """Create a test debug provider instance."""
    provider = TestDebugProvider(config=config, **data)
    provider.context = mock_context
    return provider


def test_provider_initialization(provider, config):
    """Test basic provider initialization."""
    assert provider.config == config
    assert provider.config.show_instructions is True
    assert provider.config.show_function_calls is True
    assert provider.config.show_budget is True


@patch('schwarm.provider.debug_provider.console')
def test_handle_instructions(mock_console, provider, mock_context):
    """Test instruction handling and display."""
    mock_context.current_agent.instructions = "Test instructions"
    provider.handle_start(mock_context)
    mock_console.print.assert_called()


@patch('schwarm.provider.debug_provider.console')
@patch('schwarm.provider.debug_provider.ProviderManager')
def test_handle_message_completion_with_budget(mock_manager, mock_console, provider, mock_context):
    """Test message completion handling with budget display."""
    # Create a real BudgetProviderConfig instance
    budget_config = BudgetConfig(
        max_spent=10.0,
        max_tokens=1000,
        current_spent=5.0,
        current_tokens=500
    )
    
    # Create and configure mock budget provider
    mock_budget = MagicMock(spec=BudgetProvider)
    mock_budget.config = budget_config
    
    mock_manager_instance = MagicMock()
    mock_manager_instance.get_provider.return_value = mock_budget
    mock_manager.return_value = mock_manager_instance
    
    provider.handle_message_completion()
    mock_console.print.assert_called()


@patch('schwarm.provider.debug_provider.console')
def test_handle_tool_execution(mock_console, provider, mock_context):
    """Test tool execution handling and function display."""
    # Create a mock tool call that matches the expected structure
    tool_call = MagicMock()
    tool_call.function = MagicMock()
    tool_call.function.name = "test_function"
    tool_call.function.arguments = {"param": "value"}
    
    message = Message(
        role="assistant",
        content="Test message",
        tool_calls=[tool_call]
    )
    mock_context.message_history.append(message)
    
    provider.handle_tool_execution()
    mock_console.print.assert_called()


@patch('schwarm.provider.debug_provider.console')
def test_handle_post_tool_execution(mock_console, provider, mock_context):
    """Test post tool execution handling and result display."""
    # Create a mock agent that matches the Agent type
    test_agent = MagicMock(spec=Agent)
    test_agent.name = "test_agent"
    
    result = Result(
        value="test result",
        context_variables={"test": "value"},
        agent=test_agent
    )
    message = Message(
        role="tool",
        content="Test result",
        additional_info={"result": result}
    )
    mock_context.message_history.extend([
        Message(role="assistant", content="Test call"),
        message
    ])
    
    provider.handle_post_tool_execution()
    mock_console.print.assert_called()


@patch('schwarm.provider.debug_provider.os.makedirs')
@patch('schwarm.provider.debug_provider.Path')
def test_log_file_management(mock_path, mock_makedirs, provider):
    """Test log file creation and management."""
    mock_path_instance = MagicMock()
    mock_path_instance.exists.return_value = True
    mock_path_instance.glob.return_value = [MagicMock()]
    mock_path.return_value = mock_path_instance
    
    # Set save_logs to True to ensure makedirs is called
    provider.config.save_logs = True
    
    # Mock APP_SETTINGS.DATA_FOLDER to ensure consistent path
    with patch('schwarm.provider.debug_provider.APP_SETTINGS') as mock_settings:
        mock_settings.DATA_FOLDER = "/test/path"
        provider._ensure_log_directory()
        provider._delete_logs()
    
        # Verify makedirs was called with the correct path
        expected_path = os.path.normpath("/test/path/logs")
        mock_makedirs.assert_called_with(expected_path, exist_ok=True)


@patch('schwarm.provider.debug_provider.console')
def test_disabled_features(mock_console, provider):
    """Test provider with disabled features."""
    provider.config.show_instructions = False
    provider.config.show_function_calls = False
    provider.config.show_budget = False
    
    # Set instructions directly on the mock agent
    provider.context.current_agent.instructions = "Test instructions"
    
    provider.handle_tool_execution()
    provider.handle_message_completion()
    
    # Console should not be used when features are disabled
    mock_console.print.assert_not_called()


@patch('schwarm.provider.debug_provider.open')
def test_log_writing(mock_open, provider):
    """Test log writing functionality."""
    provider._write_to_log("test.log", "Test content")
    mock_open.assert_called()


def test_handle_missing_context(provider):
    """Test handling when context is missing."""
    provider.context = None
    
    # Should not raise errors when context is missing
    provider.handle_message_completion()
    provider.handle_tool_execution()
    provider.handle_post_tool_execution()


def test_handle_empty_message_history(provider, mock_context):
    """Test handling empty message history."""
    mock_context.message_history = []
    
    # Should not raise errors with empty message history
    provider.handle_tool_execution()
    provider.handle_post_tool_execution()


@patch('schwarm.provider.debug_provider.console')
def test_truncated_display(mock_console, provider):
    """Test text truncation in display."""
    provider.config.max_length = 10
    long_text = "x" * 20
    
    provider.context.current_agent.instructions = long_text
    
    provider.handle_start(provider.context)
    mock_console.print.assert_called()
