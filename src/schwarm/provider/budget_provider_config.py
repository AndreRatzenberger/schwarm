"""Config for the budget provider."""

from typing import Literal

from pydantic import Field

from schwarm.provider.base.models import BaseEventHandleProviderConfig


class BudgetProviderConfig(BaseEventHandleProviderConfig):
    """Configuration for the budget provider.

    This configuration includes all settings for budget tracking,
    including limits, persistence options, and behavior on limit exceed.
    """

    save_budget: bool = Field(default=True, description="Whether to save budget to CSV")
    show_budget: bool = Field(default=False, description="Whether to show budget in display")
    effect_on_exceed: Literal["warning", "error", "nothing"] = Field(
        default="warning", description="What to do when limits are exceeded"
    )
    max_spent: float = Field(default=10.0, description="Maximum allowed spend")
    max_tokens: int = Field(default=10000, description="Maximum allowed tokens")
    current_spent: float = Field(default=0.0, description="Current amount spent")
    current_tokens: int = Field(default=0, description="Current tokens used")

    def __init__(self, **data):
        """Initialize the budget provider configuration."""
        super().__init__(
            provider_type="event",  # Budget provider is an event handler
            provider_name="budget",
            provider_lifecycle="scoped",
            **data,
        )
