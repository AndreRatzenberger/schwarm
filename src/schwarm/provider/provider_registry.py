"""Provider manager for handling provider lifecycle and events."""

from typing import Any

from loguru import logger

from schwarm.models.agent import Agent
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.models.base_provider_config import BaseProviderConfig
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.zep_provider import ZepProvider


class ProviderRegistry:
    """Manages provider lifecycle and event handling.

    The ProviderRegistry class is responsible for managing provider lifecycle and event handling.
    Schwarm agents can access providers through the provider registry, which handles provider creation,
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance of the provider registry."""
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize the provider registry."""
        # Initialize the provider registry

        # Singleton:
        # The singleton_providers attribute is a dictionary that stores singleton providers.
        # Lifetime: Start of the application until the end of the application.
        # Scope: All agents in the application access the same singleton provider instance.

        # Scoped:
        # the scoped_providers attribute is a dictionary that stores scoped providers.
        # Lifetime: tart of the application until the end of the application.
        # Scope: Each agent has its own scoped provider instances.

        # Stateless:
        # Lifetime: get created when called. we don't have to store them.
        # Scope: Created on-demand.

        self._agents: dict[str, Agent] = {}

        self._singleton_providers: dict[str, BaseProvider] = {}
        self._scoped_providers: dict[str, dict[str, BaseProvider]] = {}
        self._types: dict[str, type[BaseProvider]] = {
            "lite_llm": LiteLLMProvider,
            "zep": ZepProvider,
        }

    def handle_event(self, event_name: str, **kwargs: Any) -> dict[str, Any]:
        """Handle an event by dispatching to all providers.

        Args:
            event_name: Name of the event to handle
            **kwargs: Event data to pass to handlers

        Returns:
            dict: Result of handling the event by each provider
        """
        result = {}
        for provider in self._get_event_providers():
            try:
                provider_result = provider.handle_event(event_name, **kwargs)
                if provider_result:
                    result[provider.provider_name] = provider_result
            except Exception as e:
                logger.error(f"Error handling event {event_name} in provider {provider.provider_name}: {e}")
        return result

    def get_provider(
        self, agent_name: str, provider_name: str, provider_config: BaseProviderConfig | None = None
    ) -> BaseProvider | None:
        """Get a provider instance for an agent.

        This method handles provider lifecycle management, returning:
        - Singleton provider if it exists
        - Scoped provider for the agent if it exists
        - New stateless provider instance if neither exists

        Args:
            agent_name: The agent requesting the provider
            provider_name: Name of the provider to get

        Returns:
            Provider instance or None if not found/created
        """
        # Check singleton providers first
        if provider_name in self._singleton_providers:
            return self._singleton_providers[provider_name]

        # Check scoped providers for this agent
        agent_providers = self._scoped_providers.get(agent_name, {})
        if provider_name in agent_providers:
            return agent_providers[provider_name]

        # stateless providers need to be created on-demand with a provider config
        if not provider_config:
            logger.warning(f"No provider config found for {provider_name}")
            return None

        # Create new stateless provider if needed
        agent = self._agents.get(agent_name)
        if provider_config.provider_lifecycle == "stateless":
            return self._create_provider(provider_config, agent)

        return None

    def _get_event_providers(self) -> list[Any]:
        """Get all providers that can handle events.

        Returns:
            List of event-handling providers
        """
        providers = []
        for provider_config in self.agent.provider_configurations:
            provider = self.agent.get_provider(provider_config.provider_name)
            if provider and hasattr(provider, "handle_event"):
                providers.append(provider)
        return providers

    def get_llm_provider(self) -> BaseLLMProvider | None:
        """Get the LLM provider for this agent.

        Returns:
            LLM provider instance or None if not found
        """
        return self.agent.get_llm_provider()

    def _create_provider(self, config: BaseProviderConfig, agent: Agent | None = None) -> BaseProvider | None:
        """Create a provider instance based on configuration.

        Args:
            config: Provider configuration
            agent: Optional agent context

        Returns:
            Created provider instance or None if creation fails
        """
        try:
            provider_name = config.provider_name
            provider_class = self._types.get(provider_name)
            if not provider_class:
                logger.warning(f"No provider class registered for {provider_name}")
                return None

            if issubclass(provider_class, BaseLLMProvider):
                if not agent:
                    raise ValueError("Agent required for LLM provider creation")
                return provider_class(agent.model, config)
            if agent:
                return provider_class(agent, config)
            return None
        except Exception as e:
            logger.error(f"Failed to create provider {config.provider_name}: {e}")
            return None


# """A provider factory that creates providers based on the provider type and name."""

# from loguru import logger

# from schwarm.core.logging import log_function_call
# from schwarm.models.types import Agent
# from schwarm.provider.base.base_llm_provider import BaseLLMProvider
# from schwarm.provider.base.base_provider import BaseProvider
# from schwarm.provider.litellm_provider import LiteLLMProvider
# from schwarm.provider.models.base_provider_config import BaseProviderConfig
# from schwarm.provider.models.lite_llm_config import LiteLLMConfig
# from schwarm.provider.zep_provider import ZepProvider


# class ProviderManager:
#     """Factory class for creating and managing providers.

#     This class handles provider lifecycle management (singleton/scoped/stateless),
#     provider initialization, and provider type-specific operations.
#     """

