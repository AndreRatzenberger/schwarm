"""Manages provider lifecycles and access."""

import importlib
import inspect
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar

from loguru import logger

from schwarm.events import Event, EventType
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base import BaseProviderConfig
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider

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
            # {provider_id: provider_instance}

            self._providers: dict[str, list[BaseProvider]] = {}

            # Stores registered provider classes and their configs
            # {config_class: provider_class}
            self._config_to_provider_map: dict[type[BaseProviderConfig], type[BaseProvider]] = {}

            self._scan_and_register_providers()
            self._initialized = True

    def register_provider(self, config_class: type[BaseProviderConfig], provider_class: type[BaseProvider]) -> None:
        """Register a provider class and its config class."""
        self._config_to_provider_map[config_class] = provider_class

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
                                        self._config_to_provider_map[config_obj] = obj
                                        logger.debug(
                                            f"Registered provider {obj.__name__} with config {config_obj.__name__}"
                                        )

                    except Exception as e:
                        logger.warning(f"Failed to load module {module_name}: {e!s}")

    def _create_provider(self, config: BaseProviderConfig, scope: str) -> BaseProvider:
        """Create a new provider instance."""
        try:
            provider_class = self._config_to_provider_map.get(type(config))
            if not provider_class:
                raise ProviderInitError(
                    f"No provider implementation found for config type: {config.__class__.__name__}"
                )

            provider = provider_class(config=config)

            return provider
        except (ImportError, ModuleNotFoundError) as e:
            raise ProviderInitError(
                f"Failed to initialize provider for config type: {config.__class__.__name__}: {e!s}"
            )
        except Exception as e:
            raise ProviderInitError(
                f"Failed to initialize provider for config type: {config.__class__.__name__}: {e!s}"
            )

    def get_providers_by_class(self, provider_class: type[P]) -> list[P]:
        """Get a provider instance by its class."""
        logger.debug(f"Provider class: {provider_class}")
        result = []
        for p in self._providers.values():
            for provider in p:
                if isinstance(provider, provider_class):
                    result.append(provider)

        logger.debug(f"Found provider: {len(result)}")
        return result

    def get_provider_to_agent_name_by_class(self, agent_name: str, provider_class: type[P]) -> list[P]:
        """Get a provider instance by its class which would trigger if an agent is triggering an event."""
        logger.debug(f"Looking for provider of type {provider_class.__name__} for agent {agent_name}")
        logger.debug(f"Provider class module: {provider_class.__module__}")
        logger.debug(f"Provider class id: {id(provider_class)}")

        result = []
        for p in self._providers.items():
            scope = p[0]
            for provider in p[1]:
                if isinstance(provider, provider_class) and (scope == "global" or scope == agent_name):
                    logger.debug(f"provider: {type(p).__name__}")
                    logger.debug(f"provider module: {type(p).__module__}")
                    logger.debug(f"scope: {scope}")
                    result.append(provider)

        logger.debug(f"Found provider: {len(result)}")
        return result

    def get_provider_by_id(self, scope: str, provider_id: str) -> BaseProvider | None:
        """Get a provider instance based on its scope."""
        try:
            if scope:
                providers = self._providers.get(scope)
                if providers:
                    for p in providers:
                        if p._provider_id == provider_id:
                            return p
        except KeyError:
            return None

    def get_all_providers_to_scope(self, scope: str) -> list[BaseProvider]:
        """Get all providers for an scope."""
        return self._providers.get(scope, [])

    def get_first_llm_provider(self, scope: str) -> BaseLLMProvider | None:
        """Get the first LiteLLM provider for an agent."""
        for provider in self.get_all_providers_to_scope(scope):
            if isinstance(provider, BaseLLMProvider):
                return provider
        return None

    def create_provider_and_register(self, agent_id: str, config: BaseProviderConfig) -> BaseProvider:
        """Creates a provider instance based on its configuration, and registers it."""
        # Handle based on scope

        if config.scope == "global" or config.scope == "scoped":
            scope = agent_id
            if config.scope == "global":
                scope = "global"

            provider = self._create_provider(config, agent_id)

            if scope in self._providers:
                self._providers[scope].append(provider)
            else:
                self._providers[scope] = [provider]
            logger.info(f"Created global provider: {provider._provider_id}")
            return provider

        else:
            provider = self._create_provider(config, agent_id)
            logger.info(f"Created jit provider: {provider._provider_id} for agent: {agent_id}")
            return provider

    def get_event_providers(self, scope: str) -> list[BaseEventHandleProvider]:
        """Get all event handling providers for an agent."""
        providers = []

        # Get all providers
        all_providers = self.get_all_providers_to_scope(scope)

        # Filter for event providers
        for provider in all_providers:
            if isinstance(provider, BaseEventHandleProvider):
                providers.append(provider)

        # Sort by priority (higher priority first)
        providers.sort(key=lambda p: getattr(p, "priority", 0), reverse=True)
        return providers

    def get_all_provider_cfgs_as_dict(self) -> dict[str, list[BaseProviderConfig]]:
        """Return a dictionary of all instanced providers and their configs."""
        result = {}
        for providers in self._providers.items():
            result[providers[0]] = [provider.config for provider in providers[1]]

        return result

    def trigger_event(self, event_type: EventType, payload: ProviderContext) -> list[ProviderContext]:
        """Trigger an event across all relevant providers."""
        agent_id = payload.current_agent.name
        event = Event(type=event_type, payload=payload, agent_id=agent_id, datetime=datetime.now().isoformat())
        # Get event providers in priority order
        providers = self.get_event_providers(agent_id)
        providers.extend(self.get_event_providers("global"))

        result = []
        for provider in providers:
            event_result = provider.handle_event(event)
            result.append(event_result)

        return result
