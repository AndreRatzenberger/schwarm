"""LLM provider implementation using LiteLLM."""

from dataclasses import dataclass
from typing import Any, Literal

import litellm
from pydantic import BaseModel
from schwarma_core.provider import Provider


@dataclass
class Message:
    """Message structure for LLM interactions."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None


class LLMConfig(BaseModel):
    """Configuration for the LLM provider.

    Attributes:
        model: The model identifier (e.g., "gpt-4")
        temperature: Controls randomness in responses
        max_tokens: Maximum tokens in response
        streaming: Whether to stream responses
        cache_responses: Whether to cache responses
    """

    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int | None = None
    streaming: bool = False
    cache_responses: bool = False


class LLMProvider(Provider):
    """Provider for language model interactions using LiteLLM.

    This provider offers a clean interface to language models through LiteLLM,
    supporting various models while maintaining a simple API.

    Example:
        config = LLMConfig(model="gpt-4", temperature=0.7)
        provider = LLMProvider(config)
        await provider.initialize()
        response = await provider.execute(
            messages=[
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello!")
            ]
        )
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the LLM provider.

        Args:
            config: Provider configuration
        """
        self.config = config
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the provider.

        Sets up caching if enabled and validates the configuration.
        """
        if self.config.cache_responses:
            litellm.cache = litellm.Cache(type="disk", disk_cache_dir=".llm_cache")  # type: ignore

        litellm.drop_params = True
        self._initialized = True

    async def execute(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | None = None,
    ) -> Message:
        """Execute the provider with the given messages.

        Args:
            messages: List of messages in the conversation
            tools: Optional list of tools available to the model
            tool_choice: Optional tool selection strategy

        Returns:
            The model's response as a Message

        Raises:
            RuntimeError: If provider not initialized
            ValueError: If messages list is empty
        """
        if not self._initialized:
            raise RuntimeError("Provider not initialized")
        if not messages:
            raise ValueError("At least one message is required")

        # Convert messages to LiteLLM format
        llm_messages = [
            {
                "role": msg.role,
                "content": msg.content,
                "name": msg.name,
                "tool_calls": msg.tool_calls,
                "tool_call_id": msg.tool_call_id,
            }
            for msg in messages
        ]

        # Prepare completion kwargs
        completion_kwargs = {
            "model": self.config.model,
            "messages": llm_messages,
            "temperature": self.config.temperature,
            "stream": self.config.streaming,
        }

        if self.config.max_tokens:
            completion_kwargs["max_tokens"] = self.config.max_tokens

        if tools:
            completion_kwargs.update(
                {
                    "tools": tools,
                    "tool_choice": tool_choice or "auto",
                }
            )

        try:
            # Execute completion
            response = await litellm.acompletion(**completion_kwargs)

            # Extract response content
            choice = response.choices[0]
            message = choice.message

            # Convert to our Message format
            return Message(
                role=message.role,
                content=message.content or "",
                tool_calls=getattr(message, "tool_calls", None),
            )

        except Exception as e:
            # Re-raise with more context
            raise RuntimeError(f"LLM execution failed: {e!s}") from e
