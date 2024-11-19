"""Context management provider."""

from typing import Any

from loguru import logger
from pydantic import BaseModel, Field

from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContext
from schwarm.models.types import Agent
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider


class ContextVariables(BaseModel):
    """A dictionary of variables that can be used by agents."""

    variables: dict[str, Any] = Field(
        default_factory=dict, description="A dictionary of variables that can be used by agents."
    )


class ContextProvider(BaseEventHandleProvider):
    """Context management provider that maintains state across agent interactions.

    This provider manages context variables and message history, ensuring
    consistent state across agent handoffs and interactions.
    """

    variables: ContextVariables = Field(
        default_factory=ContextVariables, description="A dictionary of variables that can be used by agents."
    )

    def handle_start(self) -> None:
        """Handle agent start by initializing context.

        This handler ensures the provider has a valid context when an agent starts,
        either creating a new one or updating the existing one.
        """
        if not self.context:
            # Initialize new context if none exists
            self.context = ProviderContext(
                current_agent=self.agent, message_history=[], context_variables=self.variables.variables
            )
            logger.debug(f"Initialized new context for agent {self.agent.name}")
        else:
            # Update existing context with current agent
            self.context.current_agent = self.agent
            logger.debug(f"Updated context for agent {self.agent.name}")

    def handle_post_message_completion(self) -> None:
        """Handle post message completion to update context.

        This handler updates the context after each message completion,
        maintaining the message history and any additional info that
        might contain context-relevant data.
        """
        if not self.context:
            logger.warning("No context available for update")
            return

        # Get the latest message
        if not self.context.message_history:
            return

        latest_message = self.context.message_history[-1]
        if not isinstance(latest_message, Message):
            return

        # Check additional_info for any context variables
        if "context_variables" in latest_message.additional_info:
            new_vars = latest_message.additional_info["context_variables"]
            self.variables.variables.update(new_vars)
            self.context.context_variables = self.variables.variables
            logger.debug(f"Updated context variables: {new_vars}")

    def handle_handoff(self, next_agent: Agent) -> Agent | None:
        """Handle agent handoff to transfer context.

        This handler ensures context is maintained across agent handoffs
        by transferring the current context to the next agent.

        Args:
            next_agent: The agent being handed off to

        Returns:
            The next agent, or None to veto handoff
        """
        if not next_agent:
            return None

        if not self.context:
            logger.warning("No context available for handoff")
            return next_agent

        # Update context with next agent
        self.context.current_agent = next_agent
        logger.debug(f"Transferred context to agent {next_agent.name}")

        return next_agent

    def handle_tool_execution(self) -> None:
        """Handle tool execution to update context.

        This handler is called before tool execution, allowing us to
        provide the tool with current context variables.
        """
        if not self.context:
            logger.warning("No context available for tool execution")
            return

        # Ensure context variables are up to date
        self.context.context_variables = self.variables.variables

    def handle_post_tool_execution(self) -> None:
        """Handle post tool execution to update context.

        This handler updates the context after tool execution,
        capturing any changes to context variables or message history.
        """
        if not self.context:
            logger.warning("No context available after tool execution")
            return

        # Update our variables with any changes from tool execution
        self.variables.variables = self.context.context_variables
