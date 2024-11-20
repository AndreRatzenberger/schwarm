"""Core types for the Schwarm framework."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, Optional, TypeVar

from schwarm.core.schwarm import Schwarm
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig

T = TypeVar("T", bound=BaseProvider)


@dataclass
class Result:
    """Result from an agent function execution."""

    value: Any
    context_variables: dict[str, Any] | None = None
    agent: Optional["Agent"] = None


@dataclass
class Agent:
    """An agent with specific capabilities through providers."""

    name: str
    provider_configurations: list[BaseProviderConfig]
    instructions: Callable[[dict[str, Any]], str] | None = None
    functions: list[Callable] = field(default_factory=list)
    _providers: dict[str, BaseProvider] = field(default_factory=dict)

    def get_typed_provider(self, provider_type: type[T]) -> T:
        """Get a provider with proper type safety."""
        for provider in self._providers.values():
            if isinstance(provider, provider_type):
                return provider
        raise ValueError(f"No provider of type {provider_type.__name__} configured")

    def quickstart(
        self,
        input_text: str,
        context_variables: dict[str, Any] | None = None,
        mode: Literal["auto", "interactive"] = "interactive",
    ) -> Result:
        """Quick way to start the agent with minimal configuration.

        This method uses Schwarm's quickstart functionality to run the agent.

        Args:
            input_text: The input text to process
            context_variables: Optional context variables
            mode: Either "auto" or "interactive" mode

        Returns:
            Result containing the response and any updates
        """
        # Create Schwarm instance
        schwarm = Schwarm()
        schwarm.register_agent(self)

        # Run through Schwarm's quickstart
        response = schwarm.quickstart(
            agent=self, input_text=input_text, context_variables=context_variables or {}, mode=mode
        )

        # Convert Response to Result
        return Result(
            value=response.messages[-1].content if response.messages else "",
            context_variables=response.context_variables,
            agent=response.agent,
        )

    def _setup_providers(self) -> None:
        """Initialize all configured providers."""
        for config in self.provider_configurations:
            provider_class = config.get_provider_class()
            provider = provider_class(config)
            provider.set_up()
            self._providers[config.provider_name] = provider
