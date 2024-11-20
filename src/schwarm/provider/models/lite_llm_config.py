"""Configuration for the LiteLLM provider."""

from pydantic import BaseModel, Field

from schwarm.provider.models.base_llm_provider_config import BaseLLMProviderConfig


class EnvironmentConfig(BaseModel):
    """Configuration for environment variable handling.

    Attributes:
        override: Whether to override environment variables
        variables: Environment variables to override (excluding API_KEY)
    """

    override: bool = Field(default=False, description="Controls whether environment variables should be overridden")
    variables: dict[str, str] = Field(
        default_factory=dict, description="Environment variables to override (excluding API_KEY)"
    )


class FeatureFlags(BaseModel):
    """Feature flags for LiteLLM provider.

    Attributes:
        cache: Whether to enable response caching
        debug: Whether to enable debug mode
        mocking: Whether to enable mock responses
    """

    cache: bool = Field(default=False, description="Enables response caching for improved performance")
    debug: bool = Field(default=False, description="Enables debug mode for detailed logging")
    mocking: bool = Field(default=False, description="Enables mock responses for testing purposes")


class LiteLLMConfig(BaseLLMProviderConfig):
    """Configuration for the LiteLLM provider.

    This configuration class manages settings for the LiteLLM provider,
    including environment variable handling and feature flags.

    See LiteLLM documentation for model-specific environment variable requirements.

    Attributes:
        environment: Environment variable configuration
        features: Feature flag configuration
    """

    environment: EnvironmentConfig = Field(
        default_factory=EnvironmentConfig, description="Environment variable configuration"
    )
    features: FeatureFlags = Field(default_factory=FeatureFlags, description="Feature flag configuration")
