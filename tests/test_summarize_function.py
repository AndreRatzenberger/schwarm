"""Tests for the summarize function implementation."""

from unittest.mock import Mock

import pytest

from schwarm.context.context import Context
from schwarm.functions.text_functions import summarize_function
from schwarm.providers.simple_llm_provider import SimpleLLMProvider


@pytest.mark.asyncio
async def test_summarize_without_provider():
    """Test that summarize fails appropriately when no provider is available."""
    context = Context()
    
    with pytest.raises(ValueError, match="LLM provider not found in context"):
        await summarize_function.execute(
            context,
            "Test text to summarize"
        )


@pytest.mark.asyncio
async def test_summarize_with_invalid_provider():
    """Test that summarize fails when an invalid provider is set."""
    context = Context()
    context.set("llm_provider", "not a provider")
    
    with pytest.raises(ValueError, match="LLM provider not found in context"):
        await summarize_function.execute(
            context,
            "Test text to summarize"
        )


@pytest.mark.asyncio
async def test_summarize_basic():
    """Test basic summarization functionality."""
    context = Context()
    
    # Create a mock provider
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.return_value = "Summarized text"
    context.set("llm_provider", mock_provider)
    
    result = await summarize_function.execute(
        context,
        "Test text to summarize"
    )
    
    assert result == "Summarized text"
    mock_provider.execute.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_with_max_length():
    """Test summarization with max length parameter."""
    context = Context()
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.return_value = "Short summary"
    context.set("llm_provider", mock_provider)
    
    await summarize_function.execute(
        context,
        "Test text to summarize",
        max_length=50
    )
    
    # Verify the prompt includes the max length
    call_args = mock_provider.execute.call_args[1]
    assert "50 words" in call_args["prompt"]


@pytest.mark.asyncio
async def test_summarize_provider_error():
    """Test handling of provider errors during summarization."""
    context = Context()
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.side_effect = Exception("Provider error")
    context.set("llm_provider", mock_provider)
    
    with pytest.raises(Exception, match="Provider error"):
        await summarize_function.execute(
            context,
            "Test text to summarize"
        )


@pytest.mark.asyncio
async def test_summarize_empty_text():
    """Test summarization of empty text."""
    context = Context()
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.return_value = ""
    context.set("llm_provider", mock_provider)
    
    result = await summarize_function.execute(context, "")
    assert result == ""


@pytest.mark.asyncio
async def test_summarize_long_text():
    """Test summarization of a longer text."""
    context = Context()
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.return_value = "Summary of long text"
    context.set("llm_provider", mock_provider)
    
    long_text = " ".join(["word"] * 1000)  # Create a long text
    result = await summarize_function.execute(context, long_text)
    
    assert result == "Summary of long text"
    mock_provider.execute.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_system_message():
    """Test that the system message is properly formatted."""
    context = Context()
    mock_provider = Mock(spec=SimpleLLMProvider)
    mock_provider.execute.return_value = "Summary"
    context.set("llm_provider", mock_provider)
    
    await summarize_function.execute(
        context,
        "Test text"
    )
    
    call_args = mock_provider.execute.call_args[1]
    assert "system_message" in call_args
    assert "specialized in creating clear and concise summaries" in call_args["system_message"]


@pytest.mark.asyncio
async def test_summarize_function_metadata():
    """Test the function's metadata."""
    assert summarize_function.name == "summarize"
    assert "summarize" in summarize_function.description.lower()
