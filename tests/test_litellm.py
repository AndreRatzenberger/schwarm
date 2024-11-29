"""Tests for the LiteLLM provider."""

import os
from typing import cast
from unittest.mock import patch, MagicMock

import pytest

from schwarm.models.message import Message
from schwarm.provider.llm_provider import (
    ConfigurationError,
    ConnectionError,
    CompletionError,
    LLMConfig,
    LLMProvider,
    EnvironmentConfig
)


def create_config(
    llm_model_id: str = "gpt-4",
    enable_cache: bool = False,
    enable_debug: bool = False
) -> LLMConfig:
    """Create a LiteLLMConfig with the given parameters."""
    return LLMConfig(
        name=llm_model_id,
        enable_cache=True,
        enable_debug=enable_debug,
        enable_mocking=False,
        environment=EnvironmentConfig(
            override=False,
            variables={}
        )
    )


def create_mock_completion_response(content: str = "Test response") -> MagicMock:
    """Create a mock completion response."""
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(
            model_extra={
                "message": {
                    "content": content,
                    "role": "assistant",
                    "tool_calls": []
                }
            }
        )
    ]
    return mock_response


@pytest.fixture
async def test_provider_initialization():
    """Test basic provider initialization."""
    config = create_config()
    provider = LLMProvider(config)
    assert provider.config == config





@pytest.fixture
async def test_provider_initialization_with_debug():
    """Test provider initialization with debug mode."""
    config = create_config(enable_debug=True)
    provider = LLMProvider(config)
    provider.initialize()
    # Debug mode should be enabled
    assert hasattr(provider, 'config')
    config = cast(LLMConfig, provider.config)
    assert config.enable_debug is True

@pytest.fixture
def test_provider_completion_success():
    """Test successful completion request."""
    expected_response = "Hello, world!"
    mock_response = create_mock_completion_response(expected_response)

    with patch('schwarm.provider.litellm_provider.completion', return_value=mock_response):
        provider = LLMProvider(create_config())
        provider.initialize()

        msg = Message(role="user", content="Test message")
        result = provider.complete([msg])

        assert result.content == expected_response
        assert result.role == "assistant"
        assert result.name == "gpt-4"


@pytest.fixture
def test_provider_completion_with_tools():
    """Test completion with tools enabled."""
    expected_response = "Tool response"
    mock_response = create_mock_completion_response(expected_response)

    with patch('schwarm.provider.litellm_provider.completion', return_value=mock_response):
        provider = LLMProvider(create_config())
        provider.initialize()

        msg = Message(role="user", content="Use tool")
        tools = [{"type": "function", "function": {"name": "test_tool"}}]
        result = provider.complete([msg], tools=tools)

        assert result.content == expected_response
        assert result.role == "assistant"


@pytest.fixture
def test_provider_completion_error():
    """Test completion error handling."""
    with patch('schwarm.provider.litellm_provider.completion', side_effect=Exception("API Error")):
        provider = LLMProvider(create_config())
        with pytest.raises(ConnectionError):
            provider.initialize()




@pytest.fixture
def test_provider_empty_messages():
    """Test handling of empty message list."""
    provider = LLMProvider(create_config())
    provider.initialize()

    with pytest.raises(ValueError):
        provider.complete([])

@pytest.fixture
def test_provider_with_environment_override():
    """Test provider with environment variable override."""
    expected_response = "Environment test"
    mock_response = create_mock_completion_response(expected_response)

    config = create_config()
    config.environment.override = True
    config.environment.variables = {"TEST_VAR": "test_value"}

    with patch('schwarm.provider.litellm_provider.completion', return_value=mock_response):
        provider = LLMProvider(config)
        provider.initialize()

        msg = Message(role="user", content="Test message")
        result = provider.complete([msg])

        assert result.content == expected_response


@pytest.fixture
def test_provider_connection_error():
    """Test provider connection error handling."""
    with patch('schwarm.provider.litellm_provider.completion', side_effect=Exception("Connection failed")):
        provider = LLMProvider(create_config())
        
        with pytest.raises(ConnectionError):
            provider.initialize()


@pytest.fixture
def test_provider_completion_invalid_response():
    """Test handling of invalid completion response."""
    mock_response = MagicMock()
    mock_response.choices = []  # Invalid response format

    with patch('schwarm.provider.litellm_provider.completion', return_value=mock_response):
        provider = LLMProvider(create_config())
        with pytest.raises(ConnectionError, match="Failed to initialize provider: Failed to connect to LLM service"):
            provider.initialize()




@pytest.fixture
def test_provider_async_complete():
    """Test async_complete method."""
    expected_response = "Async response"
    mock_response = create_mock_completion_response(expected_response)

    with patch('schwarm.provider.litellm_provider.completion', return_value=mock_response):
        provider = LLMProvider(create_config())
        provider.initialize()

        msg = Message(role="user", content="Test message")
        result =  provider.complete([msg])

        assert result.content == expected_response
        assert result.role == "assistant"
