"""Manages provider lifecycles and access."""

import importlib
import inspect
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, TypeVar

from loguru import logger

from schwarm.events.event import Event
from schwarm.models.event import EventType
from schwarm.models.provider_context import ProviderContextModel
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.base.base_llm_provider import BaseLLMProvider, BaseLLMProviderConfig
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.telemetry.telemetry_manager import TelemetryManager

P = TypeVar("P", bound=BaseProvider)


class ProviderInitError(Exception):
    """Raised when provider initialization fails.

    This exception is raised when there is an error during the initialization
    of a provider, such as when no provider implementation is found for a
    given configuration type.
    """

    pass


class ProviderManager:
    """Manages provider lifecycles and access.

    This class implements the Singleton pattern and manages the lifecycle of all providers
    in the system. It handles provider registration, initialization, and access control.
    It maintains separate provider instances for different scopes (global and agent-specific)
    and provides methods to interact with these providers.

    Attributes:
        _instance (Optional[ProviderManager]): Singleton instance of the manager
        _providers (dict[str, list[BaseProvider]]): Dictionary mapping scopes to provider lists
        _config_to_provider_map (dict[type[BaseProviderConfig], type[BaseProvider]]): Maps config classes to provider classes
        tracer: OpenTelemetry tracer instance for distributed tracing
    """

    _instance: Optional["ProviderManager"] = None

    @staticmethod
    def get_provider(name: str) -> BaseProvider | None:
        """Get a provider instance by its ID within a given scope."""
        if ProviderManager._instance is None:
            return None
        else:
            return ProviderManager(None).get_provider_by_name(name)

    def __new__(cls, telemetry_manager: TelemetryManager | None) -> "ProviderManager":
        """Create or return the singleton instance of ProviderManager.

        Returns:
            ProviderManager: The singleton instance of the provider manager.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, telemetry_manager: TelemetryManager | None):
        """Initialize the provider manager.

        Sets up the provider storage, OpenTelemetry tracing, and scans for available
        providers if not already initialized. This method is safe to call multiple
        times due to the singleton pattern implementation.
        """
        if not self._initialized:
            # Stores global provider instances
            # {provider_id: provider_instance}

            self._providers: list[BaseProvider] = []
            self._global_break: bool = False
            self.breakpoint: dict[EventType, bool] = {
                EventType.START: False,
                EventType.HANDOFF: False,
                EventType.INSTRUCT: False,
                EventType.MESSAGE_COMPLETION: False,
                EventType.POST_MESSAGE_COMPLETION: False,
                EventType.START_TURN: False,
                EventType.TOOL_EXECUTION: False,
                EventType.POST_TOOL_EXECUTION: False,
            }
            self.breakpoint_counter: int = 0
            self.wait_for_user_input: bool = False
            self.last_user_input: str = ""
            self.is_streaming: bool = False
            self.chunk = ""

            # Stores registered provider classes and their configs
            # {config_class: provider_class}
            self._config_to_provider_map: dict[type[BaseProviderConfig], type[BaseProvider]] = {}
            self._scan_and_register_providers()
            self.telemetry_manager = telemetry_manager
            self._initialized = True

    def toggle_breakpoint(self, event_type: str) -> bool:
        """Toggle the global break state."""
        event = EventType(event_type)
        self.breakpoint[event] = not self.breakpoint[event]
        return self.breakpoint[event]

    def wait_for_frontend(self, wait_for_user_input: bool = False) -> None:
        """Wait for the frontend to signal a global break."""
        if self.breakpoint_counter != 0:
            return
        self._global_break = True
        self.wait_for_user_input = wait_for_user_input
        logger.info(f"Waiting for frontend... wait_for_user_input: {wait_for_user_input}")
        while self._global_break:
            pass

    def trigger_event(
        self, event: Event, context: ProviderContextModel, provider_list: list[str] | None = None
    ) -> list[ProviderContextModel]:
        """Trigger an event across all relevant providers.

        Args:
            event (Event): The event to trigger across providers.

        Returns:
            list[ProviderContext]: List of provider contexts containing the results
                                 of processing the event.

        Note:
            This method handles both agent-specific and global scope providers,
            catching and logging any errors that occur during event processing.
        """
        if provider_list:
            providers = [self.get_provider_by_name(provider) for provider in provider_list]
        else:
            providers = self.get_event_providers()

        event.timestamp = datetime.now().isoformat()

        results = []
        for provider in providers:
            if not isinstance(provider, BaseEventHandleProvider):
                continue
            try:
                result = provider.handle_event(event, context)
                event.context = result
                if result:
                    event.provider_id = provider.provider_name
                    if self.telemetry_manager:
                        self.telemetry_manager.send_provider_trace(event)
                results.append(result)
            except Exception as e:
                logger.error(f"Error triggering event for provider {type(provider).__name__}: {e}")

        return results

    def register_provider(self, config_class: type[BaseProviderConfig], provider_class: type[BaseProvider]) -> None:
        """Register a provider class and its config class.

        Args:
            config_class (type[BaseProviderConfig]): The configuration class for the provider
            provider_class (type[BaseProvider]): The provider class to register

        Note:
            This method maps configuration classes to their corresponding provider
            implementations in the internal registry.
        """
        self._config_to_provider_map[config_class] = provider_class
        logger.info(f"Registered provider {provider_class.__name__} with config {config_class.__name__}")

    def _scan_and_register_providers(self) -> None:
        """Scan the project for BaseProvider and BaseProviderConfig implementations.

        This method walks through the project directory structure to discover and
        automatically register all provider implementations and their corresponding
        configuration classes.

        Note:
            Skips base classes and handles import errors gracefully by logging warnings.
        """
        src_path = Path(__file__).parent.parent

        for root, _, files in os.walk(src_path):
            for file in files:
                if file.endswith("_provider.py"):
                    module_path = os.path.join(root, file)
                    relative_path = os.path.relpath(module_path, src_path.parent)
                    module_name = os.path.splitext(relative_path)[0].replace(os.sep, ".")

                    try:
                        module = importlib.import_module(module_name)

                        # Register all BaseProvider and BaseProviderConfig pairs
                        for name, obj in inspect.getmembers(module, inspect.isclass):
                            if issubclass(obj, BaseProvider) and obj not in {
                                BaseProvider,
                                BaseLLMProvider,
                                BaseEventHandleProvider,
                            }:
                                for config_name, config_obj in inspect.getmembers(module, inspect.isclass):
                                    if issubclass(config_obj, BaseProviderConfig) and config_obj not in {
                                        BaseProviderConfig,
                                        BaseLLMProviderConfig,
                                        BaseEventHandleProviderConfig,
                                    }:
                                        self.register_provider(config_obj, obj)

                    except Exception as e:
                        logger.warning(f"Failed to load module {module_name}: {e}")

    def create_provider(self, agent_id: str, config: BaseProviderConfig) -> BaseProvider:
        """Creates a provider instance based on its configuration and registers it.

        Args:
            agent_id (str): The ID of the agent to associate with the provider
            config (BaseProviderConfig): Configuration for the provider

        Returns:
            BaseProvider: The newly created and registered provider instance

        Note:
            The provider is registered in either the global scope or agent-specific
            scope based on the configuration.
        """
        provider_class = self._config_to_provider_map.get(type(config))
        if not provider_class:
            raise ProviderInitError(f"No provider implementation found for config type: {type(config).__name__}")

        for p in self._providers:
            if p.provider_name == config.provider_name:
                logger.debug(f"Provider {p.provider_name} already exists")
                return p
            if p.provider_name == provider_class.__name__.lower():
                logger.debug(f"Provider {p.provider_name} already exists")
                return p

        provider = provider_class(config)

        self._providers.append(provider)
        logger.debug(f"Created {type(provider).__name__} with ID {provider.provider_name}")
        return provider

    def get_event_providers(self) -> list[BaseEventHandleProvider]:
        """Get all event-handling providers for a given scope.

        Args:
            scope (str): The scope to retrieve providers for ("global" or agent ID)

        Returns:
            list[BaseEventHandleProvider]: List of event handling providers sorted by priority

        Note:
            Providers are sorted by priority in descending order, with default
            priority of 0 for providers without explicit priority.
        """
        providers = [provider for provider in self._providers if isinstance(provider, BaseEventHandleProvider)]
        # Sort by priority (default is 0 if priority is not set)
        providers.sort(key=lambda p: getattr(p, "priority", 0), reverse=True)
        return providers

    def get_providers_by_class(self, provider_class: type[P]) -> list[P]:
        """Get all provider instances of a specific class.

        Args:
            provider_class (type[P]): The class of providers to retrieve

        Returns:
            list[P]: List of all providers matching the specified class
        """
        return [provider for provider in self._providers if isinstance(provider, provider_class)]

    def get_provider_by_name(self, provider_name: str) -> BaseProvider | None:
        """Get a provider instance by its ID within a given scope.

        Args:
            scope (str): The scope to search in ("global" or agent ID)
            provider_id (str): The ID of the provider to retrieve

        Returns:
            Optional[BaseProvider]: The provider instance if found, None otherwise
        """
        for provider in self._providers:
            if provider.provider_name == provider_name:
                return provider
        return None

    def get_all_provider_cfgs_as_dict(self) -> list[BaseProviderConfig]:
        """Return a dictionary of all instantiated providers and their configs.

        Returns:
            dict[str, list[BaseProviderConfig]]: Dictionary mapping scopes to lists
            of provider configurations
        """
        return [provider.config for provider in self._providers]

    def get_provider_to_class(self, provider_class: type[P]) -> list[P]:
        """Get a provider instance by its class which would trigger if an agent is triggering an event.

        Args:
            agent_name (str): The name of the agent.
            provider_class (type[P]): The class of the provider to look for.

        Returns:
            list[P]: A list of providers matching the class and agent criteria.

        Note:
            This method checks both global scope and agent-specific scope for matching providers.
        """
        logger.debug(f"Looking for providers of type {provider_class.__name__}")

        result = []
        for provider in self._providers:
            if isinstance(provider, provider_class):
                result.append(provider)

        logger.debug(f"Total providers found: {len(result)}")
        return result

    def get_first_llm_provider(self, scope: str) -> BaseLLMProvider | None:
        """Get the first LLM provider for a given scope.

        Args:
            scope (str): The scope to search (e.g., "global" or agent name).

        Returns:
            Optional[BaseLLMProvider]: The first found LLM provider or None if no match is found.

        Note:
            This is a convenience method for getting the first available LLM provider
            in cases where only one is needed.
        """
        for provider in self._providers:
            if isinstance(provider, BaseLLMProvider):
                return provider
        return None
