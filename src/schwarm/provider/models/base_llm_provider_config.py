"""Base configuration for LLM providers."""

from pydantic import Field

from schwarm.provider.models.base_provider_config import BaseProviderConfig


class BaseLLMProviderConfig(BaseProviderConfig):
    """Configuration for the LLM providers.

    Attributes:
        model_id: The model identifier
    """

    model_id: str = Field(default="", description="The model identifier")
