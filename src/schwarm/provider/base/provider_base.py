"""Base class for LLM providers."""

from abc import ABC, abstractmethod

from schwarm.provider.models import ProviderConfig


class ProviderBase(ABC):
    """Abstract base class for LLM providers."""

    config: ProviderConfig

    @abstractmethod
    def on_start(self) -> None:
        """Run when an agent is started."""
        pass

    @abstractmethod
    def on_handoff(self) -> None:
        """Run when an agent is handing off his task to another agent."""
        pass

    @abstractmethod
    def on_message_completion(self) -> None:
        """Run when an agent is sending a message."""
        pass

    @abstractmethod
    def on_tool_execution(self) -> None:
        """Run when an agent is executing a tool."""
        pass

    @abstractmethod
    def on_post_message_completion(self) -> None:
        """Run after a message is sent and result is received."""
        pass

    @abstractmethod
    def on_post_tool_execution(self) -> None:
        """Run after a tool is executed and result is received."""
        pass
