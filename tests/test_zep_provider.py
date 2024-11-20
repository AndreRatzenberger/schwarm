"""Tests for the Zep memory provider."""
import pytest
from unittest.mock import patch, MagicMock
from zep_python.types import Message as ZepMessage, SessionSearchResult
from schwarm.events.event_types import EventType
from schwarm.provider.zep_provider import ZepProvider
from schwarm.provider.zep_config import ZepConfig

def create_config(
    api_key: str = "test_key",
    api_url: str = "http://test.com",
    min_fact_rating: float = 0.7
) -> ZepConfig:
    """Create a test configuration."""
    return ZepConfig(
        zep_api_key=api_key,
        zep_api_url=api_url,
        min_fact_rating=min_fact_rating
    )

@pytest.fixture
def mock_zep():
    """Create a mock Zep client."""
    mock = MagicMock()
    mock.user.get.return_value = None
    mock.memory.add_session.return_value = None
    return mock

@pytest.fixture
def provider(mock_zep):
    """Create a test provider instance."""
    with patch('schwarm.provider.zep_provider.Zep', return_value=mock_zep):
        provider = ZepProvider(create_config())
        provider.set_up()
        return provider

def test_provider_initialization(provider):
    """Test provider initialization."""
    assert provider.external_use is True
    assert EventType.START in provider.internal_use
    assert EventType.INSTRUCT in provider.internal_use
    assert EventType.MESSAGE_COMPLETION in provider.internal_use

def test_provider_start_event(provider, mock_zep):
    """Test START event handling."""
    provider.handle_event(EventType.START)
    
    assert provider.zep_service is not None
    assert provider.user_id is not None
    assert provider.session_id is not None
    mock_zep.user.add.assert_called_once()
    mock_zep.memory.add_session.assert_called_once()

def test_enhance_instructions(provider, mock_zep):
    """Test instruction enhancement."""
    mock_memory = MagicMock()
    mock_memory.relevant_facts = "Test fact 1\nTest fact 2"
    mock_zep.memory.get.return_value = mock_memory
    
    provider.handle_event(EventType.START)  # Initialize first
    result = provider.handle_event(EventType.INSTRUCT)
    
    assert result is not None
    assert "Test fact 1" in result
    assert "Test fact 2" in result

def test_save_completion(provider, mock_zep):
    """Test completion saving."""
    provider.handle_event(EventType.START)  # Initialize first
    
    test_message = MagicMock()
    test_message.content = "Test completion"
    
    provider.handle_event(
        EventType.MESSAGE_COMPLETION,
        messages=[test_message]
    )
    
    mock_zep.memory.add.assert_called_once()

def test_split_text():
    """Test text splitting functionality."""
    provider = ZepProvider(create_config())
    
    # Test empty text
    assert provider.split_text(None) == []
    
    # Test short text
    short_text = "Short message"
    result = provider.split_text(short_text)
    assert len(result) == 1
    assert isinstance(result[0], ZepMessage)
    assert result[0].content == short_text
    
    # Test long text
    long_text = "x" * 2000
    result = provider.split_text(long_text, max_length=1000)
    assert len(result) == 2
    assert all(isinstance(msg, ZepMessage) for msg in result)
    # Verify content exists and length
    for msg in result:
        assert msg.content is not None
        assert len(msg.content) <= 1000

def test_search_memory(provider, mock_zep):
    """Test memory search functionality."""
    mock_result = MagicMock(spec=SessionSearchResult)
    mock_result.message.content = "Test memory"
    mock_zep.memory.search_sessions.return_value.results = [mock_result]
    
    provider.handle_event(EventType.START)  # Initialize first
    results = provider.search_memory("test query")
    
    assert len(results) == 1
    mock_zep.memory.search_sessions.assert_called_once_with(
        text="test query",
        user_id=provider.user_id,
        search_scope="facts",
        min_fact_rating=provider.config.min_fact_rating
    )

def test_complete_not_implemented(provider):
    """Test complete method raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        provider.complete(["test message"])

def test_error_handling(provider, mock_zep):
    """Test error handling in provider methods."""
    # Test search_memory error handling
    mock_zep.memory.search_sessions.side_effect = Exception("Search failed")
    provider.handle_event(EventType.START)  # Initialize first
    results = provider.search_memory("test")
    assert results == []
    
    # Test save_completion error handling
    mock_zep.memory.add.side_effect = Exception("Save failed")
    provider.handle_event(
        EventType.MESSAGE_COMPLETION,
        messages=[MagicMock(content="test")]
    )
    # Should not raise exception, just log error
