"""Tests for ZepProvider."""

import uuid
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest
from zep_python.types import (
    Fact,
    Memory,
    Message as ZepMessage,
    SessionSearchResult,
    Summary,
    User,
)

from schwarm.models.agent import Agent
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContext
from schwarm.models.result import Result
from schwarm.models.types import AgentFunction
from schwarm.provider.zep_provider import ZepConfig, ZepProvider

# Rebuild models to handle circular imports
Result.model_rebuild()
ProviderContext.model_rebuild()


@dataclass
class MockSearchResponse:
    """Mock search response for testing."""
    results: list[SessionSearchResult]


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    return Agent(
        name="test_agent",
        model="gpt-4",
        description="Test agent for testing",
        instructions="You are a test agent",
    )


@pytest.fixture
def zep_config():
    """Create a test config."""
    return ZepConfig(
        zep_api_key="test_key",
        zep_api_url="http://test.url",
        min_fact_rating=0.7,
        on_completion_save_completion_to_memory=True,
    )


@pytest.fixture
def mock_zep():
    """Create a mock Zep client."""
    mock = MagicMock()
    mock.user = MagicMock()
    mock.memory = MagicMock()
    return mock


@pytest.fixture
def provider(zep_config, mock_zep):
    """Create a provider with mocked Zep client."""
    with patch("schwarm.provider.zep_provider.Zep", return_value=mock_zep):
        provider = ZepProvider(zep_config)
        return provider


# def test_initialize(provider, mock_zep, mock_agent):
#     """Test initialization of provider."""
#     # Test with default user_id
#     context = ProviderContext(
#         current_message=Message(role="user", content="test"),
#         current_agent=mock_agent,
#         context_variables={},
#     )
#     provider.initialize(context)
#     assert provider.user_id == "default_user"
#     assert provider.session_id is not None
#     mock_zep.user.get.assert_called_once()
#     mock_zep.memory.add_session.assert_called_once()

#     # Test with randomized user_id
#     provider.user_id = None  # Reset
#     context = ProviderContext(
#         current_message=Message(role="user", content="test"),
#         current_agent=mock_agent,
#         context_variables={"randomize_user_id": True},
#     )
#     provider.initialize(context)
#     assert isinstance(provider.user_id, str)
#     assert provider.user_id.startswith("user_")
#     assert uuid.UUID(provider.user_id.replace("user_", ""))  # Verify UUID format


def test_setup_user_creates_new_user(provider, mock_zep):
    """Test user setup when user doesn't exist."""
    mock_zep.user.get.return_value = None
    provider.user_id = "test_user"
    provider.zep_service = mock_zep
    
    provider._setup_user()
    
    mock_zep.user.add.assert_called_once_with(user_id="test_user")


def test_split_text(provider):
    """Test text splitting functionality."""
    text = "a" * 2000
    max_length = 1000
    
    messages = provider.split_text(text, max_length)
    
    assert len(messages) == 2
    assert all(len(msg.content) <= max_length for msg in messages)
    assert "".join(msg.content for msg in messages) == text


def test_add_to_memory(provider, mock_zep):
    """Test adding text to memory."""
    provider.zep_service = mock_zep
    provider.session_id = "test_session"
    test_text = "Test memory text"
    
    provider.add_to_memory(test_text)
    
    mock_zep.memory.add.assert_called_once()
    args = mock_zep.memory.add.call_args[1]
    assert args["session_id"] == "test_session"
    assert isinstance(args["messages"], list)
    assert all(isinstance(msg, ZepMessage) for msg in args["messages"])


def test_search_memory(provider, mock_zep):
    """Test memory search functionality."""
    provider.zep_service = mock_zep
    provider.user_id = "test_user"
    
    # Mock search response
    search_result = SessionSearchResult(
        session_id="test_session",
        summary=Summary(content="test summary"),
        score=0.8,
    )
    mock_zep.memory.search_sessions.return_value = MockSearchResponse(results=[search_result])
    
    results = provider.search_memory("test query")
    
    assert len(results) == 1
    mock_zep.memory.search_sessions.assert_called_once_with(
        text="test query",
        user_id="test_user",
        search_scope="facts",
        min_fact_rating=0.7
    )


def test_enhance_instructions(provider, mock_zep):
    """Test instruction enhancement with memory context."""
    provider.zep_service = mock_zep
    provider.session_id = "test_session"
    
    # Mock memory response with proper Fact list
    mock_zep.memory.get.return_value = Memory(
        relevant_facts=[Fact(fact="Test relevant fact", rating=0.8)]
    )
    
    result = provider.enhance_instructions()
    
    assert "Test relevant fact" in result
    mock_zep.memory.get.assert_called_once_with(
        "test_session",
        min_rating=0.7
    )


def test_save_completion(provider, mock_zep, mock_agent):
    """Test saving completion to memory."""
    provider.zep_service = mock_zep
    provider.session_id = "test_session"
    
    # Create test message and context
    message = Message(role="assistant", content="Test completion")
    context = ProviderContext(
        current_message=message,
        current_agent=mock_agent,
        context_variables={},
    )
    
    provider.save_completion(context)
    
    mock_zep.memory.add.assert_called_once()
    args = mock_zep.memory.add.call_args[1]
    assert args["session_id"] == "test_session"
    assert isinstance(args["messages"], list)
    assert args["messages"][0].content == "Test completion"


def test_complete_raises_not_implemented(provider):
    """Test that complete method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        provider.complete(["test message"])
