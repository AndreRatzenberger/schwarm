"""Tests for the Agent class."""
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from schwarm.models.message import Message
from schwarm.models.result import Result
from schwarm.models.agent import Agent
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.debug_provider import DebugConfig, DebugProvider
from schwarm.provider.provider_context import ProviderContext
from schwarm.provider.provider_manager import ProviderManager

# Import and rebuild Result model
Result.model_rebuild()

class TestConfig(BaseProviderConfig):
    """Test provider configuration."""


class TestProvider(BaseEventHandleProvider):
    """Test provider implementation."""
    def __init__(self, config: BaseProviderConfig, **data):
        super().__init__(config,**data)
        self.calls: list[str] = []
        self.context = ProviderContext()
        
    def initialize(self) -> None:
        """Initialize the provider."""
        self.calls.append("initialize")
        
    def complete(self, messages: list[Message]) -> Message:
        """Complete the given messages."""
        self.calls.append(f"complete: {messages[0].content}")
        return Message(role="assistant", content=f"Response to: {messages[0].content}")

    def handle_event(self, event):
        return ProviderContext()



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
    pm = ProviderManager()
    pm._config_to_provider_map[TestConfig] = TestProvider
    agent = Agent(
        name="test_agent",
        provider_configurations=[TestConfig()],
        instructions="You are a test agent.",
        functions=[test_function]
    )
    # Initialize providers
    for config in agent.provider_configurations:
        provider = agent._provider_manager.create_provider(agent.name, config)

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
    assert isinstance(provider[0], TestProvider)



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
    provider = ProviderManager().get_providers_by_class(TestProvider) 
    assert isinstance(provider[0], TestProvider)



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

def test_constructor():
    zap = DebugProvider(DebugConfig())

def test_multiple_providers():
    """Test agent with multiple providers."""
    class AnotherConfig(TestConfig):
        """Another provider configuration."""
    ProviderManager()._config_to_provider_map[TestConfig] = TestProvider
    ProviderManager()._config_to_provider_map[AnotherConfig] = TestProvider
    
    
    agent = Agent(
        name="multi_agent",
        provider_configurations=[
            TestConfig(),
            AnotherConfig()
        ]
    )
    
    # Initialize providers
    for config in agent.provider_configurations:
        provider = ProviderManager().create_provider(agent.name, config)
 
    
    providers = ProviderManager().get_all_providers_to_scope(agent.name)
    assert len(providers) == 2
    assert type(providers[0]) is TestProvider
    assert type(providers[1]) is TestProvider
