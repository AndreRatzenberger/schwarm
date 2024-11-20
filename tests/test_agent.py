"""Tests for the Agent class."""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List
from schwarm.models.types import Agent, Result
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig, ProviderScope
from schwarm.models.message import Message

class TestConfig(BaseProviderConfig):
    """Test provider configuration."""
    def __init__(self, **data):
        data.update({
            "provider_name": "test_provider",
            "provider_type": "test",
            "provider_class": "tests.test_agent.TestProvider",
            "scope": ProviderScope.AGENT
        })
        super().__init__(**data)

class TestProvider(BaseProvider):
    """Test provider implementation."""
    def __init__(self, config: BaseProviderConfig):
        super().__init__(config)
        self.calls: List[str] = []
        
    def set_up(self) -> None:
        self.calls.append("set_up")
        
    def complete(self, messages: List[str]) -> str:
        self.calls.append(f"complete: {messages[0]}")
        return f"Response to: {messages[0]}"

def test_instructions(context: Dict) -> str:
    """Test dynamic instructions."""
    return "Test instructions"

def test_function(context: Dict, query: str) -> Result:
    """Test agent function."""
    return Result(
        value=f"Processed: {query}",
        context_variables=context
    )

@pytest.fixture
def agent():
    """Create a test agent."""
    return Agent(
        name="test_agent",
        provider_configurations=[TestConfig()],
        instructions=test_instructions,
        functions=[test_function]
    )

def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent.name == "test_agent"
    assert len(agent.provider_configurations) == 1
    assert agent.instructions is test_instructions
    assert len(agent.functions) == 1
    assert agent._providers == {}

def test_get_typed_provider(agent):
    """Test getting typed provider."""
    # Set up providers first
    agent._setup_providers()
    
    # Get provider by type
    provider = agent.get_typed_provider(TestProvider)
    assert isinstance(provider, TestProvider)
    assert "set_up" in provider.calls
    
    # Test getting non-existent provider type
    with pytest.raises(ValueError):
        agent.get_typed_provider(MagicMock)

def test_quickstart_with_function(agent):
    """Test quickstart using agent function."""
    result = agent.quickstart(
        "test query",
        context_variables={"test": "value"}
    )
    
    assert isinstance(result, Result)
    assert result.value == "Processed: test query"
    assert result.context_variables == {"test": "value"}

@patch('schwarm.core.schwarm.Schwarm')
def test_quickstart_modes(mock_schwarm, agent):
    """Test quickstart in different modes."""
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
    agent._setup_providers()
    
    assert len(agent._providers) == 1
    provider = agent._providers["test_provider"]
    assert isinstance(provider, TestProvider)
    assert "set_up" in provider.calls

def test_quickstart_response_conversion():
    """Test conversion of Schwarm Response to Result."""
    agent = Agent(
        name="test_agent",
        provider_configurations=[TestConfig()]
    )
    
    mock_response = MagicMock()
    mock_response.messages = [Message(role="assistant", content="Test response")]
    mock_response.context_variables = {"test": "value"}
    mock_response.agent = agent
    
    with patch('schwarm.core.schwarm.Schwarm') as mock_schwarm:
        mock_schwarm.return_value.quickstart.return_value = mock_response
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
    
    agent._setup_providers()
    assert len(agent._providers) == 2
    assert "test_provider" in agent._providers
    assert "another_provider" in agent._providers
