"""Provider configuration model."""

import csv
import os
from datetime import datetime
from typing import Literal

from loguru import logger
from pydantic import BaseModel, Field

from schwarm.utils.settings import APP_SETTINGS


class BudgetService(BaseModel):
    """Configuration for a rendering service.

    Attributes:
        print_function_calls: display function calls
        wait_for_user_input_on_function_calls: If the process stops and waits for user input on function calls
    """

    save_budget: bool = Field(default=True, description="Save budget")
    show_budget: bool = Field(default=False, description="Show budget")
    effect_on_exceed: Literal["warning", "error", "nothing"] = Field(default="warning", description="Effect on exceed")
    max_spent: float = Field(default=10.0, description="Max spent")
    max_tokens: int = Field(default=10000, description="Max tokens")
    current_spent: float = Field(default=0.0, description="Current spent")
    current_tokens: int = Field(default=0, description="Current tokens")

    def save_to_csv(self, agent_name: str):
        """Save current budget state to CSV file.

        Args:
            agent_name: Name of the agent for the log file
        """
        if not self.save_budget:
            return

        timestamp = datetime.now().isoformat()
        filepath = f"{APP_SETTINGS.DATA_FOLDER}/logs/{agent_name}_budget.csv"
        file_exists = os.path.exists(filepath)
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, mode="a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "current_spent", "max_spent", "current_tokens", "max_tokens"])
            writer.writerow([timestamp, self.current_spent, self.max_spent, self.current_tokens, self.max_tokens])

    def check_limits(self):
        """Check if budget or token limits are exceeded and handle according to effect_on_exceed setting."""
        if self.current_spent > self.max_spent:
            message = f"Budget exceeded: current_spent={self.current_spent}, max_spent={self.max_spent}"
            self._handle_exceed(message)

        if self.current_tokens > self.max_tokens:
            message = f"Token limit exceeded: current_tokens={self.current_tokens}, max_tokens={self.max_tokens}"
            self._handle_exceed(message)

    def _handle_exceed(self, message: str):
        """Handle exceeded limits based on effect_on_exceed setting.

        Args:
            message: The error/warning message to display

        Raises:
            ValueError: If effect_on_exceed is set to "error"
        """
        if self.effect_on_exceed == "warning":
            logger.warning(message)
        elif self.effect_on_exceed == "error":
            logger.error(message)
            raise ValueError(message)
