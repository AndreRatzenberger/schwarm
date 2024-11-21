"""Manages provider lifecycles and access."""

import importlib
import inspect
import os
from pathlib import Path
from typing import Optional, TypeVar

from loguru import logger

from schwarm.events.event_data import Event
from schwarm.events.event_types import EventType
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base import BaseProviderConfig
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.litellm_provider import LiteLLMProvider

P = TypeVar("P", bound=BaseProvider)


class ProviderInitError(Exception):
    """Raised when provider initialization fails."""

    pass


class ProviderManager:
    """Manages provider lifecycles and access."""

    _instance: Optional["ProviderManager"] = None

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

            # Stores registered provider classes and their configs
            # {config_class: provider_class}
            self._registered_providers: dict[type[BaseProviderConfig], type[BaseProvider]] = {}

            self._scan_and_register_providers()
            self._initialized = True

    def register_provider(self, config_class: type[BaseProviderConfig], provider_class: type[BaseProvider]) -> None:
        """Register a provider class and its config class."""
        self._registered_providers[config_class] = provider_class

    def _scan_and_register_providers(self) -> None:
        """Scan the project for BaseProvider and BaseProviderConfig implementations."""
        src_path = Path(__file__).parent.parent

        for root, _, files in os.walk(src_path):
            for file in files:
                if file.endswith(".py"):
                    module_path = os.path.join(root, file)
                    relative_path = os.path.relpath(module_path, src_path.parent)
                    module_name = os.path.splitext(relative_path)[0].replace(os.sep, ".")

                    try:
                        module = importlib.import_module(module_name)

                        # Get all classes defined in the module
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            # Check if it's a provider class
                            if issubclass(obj, BaseProvider) and obj != BaseProvider:
                                # Find corresponding config class
                                for config_name, config_obj in inspect.getmembers(module, inspect.isclass):
                                    if issubclass(config_obj, BaseProviderConfig) and config_obj != BaseProviderConfig:
                                        # Register the provider and config pair
                                        self._registered_providers[config_obj] = obj
                                        logger.debug(
                                            f"Registered provider {obj.__name__} with config {config_obj.__name__}"
                                        )

                    except Exception as e:
                        logger.warning(f"Failed to load module {module_name}: {e!s}")

    def _create_provider(self, config: BaseProviderConfig, agent_id: str | None = None) -> BaseProvider:
        """Create a new provider instance."""
        try:
            provider_class = self._registered_providers.get(type(config))
            if not provider_class:
                raise ProviderInitError(f"No implementation found for provider type: {config.provider_type}")

            provider = provider_class(config)
            return provider
        except (ImportError, ModuleNotFoundError) as e:
            raise ProviderInitError(f"Failed to initialize provider {config.provider_name}: {e!s}")
        except Exception as e:
            raise ProviderInitError(f"Failed to initialize provider {config.provider_name}: {e!s}")

    def get_provider_by_class(self, agent_id: str, provider_class: type[P]) -> P:
        """Get a provider instance by its class."""
        logger.debug(f"Looking for provider of type {provider_class.__name__} for agent {agent_id}")
        logger.debug(f"Provider class module: {provider_class.__module__}")
        logger.debug(f"Provider class id: {id(provider_class)}")

        # Check global providers first
        for provider in self._global_providers.values():
            provider_type = type(provider)
            logger.debug(f"Checking global provider: {provider_type.__name__}")
            logger.debug(f"Global provider module: {provider_type.__module__}")
            logger.debug(f"Global provider class id: {id(provider_type)}")
            if isinstance(provider, provider_class):
                return provider

        # Check agent-specific providers
        agent_providers = self._agent_providers.get(agent_id, {})
        logger.debug(f"Found {len(agent_providers)} agent-specific providers")
        for provider in agent_providers.values():
            provider_type = type(provider)
            logger.debug(f"Checking agent provider: {provider_type.__name__}")
            logger.debug(f"Agent provider module: {provider_type.__module__}")
            logger.debug(f"Agent provider class id: {id(provider_type)}")
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
        providers = {}
        # Include global providers
        providers.update(self._global_providers)
        # Include agent-specific providers
        providers.update(self._agent_providers.get(agent_id, {}))
        return providers

    def get_first_llm_provider(self, agent_id: str) -> LiteLLMProvider | None:
        """Get the first LiteLLM provider for an agent."""
        for provider in self.get_all_providers(agent_id).values():
            if isinstance(provider, LiteLLMProvider):
                return provider
        return None

    def initialize_provider(self, agent_id: str, config: BaseProviderConfig) -> BaseProvider:
        """Initialize a provider based on its scope."""
        if not config.enabled:
            raise ProviderInitError(f"Provider {config.provider_name} is disabled")

        # Handle based on scope
        if config.scope == "singleton":
            if config.provider_name not in self._global_providers:
                provider = self._create_provider(config)
                self._global_providers[config.provider_name] = provider
                logger.info(f"Initialized singleton provider: {config.provider_name}")
            return self._global_providers[config.provider_name]

        elif config.scope == "scoped":
            if agent_id not in self._agent_providers:
                self._agent_providers[agent_id] = {}
            if config.provider_name not in self._agent_providers[agent_id]:
                provider = self._create_provider(config, agent_id)
                self._agent_providers[agent_id][config.provider_name] = provider
                logger.info(f"Initialized scoped provider: {config.provider_name} for agent: {agent_id}")
            return self._agent_providers[agent_id][config.provider_name]

        else:  # EPHEMERAL
            provider = self._create_provider(config, agent_id)
            logger.info(f"Created jit provider: {config.provider_name} for agent: {agent_id}")
            return provider

    def get_event_providers(self, agent_id: str) -> list[BaseEventHandleProvider]:
        """Get all event handling providers for an agent."""
        providers = []

        # Get all providers
        all_providers = self.get_all_providers(agent_id)

        # Filter for event providers
        for provider in all_providers.values():
            if isinstance(provider, BaseEventHandleProvider):
                providers.append(provider)

        # Sort by priority (higher priority first)
        providers.sort(key=lambda p: getattr(p, "priority", 0), reverse=True)
        return providers

    def get_all_providers_as_dict(self) -> dict[str, list[BaseProviderConfig]]:
        """Return a dictionary of all instanced providers and their configs."""
        result = {"global": [provider.config for provider in self._global_providers.values()]}

        # Add agent-specific providers
        for agent_id, providers in self._agent_providers.items():
            result[agent_id] = [provider.config for provider in providers.values()]

        return result

    def trigger_event(self, event_type: EventType, payload: ProviderContext) -> None:
        """Trigger an event across all relevant providers."""
        agent_id = payload.current_agent.name
        event = Event(type=event_type, payload=payload, agent_id=agent_id)

        # Get event providers in priority order
        providers = self.get_event_providers(agent_id)
