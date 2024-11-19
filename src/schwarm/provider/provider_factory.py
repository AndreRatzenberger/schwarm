"""A provider factory that creates providers based on the provider type and name."""

from schwarm.models.types import Agent
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.models.base_provider_config import BaseProviderConfig
from schwarm.provider.models.lite_llm_config import LiteLLMConfig


class ProviderFactory:
    """Factory class for creating providers."""

    @staticmethod
    def create_provider(agent, config: BaseProviderConfig):
        """Creates a provider based on the provider type and name."""
        if config.provider_name == "lite_llm" and isinstance(config, LiteLLMConfig):
            return LiteLLMProvider(agent, config)

    @staticmethod
    def create_llm_provider_from_agent(agent: Agent):
        """Creates a provider based on the agent."""
        for provider in agent.providers:
            if provider.provider_name == "lite_llm" and isinstance(provider, LiteLLMConfig):
                return LiteLLMProvider(agent.model, provider)
