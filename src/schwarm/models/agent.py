"""Agent model definition."""

from collections.abc import Callable
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field, PrivateAttr

from schwarm.models.result import Result
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig
from schwarm.provider.provider_manager import ProviderManager

T = TypeVar("T", bound=BaseProvider)


class Agent(BaseModel):
    """An agent with specific capabilities through providers."""

    name: str = Field(default="Agent", description="Identifier name for the agent")
    model: str = Field(default="gpt-4", description="OpenAI model identifier to use for this agent")
    description: str = Field(default="", description="Description of the agent")
    instructions: str | Callable[..., str] = Field(
        default="You are a helpful agent.",
        description="Static string or callable returning agent instructions",
    )
    functions: list[Callable[..., Any]] = Field(
        default_factory=list, description="List of functions available to the agent"
    )
    tool_choice: Literal["none", "auto", "required"] = Field(
        default="required",
        description="Specific tool selection strategy. none = no tools get called, auto = llm decides if generating a text or calling a tool, required = tools are forced",
    )
    parallel_tool_calls: bool = Field(default=False, description="Whether multiple tools can be called in parallel")
    provider_configurations: list[BaseProviderConfig] = Field(
        default_factory=list, description="List of provider configurations"
    )
    _provider_manager: ProviderManager = PrivateAttr(
        default_factory=lambda: __import__("schwarm.provider.provider_manager").ProviderManager()
    )

    def get_typed_provider(self, provider_type: type[T]) -> T:
        """Get a provider with proper type safety."""
        provider = self._provider_manager.get_provider_by_class(self.name, provider_type)
        if provider:
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
        # Import here to avoid circular dependency
        from schwarm.core.schwarm import Schwarm

        # Create Schwarm instance
        schwarm = Schwarm()
        schwarm.register_agent(self)

        # Run through Schwarm's quickstart
        response = schwarm.quickstart(
            agent=self, input_text=input_text, context_variables=context_variables or {}, mode=mode
        )

        # Convert Response to Result
        return Result(
            value=response.messages[-1].content
            if response and response.messages and response.messages[-1].content
            else "",
            agent=response.agent,
            context_variables=response.context_variables,
        )

    def _setup_providers(self) -> None:
        """Initialize all configured providers."""
        for config in self.provider_configurations:
            self._provider_manager.initialize_provider(self.name, config)
            provider_class = config.get_provider_class()
            provider = provider_class(config)
            provider.set_up()
