"""LLM provider implementation using litellm."""

from typing import Any

from litellm import acompletion

from .provider import Provider


class AgentLLMProvider(Provider):
    """Provider for interacting with Language Models through litellm.

    This provider offers a unified interface to various LLM providers
    (like OpenAI, Anthropic, etc.) through litellm.

    Example:
        provider = LLMProvider(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        await provider.initialize()
        response = await provider.execute(
            "Explain what a neural network is."
        )
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int | None = None, **kwargs: Any) -> None:
        """Initialize the LLM provider.

        Args:
            model: The model identifier (e.g., "gpt-3.5-turbo")
            temperature: Controls randomness in responses (0.0 to 1.0)
            max_tokens: Maximum tokens in the response
            **kwargs: Additional parameters to pass to the model
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.additional_params = kwargs

    async def initialize(self) -> None:
        """Initialize the provider.

        Note:
            Currently, no initialization is needed as litellm handles
            connection management internally.
        """
        pass

    async def execute(self, prompt: str, system_message: str | None = None, **kwargs: Any) -> str:
        """Execute an LLM query.

        Args:
            prompt: The user prompt to send to the model
            system_message: Optional system message for chat models
            **kwargs: Additional parameters to override defaults

        Returns:
            The model's response text

        Note:
            This implementation assumes chat model format. For completion-only
            models, modifications might be needed.
        """
        messages = []

        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Add user message
        messages.append({"role": "user", "content": prompt})

        # Prepare parameters
        params: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **self.additional_params,
        }

        # Apply max_tokens if set, allowing override from kwargs
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs.pop("max_tokens")
        elif self.max_tokens is not None:
            params["max_tokens"] = self.max_tokens

        # Apply any remaining kwargs
        params.update(kwargs)

        # Execute the query
        response = await acompletion(**params)

        # Extract and return the response text
        return response.choices[0].message.content  # type: ignore
