"""Provider configuration model."""

from pydantic import Field

from schwarm.provider.models.base_provider_config import BaseProviderConfig


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for a provider.

    Attributes:
        provider_id: The provider id.
    """

    enable_on_message_completion: bool = Field(default=False, description="Whether to enable on_message_completion")
    enable_on_post_message_completion: bool = Field(
        default=False, description="Whether to enable post_message_completion"
    )
    enable_on_tool_execution: bool = Field(default=False, description="Whether to enable on_tool_execution")
    enable_on_post_tool_execution: bool = Field(default=False, description="Whether to enable post_tool_execution")
    enable_on_start: bool = Field(default=False, description="Whether to enable on_start")
    enable_on_handoff: bool = Field(default=False, description="Whether to enable on_handoff")
