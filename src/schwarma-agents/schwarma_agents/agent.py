"""Base agent implementation."""

from collections.abc import Callable
from typing import Any

from schwarma_core.context import Context
from schwarma_core.events import Event, EventDispatcher, EventType
from schwarma_core.function import Function
from schwarma_core.provider import Provider


class Agent:
    """Core agent class that orchestrates behavior and manages state.

    An Agent combines functions and providers to perform tasks, maintaining
    state through a context and communicating changes via events.

    Example:
        agent = Agent(
            name="assistant",
            instructions="You are a helpful assistant.",
            functions=[greet_function],
            providers=[llm_provider]
        )
        await agent.initialize()
        result = await agent.execute_function("greet", name="Alice")
    """

    def __init__(
        self,
        name: str,
        instructions: str | Callable[[Context], str] | None = None,
        functions: list[Function] | None = None,
        providers: list[Provider] | None = None,
        context: Context | None = None,
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        """Initialize a new agent.

        Args:
            name: The name of the agent
            instructions: Static string or callable that generates instructions
            functions: List of functions available to the agent
            providers: List of providers available to the agent
            context: Shared context object (creates new if None)
            event_dispatcher: Event dispatcher (creates new if None)
        """
        self.name = name
        self._instructions = instructions
        self._functions: dict[str, Function] = {f.name: f for f in (functions or [])}
        self._providers = providers or []
        self.context = context or Context()
        self._event_dispatcher = event_dispatcher or EventDispatcher()

    async def initialize(self) -> None:
        """Initialize the agent and its components.

        This method initializes all providers and dispatches an initialization event.
        """
        # Initialize all providers
        for provider in self._providers:
            await provider.initialize()

        # Dispatch initialization event
        await self._dispatch_event(
            EventType.AGENT_INITIALIZED,
            {"agent_name": self.name},
        )

    def get_instructions(self) -> str:
        """Get the current instructions for the agent.

        Returns:
            The agent's instructions, either static or dynamically generated
        """
        if callable(self._instructions):
            return self._instructions(self.context)
        return self._instructions or "No instructions provided"

    def add_function(self, function: Function) -> None:
        """Add a function to the agent.

        Args:
            function: The function to add
        """
        self._functions[function.name] = function

    def remove_function(self, function_name: str) -> None:
        """Remove a function from the agent.

        Args:
            function_name: The name of the function to remove
        """
        self._functions.pop(function_name, None)

    def add_provider(self, provider: Provider) -> None:
        """Add a provider to the agent.

        Args:
            provider: The provider to add
        """
        self._providers.append(provider)

    def remove_provider(self, provider: Provider) -> None:
        """Remove a provider from the agent.

        Args:
            provider: The provider to remove
        """
        if provider in self._providers:
            self._providers.remove(provider)

    async def execute_function(self, function_name: str, *args: Any, **kwargs: Any) -> Any:
        """Execute a function by name.

        Args:
            function_name: The name of the function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            The result of the function execution

        Raises:
            KeyError: If the function name is not found
        """
        if function_name not in self._functions:
            raise KeyError(f"Function '{function_name}' not found")

        function = self._functions[function_name]

        # Dispatch before execution event
        await self._dispatch_event(
            EventType.BEFORE_FUNCTION_EXECUTION,
            {
                "function_name": function_name,
                "args": args,
                "kwargs": kwargs,
            },
        )

        try:
            result = await function.execute(*args, **kwargs)

            # Dispatch after execution event
            await self._dispatch_event(
                EventType.AFTER_FUNCTION_EXECUTION,
                {
                    "function_name": function_name,
                    "result": result,
                },
            )

            return result

        except Exception as e:
            # Dispatch error event
            await self._dispatch_event(
                EventType.FUNCTION_ERROR,
                {
                    "function_name": function_name,
                    "error": str(e),
                },
            )
            raise

    async def execute_provider(self, provider: Provider, *args: Any, **kwargs: Any) -> Any:
        """Execute a provider.

        Args:
            provider: The provider to execute
            *args: Positional arguments to pass to the provider
            **kwargs: Keyword arguments to pass to the provider

        Returns:
            The result of the provider execution

        Raises:
            ValueError: If the provider is not registered with this agent
        """
        if provider not in self._providers:
            raise ValueError("Provider not registered with this agent")

        # Dispatch before execution event
        await self._dispatch_event(
            EventType.BEFORE_PROVIDER_EXECUTION,
            {
                "provider": provider.__class__.__name__,
                "args": args,
                "kwargs": kwargs,
            },
        )

        try:
            result = await provider.execute(*args, **kwargs)

            # Dispatch after execution event
            await self._dispatch_event(
                EventType.AFTER_PROVIDER_EXECUTION,
                {
                    "provider": provider.__class__.__name__,
                    "result": result,
                },
            )

            return result

        except Exception as e:
            # Dispatch error event
            await self._dispatch_event(
                EventType.PROVIDER_ERROR,
                {
                    "provider": provider.__class__.__name__,
                    "error": str(e),
                },
            )
            raise

    async def _dispatch_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Dispatch an agent-related event.

        Args:
            event_type: The type of event to dispatch
            data: Event-specific data
        """
        await self._event_dispatcher.dispatch(
            Event(
                type=event_type,
                data=data,
                source=self.name,
            )
        )
