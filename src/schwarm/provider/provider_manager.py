"""Provider manager for handling provider lifecycle, creation, and events."""

from typing import Any, Optional, TypeVar, cast

from loguru import logger

from schwarm.models.agent import Agent
from schwarm.provider.base.base_event_handle_provider import ModernEventHandleProvider
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.models.base_provider_config import BaseProviderConfig
from schwarm.provider.base.models.provider_scope import ProviderScope
from schwarm.provider.litellm_provider import LiteLLMProvider
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.provider.zep_provider import ZepProvider

P = TypeVar("P", bound=BaseProvider)


class ProviderManager:
    """Manages provider lifecycle, creation, and events.

    This class combines provider factory and registry functionality to provide:
    - Provider lifecycle management based on scope (GLOBAL, SCOPED, EPHEMERAL)
    - Provider creation and type-safe access
    - Event handling and dispatch
    - Agent registration and management
    """

    _instance: Optional["ProviderManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ProviderManager":
        """Create a singleton instance of the provider manager."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the provider manager."""
        if not hasattr(self, "_initialized"):
            self._initialized = True
            self._agents: dict[str, Agent] = {}
            self._provider_registry: dict[str, type[BaseProvider]] = {
                "lite_llm": LiteLLMProvider,
                "zep": ZepProvider,
            }
            self._global_providers: dict[str, BaseProvider] = {}
            self._scoped_providers: dict[str, dict[str, BaseProvider]] = {}

    def register_provider(self, name: str, provider_class: type[BaseProvider]) -> None:
        """Register a new provider type.

        Args:
            name: Name to register the provider under
            provider_class: Provider class to register
        """
        self._provider_registry[name] = provider_class
        logger.debug(f"Registered provider type: {name}")

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the manager.

        Args:
            agent: The agent to register
        """
        self._agents[agent.name] = agent
        logger.debug(f"Registered agent: {agent.name}")

    def get_provider(
        self,
        agent_name: str,
        provider_name: str,
        provider_config: BaseProviderConfig | None = None,
        provider_type: type[P] | None = None,
    ) -> P | None:
        """Get or create a provider instance.

        This method handles provider lifecycle management based on scope:
        - GLOBAL: One instance shared across all agents
        - SCOPED: New instance per agent
        - EPHEMERAL: New instance every time

        Args:
            agent_name: The agent requesting the provider
            provider_name: Name of the provider to get
            provider_config: Optional provider configuration for new instances
            provider_type: Optional type hint for better IDE support

        Returns:
            Provider instance or None if not found/created
        """
        agent = self._agents.get(agent_name)
        if not agent:
            logger.warning(f"No agent found with name {agent_name}")
            return None

        # Check global providers first
        if provider_name in self._global_providers:
            provider = self._global_providers[provider_name]
            return cast(P, provider) if provider_type else cast(P | None, provider)

        # Check scoped providers
        if agent_name in self._scoped_providers:
            provider = self._scoped_providers[agent_name].get(provider_name)
            if provider:
                return cast(P, provider) if provider_type else cast(P | None, provider)

        # Create new provider if config provided
        if provider_config:
            return self._create_provider(provider_config, agent, provider_type)

        logger.warning(f"No provider config found for {provider_name}")
        return None

    def get_llm_provider(self, agent_name: str) -> BaseLLMProvider | None:
        """Get the LLM provider for an agent.

        Args:
            agent_name: Name of the agent to get the LLM provider for

        Returns:
            LLM provider instance or None if not found
        """
        agent = self._agents.get(agent_name)
        if not agent:
            logger.warning(f"No agent found with name {agent_name}")
            return None

        for config in agent.provider_configurations:
            if config.provider_type == "llm":
                provider = self.get_provider(agent_name, config.provider_name, config)
                if isinstance(provider, BaseLLMProvider):
                    return cast(BaseLLMProvider, provider)
        return None

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
                if isinstance(provider, ModernEventHandleProvider):
                    provider_result = provider.handle_event(event_name, **kwargs)
                    if provider_result:
                        result[provider.provider_name] = provider_result
            except Exception as e:
                logger.error(f"Error handling event {event_name} in provider {provider.provider_name}: {e}")
        return result

    def _create_provider(
        self, config: BaseProviderConfig, agent: Agent, provider_type: type[P] | None = None
    ) -> P | None:
        """Create a provider instance based on configuration and scope.

        Args:
            config: Provider configuration
            agent: Agent context
            provider_type: Optional type hint for better IDE support

        Returns:
            Provider instance or None if creation fails
        """
        provider_class = self._provider_registry.get(config.provider_name)
        if not provider_class:
            logger.warning(f"No provider class registered for {config.provider_name}")
            return None

        if provider_type and not issubclass(provider_class, provider_type):
            logger.error(f"Provider {config.provider_name} is not of type {provider_type.__name__}")
            return None

        try:
            provider = self._instantiate_provider(config, agent, provider_class)
            if not provider:
                return None

            # Store provider based on scope
            if config.scope == ProviderScope.GLOBAL:
                self._global_providers[config.provider_name] = provider
            elif config.scope == ProviderScope.SCOPED:
                if agent.name not in self._scoped_providers:
                    self._scoped_providers[agent.name] = {}
                self._scoped_providers[agent.name][config.provider_name] = provider

            return cast(P, provider)

        except Exception as e:
            logger.error(f"Failed to create provider {config.provider_name}: {e}")
            return None

    def _instantiate_provider(
        self, config: BaseProviderConfig, agent: Agent, provider_class: type[BaseProvider]
    ) -> BaseProvider | None:
        """Create a new provider instance.

        Args:
            config: Provider configuration
            agent: Agent context
            provider_class: Provider class to instantiate

        Returns:
            New provider instance or None if creation fails
        """
        if issubclass(provider_class, BaseLLMProvider):
            if isinstance(config, LiteLLMConfig):
                return provider_class(agent.model, config)  # type: ignore
        return provider_class(agent, config)

    def _get_event_providers(self) -> list[BaseProvider]:
        """Get all providers that can handle events.

        Returns:
            List of event-handling providers
        """
        providers: list[BaseProvider] = []
        for agent in self._agents.values():
            for config in agent.provider_configurations:
                provider = self.get_provider(agent.name, config.provider_name, config)
                if provider and hasattr(provider, "handle_event"):
                    providers.append(provider)
        return providers
