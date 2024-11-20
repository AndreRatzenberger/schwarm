"""Base configuration for LLM providers."""

from pydantic import Field

from schwarm.provider.base.base_provider_config import BaseProviderConfig


class BaseLLMProviderConfig(BaseProviderConfig):
    """Configuration for the LLM providers.

    Attributes:
        llm_model_id: The model identifier
    """

    llm_model_id: str = Field(default="", description="The model identifier")
