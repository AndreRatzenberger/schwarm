"""Tests for the LLMProvider implementation."""

from unittest.mock import AsyncMock, patch

import pytest

from schwarm.providers.llm_provider import LLMProvider


@pytest.mark.asyncio
async def test_llm_provider_initialization():
    """Test LLMProvider initialization with various parameters."""
    provider = LLMProvider(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=100,
        custom_param="value"
    )
    
    assert provider.model == "gpt-3.5-turbo"
    assert provider.temperature == 0.7
    assert provider.max_tokens == 100
    assert provider.additional_params == {"custom_param": "value"}
    
    # Initialize should not raise any errors
    await provider.initialize()


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_execution(mock_completion):
    """Test LLMProvider execution with mocked completion."""
    # Setup mock response
    mock_response = type("Response", (), {
        "choices": [
            type("Choice", (), {
                "message": type("Message", (), {
                    "content": "Mocked response"
                })
            })
        ]
    })
    mock_completion.return_value = mock_response
    
    provider = LLMProvider(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    result = await provider.execute(
        prompt="Test prompt",
        system_message="Test system message"
    )
    
    assert result == "Mocked response"
    
    # Verify the completion was called with correct parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args[1]
    
    assert call_args["model"] == "gpt-3.5-turbo"
    assert call_args["temperature"] == 0.7
    assert call_args["messages"] == [
        {"role": "system", "content": "Test system message"},
        {"role": "user", "content": "Test prompt"}
    ]


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_without_system_message(mock_completion):
    """Test LLMProvider execution without a system message."""
    mock_response = type("Response", (), {
        "choices": [
            type("Choice", (), {
                "message": type("Message", (), {
                    "content": "Mocked response"
                })
            })
        ]
    })
    mock_completion.return_value = mock_response
    
    provider = LLMProvider(model="gpt-3.5-turbo")
    result = await provider.execute(prompt="Test prompt")
    
    assert result == "Mocked response"
    
    # Verify only user message was sent
    call_args = mock_completion.call_args[1]
    assert call_args["messages"] == [
        {"role": "user", "content": "Test prompt"}
    ]


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_parameter_override(mock_completion):
    """Test that execution parameters can override initialization parameters."""
    mock_response = type("Response", (), {
        "choices": [
            type("Choice", (), {
                "message": type("Message", (), {
                    "content": "Mocked response"
                })
            })
        ]
    })
    mock_completion.return_value = mock_response
    
    provider = LLMProvider(
        model="gpt-3.5-turbo",
        temperature=0.7,
        max_tokens=100
    )
    
    await provider.execute(
        prompt="Test prompt",
        temperature=0.9,
        max_tokens=200
    )
    
    call_args = mock_completion.call_args[1]
    assert call_args["temperature"] == 0.9
    assert call_args["max_tokens"] == 200


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_additional_params(mock_completion):
    """Test that additional parameters are properly passed through."""
    mock_response = type("Response", (), {
        "choices": [
            type("Choice", (), {
                "message": type("Message", (), {
                    "content": "Mocked response"
                })
            })
        ]
    })
    mock_completion.return_value = mock_response
    
    provider = LLMProvider(
        model="gpt-3.5-turbo",
        presence_penalty=0.5,
        frequency_penalty=0.3
    )
    
    await provider.execute(prompt="Test prompt")
    
    call_args = mock_completion.call_args[1]
    assert call_args["presence_penalty"] == 0.5
    assert call_args["frequency_penalty"] == 0.3


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_error_handling(mock_completion):
    """Test that provider properly handles API errors."""
    mock_completion.side_effect = Exception("API Error")
    
    provider = LLMProvider(model="gpt-3.5-turbo")
    
    with pytest.raises(Exception, match="API Error"):
        await provider.execute(prompt="Test prompt")


@pytest.mark.asyncio
@patch("schwarm.providers.llm_provider.completion", new_callable=AsyncMock)
async def test_llm_provider_empty_response_handling(mock_completion):
    """Test handling of empty or invalid responses."""
    # Mock an empty response
    mock_response = type("Response", (), {"choices": []})
    mock_completion.return_value = mock_response
    
    provider = LLMProvider(model="gpt-3.5-turbo")
    
    with pytest.raises(IndexError):
        await provider.execute(prompt="Test prompt")
