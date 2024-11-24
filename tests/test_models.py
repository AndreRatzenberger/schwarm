"""Tests for model classes."""
from pydantic import ValidationError, HttpUrl
import pytest
from typing import List
from schwarm.models.message import Message, MessageInfo
from schwarm.models.agent import Agent
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base.base_provider import BaseProviderConfig


class TestProviderConfig(BaseProviderConfig):
    """Test provider configuration."""
    api_key: str
    api_base: HttpUrl  # Use HttpUrl for validation

    def __init__(self, **data):
        """Initialize with defaults."""
        data.update({
            "provider_name": "test_provider",
            "provider_type": "test",
            "provider_class": "tests.test_models.TestProviderConfig"
        })
        super().__init__(**data)


@pytest.fixture
def test_agent():
    """Create a test agent."""
    return Agent(
        name="test_agent",
        model="gpt-4",
        description="Test agent",
        instructions="Test instructions",
        configs=[
            TestProviderConfig(
                api_key="test-key",
                api_base="https://api.test.com"
            )
        ]
    )


@pytest.fixture
def test_message():
    """Create a test message."""
    return Message(
        role="user",
        content="test message"
    )


@pytest.fixture
def mock_context(test_agent, test_message):
    """Create a mock provider context to avoid circular dependency."""
    from unittest.mock import MagicMock
    mock_context = MagicMock(spec=ProviderContext)
    mock_context.current_agent = test_agent
    mock_context.current_message = test_message
    mock_context.message_history = [test_message]
    mock_context.available_agents = []
    mock_context.available_tools = []
    mock_context.available_providers = {}
    mock_context.context_variables = {}
    mock_context.current_instruction = None
    return mock_context


@pytest.mark.asyncio
async def test_provider_config_validation():
    """Test provider config validation."""
    # Test invalid URL
    with pytest.raises(ValidationError):
        TestProviderConfig(
            api_key="api-key",
            api_base="nouri"  # Invalid URL
        )

    # Test valid config
    config = TestProviderConfig(
        api_key="api-key",
        api_base="https://pytest.com"
    )
    assert str(config.api_base).rstrip('/') == "https://pytest.com"
    assert isinstance(config, TestProviderConfig)
    assert config.api_key == "api-key"


@pytest.mark.asyncio
async def test_agent_model():
    """Test agent model validation and functionality."""
    # Test minimal agent creation
    agent = Agent(
        name="test",
        description="test agent"
    )
    assert agent.name == "test"
    assert agent.model == "gpt-4"  # default value
    
    # Test with provider configs
    test_config = TestProviderConfig(
        api_key="test-key",
        api_base="https://api.test.com"
    )
    agent = Agent(
        name="test",
        description="test agent",
        configs=[test_config]
    )
    assert len(agent.configs) == 1
    assert isinstance(agent.configs[0], TestProviderConfig)
    assert agent.configs[0].api_key == "test-key"


@pytest.mark.asyncio
async def test_provider_context(mock_context):
    """Test provider context model."""
    # Test basic attributes
    assert mock_context.current_agent.name == "test_agent"
    assert mock_context.current_message.content == "test message"
    assert len(mock_context.message_history) == 1
    
    # Test default values
    assert mock_context.available_agents == []
    assert mock_context.available_tools == []
    assert mock_context.available_providers == {}
    assert mock_context.context_variables == {}
    assert mock_context.current_instruction is None


@pytest.mark.asyncio
async def test_message_model():
    """Test message model validation."""
    # Test basic message with defaults
    message = Message(role="user", content="test")
    assert message.role == "user"
    assert message.content == "test"
    assert isinstance(message.tool_calls, list)
    assert message.tool_calls == []
    assert message.info is None
    
    # Test with tool calls
    tool_message = Message(
        role="assistant",
        content="Using tool",
        tool_calls=[{"type": "function", "function": {"name": "test_tool", "arguments": "{}"}}]
    )
    assert isinstance(tool_message.tool_calls, list)
    assert len(tool_message.tool_calls) == 1
    assert tool_message.tool_calls[0]["function"]["name"] == "test_tool"

    # Test with message info
    info_message = Message(
        role="assistant",
        content="test",
        info=MessageInfo(token_counter=10, completion_cost=0.001)
    )
    assert info_message.info is not None
    assert info_message.info.token_counter == 10
    assert info_message.info.completion_cost == 0.001


@pytest.mark.asyncio
async def test_model_relationships(mock_context, test_agent):
    """Test relationships between models."""
    # Test agent -> provider config relationship
    assert len(test_agent.provider_configurations) == 1
    config = test_agent.provider_configurations[0]
    assert isinstance(config, TestProviderConfig)
    assert str(config.api_base).rstrip('/') == "https://api.test.com"
    assert config.api_key == "test-key"
    
    # Test context -> agent relationship
    assert mock_context.current_agent == test_agent
    assert isinstance(mock_context.current_agent.provider_configurations[0], TestProviderConfig)
    provider_config = mock_context.current_agent.provider_configurations[0]
    assert isinstance(provider_config, TestProviderConfig)
    assert provider_config.api_key == "test-key"
