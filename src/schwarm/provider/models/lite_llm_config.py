"""Configuration for the Lite LLM provider."""

from pydantic import Field

from schwarm.provider.models.base_llm_provider_config import BaseLLMProviderConfig


class LiteLLMConfig(BaseLLMProviderConfig):
    """Configuration for the Lite LLM provider.

    Attributes:
        enable_cost_tracking: Whether to enable cost tracking
        enable_cache: Whether to enable caching
    """

    enable_cache: bool = Field(default=False, description="Whether to enable cost tracking")
    enable_debug: bool = Field(default=False, description="Whether to enable debug mode")
    enable_mocking: bool = Field(
        default=False, description="Whether to enable mocking"
    )  # TODO: Add this field to the config
