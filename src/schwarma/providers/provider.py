"""Provider module containing the base Provider abstract class."""

from abc import ABC, abstractmethod
from typing import Any


class Provider(ABC):
    """Abstract base class for providers that offer external capabilities to agents.

    Providers serve as interfaces to external services or resources that agents can utilize.
    Each provider must implement the initialize and execute methods.

    Example:
        class LLMProvider(Provider):
            async def initialize(self):
                # Initialize LLM client
                pass

            async def execute(self, prompt: str) -> str:
                # Execute prompt using LLM
                return "Model response"
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider.

        This method should handle any setup required for the provider,
        such as establishing connections or loading resources.

        Returns:
            None
        """
        pass

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the provider's main functionality.

        This method implements the core capability of the provider.

        Args:
            *args: Variable positional arguments specific to the provider implementation
            **kwargs: Variable keyword arguments specific to the provider implementation

        Returns:
            Any: The result of the provider's execution
        """
        pass
