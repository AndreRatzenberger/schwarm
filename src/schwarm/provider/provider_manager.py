"""Manages provider lifecycles and access."""

from typing import Any, Optional, TypeVar

from loguru import logger

from schwarm.events.event_data import Event
from schwarm.events.event_types import EventType
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContext
from schwarm.models.types import Agent
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig, ProviderScope
from schwarm.provider.base.injection import ContextInjection, InjectionTask, InstructionInjection, MessageInjection
from schwarm.provider.litellm_provider import LiteLLMProvider

P = TypeVar("P", bound=BaseProvider)


class ProviderInitError(Exception):
    """Raised when provider initialization fails."""

    pass


class ProviderManager:
    """Manages provider lifecycles and access."""

    _instance: Optional["ProviderManager"] = None

    @staticmethod
    def initialize_provider_system():
        """Initialize the provider system with default providers."""
        manager = ProviderManager()

        # Register default provider types
        manager.register_provider_type("llm", LiteLLMProvider)

        return manager

    def __new__(cls) -> "ProviderManager":
        """Singleton instance creation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the provider manager."""
        if not self._initialized:
            # Stores global provider instances
            self._global_providers: dict[str, BaseProvider] = {}

            # Stores agent-specific provider instances
            # {agent_id: {provider_name: provider_instance}}
            self._agent_providers: dict[str, dict[str, BaseProvider]] = {}

            self._initialized = True

    def _create_provider(self, config: BaseProviderConfig, agent_id: str | None = None) -> BaseProvider:
        """Create a new provider instance."""
        provider_class = config.get_provider_class()
        if not provider_class:
            raise ProviderInitError(f"No implementation found for provider type: {config.provider_type}")

        try:
            provider = provider_class(config)
            provider.initialize()
            return provider
        except Exception as e:
            raise ProviderInitError(f"Failed to initialize provider {config.provider_name}: {e!s}")

    def get_provider_by_class(self, agent_id: str, provider_class: type[P]) -> P:
        """Get a provider instance by its class."""
        for provider in self.get_all_providers(agent_id).values():
            if isinstance(provider, provider_class):
                return provider
        raise ValueError(f"No provider of type {provider_class.__name__} found")

    def get_provider(self, agent_id: str, provider_name: str) -> BaseProvider | None:
        """Get or create a provider instance based on its scope."""
        # Check global providers first
        if provider_name in self._global_providers:
            return self._global_providers[provider_name]

        # Check agent-specific providers
        agent_providers = self._agent_providers.get(agent_id, {})
        if provider_name in agent_providers:
            return agent_providers[provider_name]

        return None

    def get_all_providers(self, agent_id: str) -> dict[str, BaseProvider]:
        """Get all providers for an agent."""
        return self._agent_providers.get(agent_id, {})

    def get_first_llm_provider(self, agent_id: str) -> LiteLLMProvider | None:
        """Get the first LiteLLM provider for an agent."""
        for provider in self._agent_providers.get(agent_id, {}).values():
            if isinstance(provider, LiteLLMProvider):
                return provider
        return

    def initialize_provider(self, agent_id: str, config: BaseProviderConfig) -> BaseProvider:
        """Initialize a provider based on its scope."""
        if not config.enabled:
            raise ProviderInitError(f"Provider {config.provider_name} is disabled")

        # Handle based on scope
        if config.scope == ProviderScope.GLOBAL:
            if config.provider_name not in self._global_providers:
                provider = self._create_provider(config)
                self._global_providers[config.provider_name] = provider
                logger.info(f"Initialized global provider: {config.provider_name}")
            return self._global_providers[config.provider_name]

        elif config.scope == ProviderScope.AGENT:
            if agent_id not in self._agent_providers:
                self._agent_providers[agent_id] = {}
            if config.provider_name not in self._agent_providers[agent_id]:
                provider = self._create_provider(config, agent_id)
                self._agent_providers[agent_id][config.provider_name] = provider
                logger.info(f"Initialized agent provider: {config.provider_name} " f"for agent: {agent_id}")
            return self._agent_providers[agent_id][config.provider_name]

        else:  # EPHEMERAL
            provider = self._create_provider(config, agent_id)
            logger.info(f"Created ephemeral provider: {config.provider_name} " f"for agent: {agent_id}")
            return provider

    def get_event_providers(self, agent_id: str) -> list[BaseEventHandleProvider]:
        """Get all event handling providers for an agent."""
        providers = []

        # Get global event providers
        for provider in self._global_providers.values():
            if isinstance(provider, BaseEventHandleProvider):
                providers.append(provider)

        # Get agent-specific event providers
        agent_providers = self._agent_providers.get(agent_id, {})
        for provider in agent_providers.values():
            if isinstance(provider, BaseEventHandleProvider):
                providers.append(provider)

        return providers

    def trigger_event(self, event_type: EventType, payload: ProviderContext) -> None:
        """Trigger an event across all relevant providers.

        Args:
            event_type: Type of event to trigger
            payload: Event data
            agent_id: ID of the agent triggering the event
            context: Optional context for injection handling
        """
        agent_id = payload.current_agent.name
        event = Event(type=event_type, payload=payload, agent_id=agent_id)

        # Get event providers in priority order
        providers = self.get_event_providers(agent_id)
        providers.sort(key=lambda p: getattr(p, "priority", 0), reverse=True)

        # Track injections to apply
        injections: list[InjectionTask] = []

        # Trigger event on all providers
        for provider in providers:
            try:
                result = provider.handle_event(event)
                if result:
                    injections.append(result)
            except Exception as e:
                logger.error(f"Error in provider {provider.config.provider_name} " f"handling {event_type}: {e}")

        # Apply injections if context is provided
        if injections:
            self._apply_injections(injections, payload)

    def _apply_injections(self, injections: list[InjectionTask], payload: ProviderContext) -> None:
        """Apply injection tasks to the given context."""
        for injection in injections:
            try:
                if injection.target == "instruction":
                    value: InstructionInjection = injection.value  # type: ignore
                    current = payload.current_instruction

                    if value.position == "prefix":  # type: ignore
                        payload.current_instruction = value.content + current  # type: ignore
                    elif value.position == "suffix":  # type: ignore
                        payload.current_instruction = current + value.content  # type: ignore
                    else:  # replace
                        payload.current_instruction = value.content  # type: ignore

                elif injection.target == "message":  # type: ignore
                    value: MessageInjection = injection.value  # type: ignore
                    messages = payload.message_history
                    messages.append(Message(role=value.role, content=value.content))  # type: ignore
                    payload.message_history = messages

                elif injection.target == "context":
                    value: dict[str, Any] = injection.value  # type: ignore
                    value: ContextInjection = injection.value  # type: ignore
                    context_vars = payload.context_variables
                    context_vars[value.key] = value.value  # type: ignore
                    payload.context_variables = context_vars

                elif injection.target == "agent":
                    if isinstance(injection.value, "Agent"):
                        value: Agent = injection.value
                        payload.current_agent = value

            except Exception as e:
                logger.error(f"Error applying injection {injection}: {e}")
