"""Base class for providers."""

from abc import abstractmethod

from schwarm.context.context import SCHWARM_CONTEXT
from schwarm.models.types import Agent
from schwarm.provider.base.base_provider import BaseProvider


class BaseEventHandleProvider(BaseProvider):
    """Abstract base class for providers."""

    @abstractmethod
    def on_start(self) -> None:
        """Run when an agent is started."""
        SCHWARM_CONTEXT.add_agent(self.agent.name)

    @abstractmethod
    def on_handoff(self, next_agent: Agent) -> Agent | None:
        """Run when an agent is handing off his task to another agent."""
        SCHWARM_CONTEXT.add_agent(self.agent.name, next_agent.name)

    @abstractmethod
    def on_message_completion(self) -> None:
        """Run when an agent is sending a message."""
        SCHWARM_CONTEXT.add_event(f"Message sent by {self.agent.name}")

    @abstractmethod
    def on_tool_execution(self) -> None:
        """Run when an agent is executing a tool."""
        SCHWARM_CONTEXT.add_event(f"Tool executed by {self.agent.name}")

    @abstractmethod
    def on_post_message_completion(self) -> None:
        """Run after a message is sent and result is received."""
        SCHWARM_CONTEXT.add_event(f"Message received by {self.agent.name}")

    @abstractmethod
    def on_post_tool_execution(self) -> None:
        """Run after a tool is executed and result is received."""
        SCHWARM_CONTEXT.add_event(f"Tool result received by {self.agent.name}")
