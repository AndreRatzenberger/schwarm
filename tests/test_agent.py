"""Tests for the Agent class."""
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from schwarm.models.message import Message
from schwarm.models.result import Result
from schwarm.models.agent import Agent
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig

# Import and rebuild Result model
Result.model_rebuild()

class TestConfig(BaseProviderConfig):
    """Test provider configuration."""
    def __init__(self, **data):
        data.update({
            "provider_name": "test_provider",
            "provider_type": "test",
            "provider_class": f"{__name__}.TestProvider",
            "scope": "scoped"
        })
        super().__init__(**data)


class TestProvider(BaseProvider):
    """Test provider implementation."""
    def __init__(self, config: BaseProviderConfig):
        super().__init__(config)
        self.calls: list[str] = []
        
    def initialize(self) -> None:
        """Initialize the provider."""
        self.calls.append("initialize")
        
    def complete(self, messages: list[Message]) -> Message:
        """Complete the given messages."""
        self.calls.append(f"complete: {messages[0].content}")
        return Message(role="assistant", content=f"Response to: {messages[0].content}")


@pytest.fixture
def context() -> Dict[str, Any]:
    """Create a test context."""
    return {"key": "value"}


def test_instructions(context: Dict[str, Any]) -> None:
    """Test dynamic instructions."""
    assert context["key"] == "value"


@pytest.fixture
def query() -> str:
    """Test query fixture."""
    return "test query"


@pytest.fixture
def mock_schwarm():
    """Create a mock Schwarm instance."""
    with patch('schwarm.core.schwarm.Schwarm') as mock:
        yield mock


def test_function(context: Dict[str, Any], query: str) -> None:
    """Test agent function."""
    result = Result(
        value=f"Processed: {query}",
        context_variables=context,
        agent=None
    )
    assert isinstance(result, Result)
    assert result.value == f"Processed: {query}"
    assert result.context_variables == context


@pytest.fixture
def agent():
    """Create a test agent."""
    agent = Agent(
        name="test_agent",
        provider_configurations=[TestConfig()],
        instructions="You are a test agent.",
        functions=[test_function]
    )
    # Initialize providers
    for config in agent.provider_configurations:
        provider = agent._provider_manager.create_provider_and_register(agent.name, config)
        provider.initialize()
    return agent


def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent.name == "test_agent"
    assert len(agent.provider_configurations) == 1
    assert agent.instructions == "You are a test agent."
    assert len(agent.functions) == 1


def test_get_typed_provider(agent):
    """Test getting typed provider."""
    provider = agent.get_typed_provider(TestProvider)
    assert isinstance(provider, TestProvider)
    assert "initialize" in provider.calls


def test_quickstart_with_function(agent, mock_schwarm):
    """Test quickstart using agent function."""
    result = Result(
        value="Test response",
        context_variables={"test": "value"},
        agent=agent
    )
    mock_schwarm.return_value.quickstart.return_value = result
    
    result = agent.quickstart(
        "test query",
        context_variables={"test": "value"}
    )
    
    assert isinstance(result, Result)
    assert result.value == "Test response"
    assert result.context_variables == {"test": "value"}


def test_quickstart_modes(mock_schwarm, agent):
    """Test quickstart in different modes."""
    result = Result(
        value="Test response",
        context_variables={},
        agent=agent
    )
    mock_schwarm.return_value.quickstart.return_value = result
    
    # Test auto mode
    agent.quickstart("test", mode="auto")
    mock_schwarm.return_value.quickstart.assert_called_with(
        agent=agent,
        input_text="test",
        context_variables={},
        mode="auto"
    )
    
    # Test interactive mode
    agent.quickstart("test", mode="interactive")
    mock_schwarm.return_value.quickstart.assert_called_with(
        agent=agent,
        input_text="test",
        context_variables={},
        mode="interactive"
    )


def test_provider_setup(agent):
    """Test provider setup."""
    provider = agent.get_typed_provider(TestProvider)
    assert isinstance(provider, TestProvider)
    assert "initialize" in provider.calls


def test_quickstart_response_conversion():
    """Test conversion of Schwarm Response to Result."""
    agent = Agent(
        name="test_agent",
        provider_configurations=[TestConfig()],
        instructions="You are a test agent."
    )
    
    result = Result(
        value="Test response",
        context_variables={"test": "value"},
        agent=agent
    )
    
    with patch('schwarm.core.schwarm.Schwarm') as mock_schwarm:
        mock_schwarm.return_value.quickstart.return_value = result
        result = agent.quickstart("test")
        
        assert isinstance(result, Result)
        assert result.value == "Test response"
        assert result.context_variables == {"test": "value"}
        assert result.agent == agent


def test_multiple_providers():
    """Test agent with multiple providers."""
    class AnotherConfig(TestConfig):
        def __init__(self):
            super().__init__()
            self.provider_name = "another_provider"
    
    agent = Agent(
        name="multi_agent",
        provider_configurations=[
            TestConfig(),
            AnotherConfig()
        ]
    )
    
    # Initialize providers
    for config in agent.provider_configurations:
        provider = agent._provider_manager.create_provider_and_register(agent.name, config)
        provider.initialize()
    
    providers = agent._provider_manager.get_all_providers_to_scope(agent.name)
    assert len(providers) == 2
    assert "test_provider" in providers
    assert "another_provider" in providers
