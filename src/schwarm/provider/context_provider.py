"""provides agents with context."""

from typing import Any

from pydantic import BaseModel, Field

from schwarm.provider.base import BaseEventHandleProvider
from schwarm.provider.models.context_config import ContextConfig


class ContextVariables(BaseModel):
    """A dictionary of variables that can be used by agents."""

    variables: dict[str, Any] = Field(
        default_factory=dict, description="A dictionary of variables that can be used by agents."
    )


class ContextProvider(BaseEventHandleProvider):
    """Knowledge graph provider with infinite memory."""

    config: ContextConfig = Field(..., description="Configuration for the config provider.")
    variables: ContextVariables = Field(
        default_factory=ContextVariables, description="A dictionary of variables that can be used by agents."
    )

    def initialize(self, randomize_user_id: bool = False) -> None:
        """Initializes the provider."""

    def on_start(self):
        super().on_start()

    def on_handoff(self, next_agent):
        super().on_handoff(next_agent)

    def on_message_completion(self):
        super().on_message_completion()

    def on_tool_execution(self):
        super().on_tool_execution()

    def on_post_message_completion(self):
        super().on_post_message_completion()

    def on_post_tool_execution(self):
        super().on_post_tool_execution()
