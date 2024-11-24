"""Budget tracking provider."""

import csv
import os
from datetime import datetime
from typing import Literal

from loguru import logger
from pydantic import Field

from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContextModel
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.utils.settings import APP_SETTINGS


class BudgetConfig(BaseEventHandleProviderConfig):
    """Configuration for the budget provider.

    This configuration includes all settings for budget tracking,
    including limits, persistence options, and behavior on limit exceed.
    """

    save_budget: bool = Field(default=True, description="Whether to save budget to CSV")
    show_budget: bool = Field(default=False, description="Whether to show budget in display")
    effect_on_exceed: Literal["warning", "error", "nothing"] = Field(
        default="warning", description="Action on limit exceed"
    )
    max_spent: float = Field(default=10.0, description="Maximum allowed spend")
    max_tokens: int = Field(default=10000, description="Maximum allowed tokens")
    current_spent: float = Field(default=0.0, description="Current amount spent")
    current_tokens: int = Field(default=0, description="Current tokens used")


class BudgetProvider(BaseEventHandleProvider):
    """Budget tracking provider that monitors API costs and token usage.

    This provider replaces the BudgetService, handling all budget tracking
    through the event system. It monitors message completions to track costs
    and token usage, persists budget data to CSV, and enforces budget limits.
    """

    config: BudgetConfig
    _provider_id: str = Field(default="budget", description="Provider ID")

    def __init__(self, **data):
        """Initialize the budget provider with tracking state."""
        super().__init__(**data)
        self.current_spent = self.config.current_spent
        self.current_tokens = self.config.current_tokens

    def handle_event(self, event):
        """Handle an event by updating budget tracking and enforcing limits."""
        if event.type == "start":
            self.handle_start(event.context)
        elif event.type == "post_message_completion":
            self.handle_post_message_completion(event.context)
        elif event.type == "handoff":
            return self.handle_handoff(event.context)

        return super().handle_event(event)

    def handle_start(self, context: ProviderContextModel) -> None:
        """Handle agent start by initializing budget tracking."""
        # Create logs directory if it doesn't exist
        if self.config.save_budget:
            os.makedirs(f"{APP_SETTINGS.DATA_FOLDER}/logs", exist_ok=True)

    def handle_post_message_completion(self, provider_context: ProviderContextModel) -> None:
        """Handle post message completion to update budget tracking.

        This handler is called after each message completion, allowing us
        to track the costs and token usage from the LLM API calls.
        """
        agent = provider_context.current_agent
        if not self.context:
            logger.warning("No context available for budget tracking")
            return

        # Get the latest message from history
        if not self.context.message_history:
            return

        latest_message = self.context.message_history[-1]
        if not isinstance(latest_message, Message):
            return

        # Update budget tracking if message has cost info
        if latest_message.info:
            self.current_spent += latest_message.info.completion_cost
            logger.debug(f"Added completion cost: {latest_message.info.completion_cost}")

            self.current_tokens += latest_message.info.token_counter
            logger.debug(f"Added tokens: {latest_message.info.token_counter}")

            # Save updated budget to CSV
            self._save_to_csv(agent.name)

            # Check if we've exceeded any limits
            self._check_limits()

    def handle_handoff(self, event: ProviderContextModel) -> None:
        """Handle agent handoff to transfer budget state.

        This handler ensures budget tracking continues across agent handoffs
        by transferring the current budget state to the next agent.

        Args:
            next_agent: The agent being handed off to

        Returns:
            The next agent with updated budget state, or None to veto handoff
        """
        next_agent = event.available_agents[-1]("next_agent")
        if not next_agent:
            return None

        # Get the budget provider from the next agent
        if not self.context:
            logger.warning("No context available for budget handoff")
            return next_agent

        for provider in next_agent.provider_configurations:
            if isinstance(provider, BudgetConfig):
                # Transfer our current state
                provider.current_spent = self.current_spent
                provider.current_tokens = self.current_tokens
                logger.debug(
                    f"Transferred budget state to {next_agent.name}: "
                    f"spent=${self.current_spent:.2f}, "
                    f"tokens={self.current_tokens}"
                )
                break

        return next_agent

    def _save_to_csv(self, name: str):
        """Save current budget state to CSV file."""
        if not self.config.save_budget:
            return

        timestamp = datetime.now().isoformat()
        filepath = f"{APP_SETTINGS.DATA_FOLDER}/logs/{name}_budget.csv"
        file_exists = os.path.exists(filepath)

        with open(filepath, mode="a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "current_spent", "max_spent", "current_tokens", "max_tokens"])
            writer.writerow(
                [timestamp, self.current_spent, self.config.max_spent, self.current_tokens, self.config.max_tokens]
            )

    def _check_limits(self):
        """Check if budget or token limits are exceeded and handle according to effect_on_exceed setting."""
        if self.current_spent > self.config.max_spent:
            message = f"Budget exceeded: current_spent={self.current_spent}, max_spent={self.config.max_spent}"
            self._handle_exceed(message)

        if self.current_tokens > self.config.max_tokens:
            message = f"Token limit exceeded: current_tokens={self.current_tokens}, max_tokens={self.config.max_tokens}"
            self._handle_exceed(message)

    def _handle_exceed(self, message: str):
        """Handle exceeded limits based on effect_on_exceed setting.

        Args:
            message: The error/warning message to display

        Raises:
            ValueError: If effect_on_exceed is set to "error"
        """
        if self.config.effect_on_exceed == "warning":
            logger.warning(message)
        elif self.config.effect_on_exceed == "error":
            logger.error(message)
            raise ValueError(message)
