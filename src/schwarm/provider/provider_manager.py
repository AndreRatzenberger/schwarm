"""A provider factory that creates providers based on the provider type and name."""

from schwarm.core.logging import log_function_call
from schwarm.models.types import Agent
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.models.base_provider_config import BaseProviderConfig
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.provider.models.zep_config import ZepConfig
from schwarm.provider.zep_provider import ZepProvider


class ProviderManager:
    """Factory class for creating providers."""

    def __init__(self):
        """Initializes the provider manager."""
        self._singleton_providers: list[BaseProvider] = []
        self._scoped_providers: dict[str, list[BaseProvider]] = {}

    @log_function_call()
    def initialize(self, agent: Agent):
        """Initializes the provider manager."""
        for provider in agent.providers:
            if provider.provider_lifecycle == "singleton":
                self.add_singleton_provider(agent, provider)
            elif provider.provider_lifecycle == "scoped":
                self.add_scoped_provider(agent, provider)

    @log_function_call()
    def add_singleton_provider(self, agent, config: BaseProviderConfig):
        """Creates a singleton provider based on the provider type and name."""
        for provider in self._singleton_providers:
            if provider.config.provider_name == config.provider_name:
                return None
        provider = ProviderManager.create_provider(config)
        if provider:
            provider.initialize()
            self._singleton_providers.append(provider)

    @log_function_call()
    def add_scoped_provider(self, active_agent: Agent, config: BaseProviderConfig):
        """Creates a scoped provider based on the provider type and name."""
        prov = self._scoped_providers[active_agent.name]

        if prov:
            for provider in prov:
                if provider.config.provider_name == config.provider_name:
                    return None
        provider = ProviderManager.create_provider(config, active_agent)
        if provider:
            provider.initialize()

            if prov:
                prov.append(provider)
            else:
                self._scoped_providers[active_agent.name] = [provider]

    @log_function_call()
    @staticmethod
    def create_provider(config: BaseProviderConfig, agent: Agent | None = None) -> BaseProvider | None:
        """Creates a provider based on the provider type and name."""
        if config.provider_name == "lite_llm" and isinstance(config, LiteLLMConfig):
            return LiteLLMProvider(agent.model if agent else "", config)
        if config.provider_name == "zep" and isinstance(config, ZepConfig) and agent:
            return ZepProvider(agent, config)

    @log_function_call()
    @staticmethod
    def create_llm_provider_from_agent(agent: Agent) -> BaseLLMProvider | None:
        """Creates a provider based on the agent."""
        for provider in agent.providers:
            if provider.provider_name == "lite_llm" and isinstance(provider, LiteLLMConfig):
                return LiteLLMProvider(agent.model, provider)


PROVIDER_MANAGER = ProviderManager()
