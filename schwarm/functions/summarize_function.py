"""Summarization function implementation."""

from typing import Optional

from ..context import Context
from ..function import Function
from ..providers.llm_provider import LLMProvider


async def summarize_text(
    context: Context,
    text: str,
    max_length: Optional[int] = None
) -> str:
    """Summarize the given text using an LLM provider.
    
    Args:
        context: The shared context object
        text: The text to summarize
        max_length: Optional target length for the summary
        
    Returns:
        A summary of the input text
        
    Raises:
        ValueError: If no LLM provider is available in the context
    """
    # Get the LLM provider from context
    provider = context.get("llm_provider")
    if not isinstance(provider, LLMProvider):
        raise ValueError("LLM provider not found in context")
        
    # Construct the prompt
    prompt = f"Please summarize the following text"
    if max_length:
        prompt += f" in approximately {max_length} words"
    prompt += f":\n\n{text}"
    
    # Use the provider to generate the summary
    system_message = (
        "You are a helpful assistant specialized in creating clear and "
        "concise summaries while preserving the key information."
    )
    
    return await provider.execute(
        prompt=prompt,
        system_message=system_message
    )


# Create the function instance
summarize_function = Function(
    name="summarize",
    implementation=summarize_text,
    description="Summarizes text using an LLM provider"
)
