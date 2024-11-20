"""Defines the Agent class for managing AI agents and their providers."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from loguru import logger
from pydantic import BaseModel, Field, PrivateAttr

if TYPE_CHECKING:
    from schwarm.models.types import Result
    from schwarm.provider.base.base_llm_provider import BaseLLMProvider
    from schwarm.provider.base.base_provider import BaseProvider
    from schwarm.provider.models.base_provider_config import BaseProviderConfig
    from schwarm.provider.provider_factory import ProviderFactory

# Type alias for agent functions that can return various types
AgentFunction = Callable[..., "str | Agent | dict[str, Any] | Result"]


class Agent(BaseModel):
    """Represents an AI agent with specific capabilities and configuration.

    Attributes:
        name: The name identifier for the agent
        model: The OpenAI model to use for this agent
        instructions: Static or dynamic instructions for the agent's behavior
        functions: List of callable functions available to the agent
        tool_choice: Specific tool selection strategy
        parallel_tool_calls: Whether multiple tools can be called simultaneously
        provider_configurations: List of provider configurations
    """

    name: str = Field(default="Agent", description="Identifier name for the agent")
    model: str = Field(default="gpt-4", description="OpenAI model identifier to use for this agent")
    description: str = Field(default="", description="Description of the agent")
    instructions: str | Callable[..., str] = Field(
        default="You are a helpful agent.",
        description="Static string or callable returning agent instructions",
    )
    functions: list[AgentFunction] = Field(default_factory=list, description="List of functions available to the agent")
    tool_choice: Literal["none", "auto", "required"] = Field(
        default="required",
        description="Specific tool selection strategy. none = no tools get called, auto = llm decides if generating a text or calling a tool, required = tools are forced",
    )
    parallel_tool_calls: bool = Field(default=False, description="Whether multiple tools can be called in parallel")
    provider_configurations: list["BaseProviderConfig"] = Field(
        default_factory=list, description="List of provider configurations"
    )

    # Private attributes for provider management
    _provider_factory: "ProviderFactory" = PrivateAttr(
        default_factory=lambda: __import__(
            "schwarm.provider.provider_factory"
        ).provider.provider_factory.ProviderFactory()
    )
    _singleton_providers: dict[str, "BaseProvider"] = PrivateAttr(default_factory=dict)
    _scoped_providers: dict[str, "BaseProvider"] = PrivateAttr(default_factory=dict)

    def initialize_providers(self) -> None:
        """Initialize all providers for this agent.

        This method handles provider lifecycle management, ensuring providers
        are created and initialized according to their lifecycle configuration.
        """
        logger.info(f"Initializing providers for agent {self.name}")

        for provider_config in self.provider_configurations:
            try:
                if provider_config.provider_lifecycle == "singleton":
                    self._add_singleton_provider(provider_config)
                elif provider_config.provider_lifecycle == "scoped":
                    self._add_scoped_provider(provider_config)
                elif provider_config.provider_lifecycle == "stateless":
                    # Stateless providers are created on-demand
                    pass
                else:
                    logger.warning(f"Unknown provider lifecycle: {provider_config.provider_lifecycle}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {provider_config.provider_name}: {e}")

    def _add_singleton_provider(self, config: "BaseProviderConfig") -> None:
        """Add a singleton provider if it doesn't already exist."""
        if config.provider_name not in self._singleton_providers:
            # Create provider with explicit type cast to avoid self-reference issues
            provider = self._provider_factory.create_provider(config, Agent.model_validate(self.model_dump()))
            if provider:
                provider.initialize()
                self._singleton_providers[config.provider_name] = provider
                logger.info(f"Created singleton provider: {config.provider_name}")

    def _add_scoped_provider(self, config: "BaseProviderConfig") -> None:
        """Add a scoped provider for this agent."""
        if config.provider_name not in self._scoped_providers:
            # Create provider with explicit type cast to avoid self-reference issues
            provider = self._provider_factory.create_provider(config, Agent.model_validate(self.model_dump()))
            if provider:
                provider.initialize()
                self._scoped_providers[config.provider_name] = provider
                logger.info(f"Created scoped provider: {config.provider_name}")

    def get_provider(self, provider_name: str) -> "BaseProvider | None":
        """Get a provider instance.

        This method handles provider lifecycle management, returning:
        - Singleton provider if it exists
        - Scoped provider if it exists
        - New stateless provider instance if neither exists

        Args:
            provider_name: Name of the provider to get

        Returns:
            Provider instance or None if not found/created
        """
        # Check singleton providers first
        if provider_name in self._singleton_providers:
            return self._singleton_providers[provider_name]

        # Check scoped providers
        if provider_name in self._scoped_providers:
            return self._scoped_providers[provider_name]

        # Find matching provider config
        provider_config = next((p for p in self.provider_configurations if p.provider_name == provider_name), None)
        if not provider_config:
            logger.warning(f"No provider config found for {provider_name}")
            return None

        # Create new stateless provider if needed
        if provider_config.provider_lifecycle == "stateless":
            # Create provider with explicit type cast to avoid self-reference issues
            return self._provider_factory.create_provider(provider_config, Agent.model_validate(self.model_dump()))

        return None

    def get_llm_provider(self) -> "BaseLLMProvider | None":
        """Get the LLM provider for this agent.

        Returns:
            LLM provider instance or None if not found
        """
        for provider_config in self.provider_configurations:
            if provider_config.provider_type == "llm":
                provider = self.get_provider(provider_config.provider_name)
                if isinstance(provider, BaseLLMProvider):
                    return provider
        return None