#     def __init__(self):
#         """Initialize the provider manager."""
#         self._singleton_providers: dict[str, BaseProvider] = {}
#         self._scoped_providers: dict[str, dict[str, BaseProvider]] = {}
#         self._provider_registry: dict[str, type[BaseProvider]] = {
#             "lite_llm": LiteLLMProvider,
#             "zep": ZepProvider,
#         }

#     @log_function_call()
#     def initialize(self, agent: Agent) -> None:
#         """Initialize providers for an agent.

#         This method handles provider lifecycle management, ensuring providers
#         are created and initialized according to their lifecycle configuration.

#         Args:
#             agent: The agent to initialize providers for
#         """
#         logger.info(f"Initializing providers for agent {agent.name}")

#         # Initialize scoped providers dict for this agent if needed
#         if agent.name not in self._scoped_providers:
#             self._scoped_providers[agent.name] = {}

#         for provider_config in agent.providers:
#             try:
#                 if provider_config.provider_lifecycle == "singleton":
#                     self._add_singleton_provider(agent, provider_config)
#                 elif provider_config.provider_lifecycle == "scoped":
#                     self._add_scoped_provider(agent, provider_config)
#                 elif provider_config.provider_lifecycle == "stateless":
#                     # Stateless providers are created on-demand
#                     pass
#                 else:
#                     logger.warning(f"Unknown provider lifecycle: {provider_config.provider_lifecycle}")
#             except Exception as e:
#                 logger.error(f"Failed to initialize provider {provider_config.provider_name}: {e}")

#     def _add_singleton_provider(self, agent: Agent, config: BaseProviderConfig) -> None:
#         """Add a singleton provider if it doesn't already exist.

#         Args:
#             agent: The agent requesting the provider
#             config: Provider configuration
#         """
#         if config.provider_name not in self._singleton_providers:
#             provider = self._create_provider(config, agent)
#             if provider:
#                 provider.initialize()
#                 self._singleton_providers[config.provider_name] = provider
#                 logger.info(f"Created singleton provider: {config.provider_name}")

#     def _add_scoped_provider(self, agent: Agent, config: BaseProviderConfig) -> None:
#         """Add a scoped provider for an agent if it doesn't already exist.

#         Args:
#             agent: The agent to create the provider for
#             config: Provider configuration
#         """
#         agent_providers = self._scoped_providers[agent.name]
#         if config.provider_name not in agent_providers:
#             provider = self._create_provider(config, agent)
#             if provider:
#                 provider.initialize()
#                 agent_providers[config.provider_name] = provider
#                 logger.info(f"Created scoped provider: {config.provider_name} for agent {agent.name}")

#     def _create_provider(self, config: BaseProviderConfig, agent: Agent | None = None) -> BaseProvider | None:
#         """Create a provider instance based on configuration.

#         Args:
#             config: Provider configuration
#             agent: Optional agent context

#         Returns:
#             Created provider instance or None if creation fails
#         """
#         provider_class = self._provider_registry.get(config.provider_name)
#         if not provider_class:
#             logger.warning(f"No provider class registered for {config.provider_name}")
#             return None

#         try:
#             if issubclass(provider_class, BaseLLMProvider):
#                 if not agent:
#                     raise ValueError("Agent required for LLM provider creation")
#                 if isinstance(config, LiteLLMConfig):
#                     return provider_class(agent.model, config)
#             if agent:
#                 return provider_class(agent, config)
#             return None
#         except Exception as e:
#             logger.error(f"Failed to create provider {config.provider_name}: {e}")
#             return None

#     def get_provider(self, agent: Agent, provider_name: str) -> BaseProvider | None:
#         """Get a provider instance for an agent.

#         This method handles provider lifecycle management, returning:
#         - Singleton provider if it exists
#         - Scoped provider for the agent if it exists
#         - New stateless provider instance if neither exists

#         Args:
#             agent: The agent requesting the provider
#             provider_name: Name of the provider to get

#         Returns:
#             Provider instance or None if not found/created
#         """
#         # Check singleton providers first
#         if provider_name in self._singleton_providers:
#             return self._singleton_providers[provider_name]

#         # Check scoped providers for this agent
#         agent_providers = self._scoped_providers.get(agent.name, {})
#         if provider_name in agent_providers:
#             return agent_providers[provider_name]

#         # Find matching provider config
#         provider_config = next((p for p in agent.providers if p.provider_name == provider_name), None)
#         if not provider_config:
#             logger.warning(f"No provider config found for {provider_name}")
#             return None

#         # Create new stateless provider if needed
#         if provider_config.provider_lifecycle == "stateless":
#             return self._create_provider(provider_config, agent)

#         return None

#     def get_llm_provider(self, agent: Agent) -> BaseLLMProvider | None:
#         """Get the LLM provider for an agent.

#         Args:
#             agent: The agent to get the LLM provider for

#         Returns:
#             LLM provider instance or None if not found
#         """
#         for provider_config in agent.providers:
#             if provider_config._provider_type == "llm":
#                 provider = self.get_provider(agent, provider_config.provider_name)
#                 if isinstance(provider, BaseLLMProvider):
#                     return provider
#         return None


# # Global provider manager instance
# PROVIDER_MANAGER = ProviderManager()
