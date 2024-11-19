"""Budget tracking provider."""

import csv
import os
from datetime import datetime

from loguru import logger
from pydantic import Field

from schwarm.models.types import Agent, Message
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.models.budget_provider_config import BudgetProviderConfig
from schwarm.utils.settings import APP_SETTINGS


class BudgetProvider(BaseEventHandleProvider):
    """Budget tracking provider that monitors API costs and token usage.

    This provider replaces the BudgetService, handling all budget tracking
    through the event system. It monitors message completions to track costs
    and token usage, persists budget data to CSV, and enforces budget limits.
    """

    config: BudgetProviderConfig

    # Budget tracking state
    current_spent: float = Field(default=0.0, description="Current amount spent")
    current_tokens: int = Field(default=0, description="Current tokens used")

    def handle_start(self) -> None:
        """Handle agent start by initializing budget tracking."""
        # Create logs directory if it doesn't exist
        if self.config.save_budget:
            os.makedirs(f"{APP_SETTINGS.DATA_FOLDER}/logs", exist_ok=True)

    def handle_post_message_completion(self) -> None:
        """Handle post message completion to update budget tracking.

        This handler is called after each message completion, allowing us
        to track the costs and token usage from the LLM API calls.
        """
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
            self._save_to_csv()

            # Check if we've exceeded any limits
            self._check_limits()

    def handle_handoff(self, next_agent: Agent) -> Agent | None:
        """Handle agent handoff to transfer budget state.

        This handler ensures budget tracking continues across agent handoffs
        by transferring the current budget state to the next agent.

        Args:
            next_agent: The agent being handed off to

        Returns:
            The next agent with updated budget state, or None to veto handoff
        """
        if not next_agent:
            return None

        # Get the budget provider from the next agent
        if not self.context:
            logger.warning("No context available for budget handoff")
            return next_agent

        for provider in next_agent.providers:
            if isinstance(provider, BudgetProviderConfig):
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

    def _save_to_csv(self):
        """Save current budget state to CSV file."""
        if not self.config.save_budget:
            return

        timestamp = datetime.now().isoformat()
        filepath = f"{APP_SETTINGS.DATA_FOLDER}/logs/{self.agent.name}_budget.csv"
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
