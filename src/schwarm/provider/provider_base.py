"""Base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any

from schwarm.models.message import Message
from schwarm.models.provider_config import ProviderConfig


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    config: ProviderConfig

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

    @staticmethod
    def build_provider_list() -> list["LLMProvider"]:
        """Build a list of available LLM providers."""
        return []
