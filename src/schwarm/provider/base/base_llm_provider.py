"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from schwarm.models.message import Message
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig


class BaseLLMProviderConfig(BaseProviderConfig):
    """Configuration for the LLM providers.

    Attributes:
        llm_model_id: The model identifier
    """

    config_type: str = Field(default="llm_provider", description="Configuration type")
    llm_model_id: str = Field(default="gpt-4o-mini", description="The model identifier")


class BaseLLMProvider(BaseProvider, ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to LLM provider."""
        pass

    @abstractmethod
    async def async_complete(
        self, messages: list[Message], override_model: str | None = None, stream: bool | None = False
    ) -> Message:
        """Generate completion for given messages. Async with optional streaming."""
        pass

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        override_model: str | None = None,
        tools: list[dict[str, Any]] = [],
        tool_choice: str = "",
        parallel_tool_calls: bool = True,
    ) -> Message:
        """Generate completion for given messages."""
        pass
