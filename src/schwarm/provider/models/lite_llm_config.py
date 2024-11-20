"""Configuration for the Lite LLM provider."""

from pydantic import Field

from schwarm.provider.models.base_llm_provider_config import BaseLLMProviderConfig


class LiteLLMConfig(BaseLLMProviderConfig):
    """Configuration for the Lite LLM provider.

    See LiteLLM docs for which model needs what environment variables.


    Attributes:
        env_var_override: Whether to override environment variables
        env_vars: Environment variables to override
        enable_cost_tracking: Whether to enable cost tracking
        enable_cache: Whether to enable caching
    """

    env_var_override: bool = Field(default=False, description="Whether to override environment variables")
    env_vars: dict[str, str] = Field(
        default_factory=dict, description="Environment variables EXCEPT API_KEY to override"
    )
    enable_cache: bool = Field(default=False, description="Whether to enable cost tracking")
    enable_debug: bool = Field(default=False, description="Whether to enable debug mode")
    enable_mocking: bool = Field(
        default=False, description="Whether to enable mocking"
    )  # TODO: Add this field to the config
