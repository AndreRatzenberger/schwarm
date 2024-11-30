"""Agent builder module providing a fluent API for agent construction."""

from typing import Any, Callable, List, Optional, Union

from schwarm.context.context import Context
from schwarm.events.events import EventDispatcher, EventType, EventListener
from schwarm.functions.function import Function
from schwarm.providers.provider import Provider
from schwarm.agents.cli import CLIFunction, Parameter
from schwarm.providers.cli_llm_provider import CLILLMProvider

from .agent import Agent


class AgentBuilder:
    """Builder class providing a fluent interface for constructing agents.
    
    The AgentBuilder allows for step-by-step configuration of an agent
    using method chaining, making agent creation more readable and maintainable.
    
    Example:
        agent = (
            AgentBuilder("AssistantAgent")
            .with_instructions("You are a helpful assistant.")
            .with_function(greet_function)
            .with_cli_function(
                name="image-gen",
                implementation=generate_image,
                description="Generate images from text",
                parameters=[
                    Parameter("-p", "prompt text", required=True),
                    Parameter("--style", choices=["realistic", "anime"])
                ]
            )
            .with_provider(llm_provider)
            .with_event_listener(
                EventType.AFTER_FUNCTION_EXECUTION,
                log_execution
            )
            .build()
        )
    """
    
    def __init__(self, name: str) -> None:
        """Initialize a new agent builder.
        
        Args:
            name: The name of the agent to build
        """
        self._name = name
        self._instructions: Optional[Union[str, Callable[[Context], str]]] = None
        self._functions: List[Function] = []
        self._providers: List[Provider] = []
        self._context: Optional[Context] = None
        self._event_dispatcher: Optional[EventDispatcher] = None
        self._event_listeners: List[tuple[EventType, EventListener]] = [] 
        
    def with_instructions(
        self,
        instructions: Union[str, Callable[[Context], str]]
    ) -> 'AgentBuilder':
        """Set the agent's instructions.
        
        Args:
            instructions: Static string or callable that generates instructions
            
        Returns:
            self for method chaining
        """
        self._instructions = instructions
        return self
        
    def with_function(self, function: Function) -> 'AgentBuilder':
        """Add a function to the agent.
        
        Args:
            function: The function to add
            
        Returns:
            self for method chaining
        """
        self._functions.append(function)
        return self
        
    def with_functions(self, functions: List[Function]) -> 'AgentBuilder':
        """Add multiple functions to the agent.
        
        Args:
            functions: List of functions to add
            
        Returns:
            self for method chaining
        """
        self._functions.extend(functions)
        return self
        
    def with_cli_function(
        self,
        name: str,
        implementation: Callable[..., Any],
        description: str,
        parameters: List[Parameter]
    ) -> 'AgentBuilder':
        """Add a CLI-style function to the agent.
        
        This is a convenience method that creates and adds a CLIFunction
        with the specified parameters.
        
        Args:
            name: The name of the function
            implementation: The callable that implements the function
            description: Description of what the function does
            parameters: List of CLI-style parameters
            
        Returns:
            self for method chaining
            
        Example:
            builder.with_cli_function(
                name="image-gen",
                implementation=generate_image,
                description="Generate images from text",
                parameters=[
                    Parameter("-p", "prompt text", required=True),
                    Parameter("--style", choices=["realistic", "anime"])
                ]
            )
        """
        cli_function = CLIFunction(
            name=name,
            implementation=implementation,
            description=description,
            parameters=parameters
        )
        return self.with_function(cli_function)
        
    def with_cli_functions(
        self,
        functions: List[tuple[str, Callable[..., Any], str, List[Parameter]]]
    ) -> 'AgentBuilder':
        """Add multiple CLI-style functions to the agent.
        
        Args:
            functions: List of tuples containing CLI function parameters
                Each tuple should contain:
                (name, implementation, description, parameters)
            
        Returns:
            self for method chaining
        """
        for name, impl, desc, params in functions:
            self.with_cli_function(name, impl, desc, params)
        return self
        
    def with_provider(self, provider: Provider) -> 'AgentBuilder':
        """Add a provider to the agent.
        
        Args:
            provider: The provider to add
            
        Returns:
            self for method chaining
        """
        self._providers.append(provider)
        return self
        
    def with_providers(self, providers: List[Provider]) -> 'AgentBuilder':
        """Add multiple providers to the agent.
        
        Args:
            providers: List of providers to add
            
        Returns:
            self for method chaining
        """
        self._providers.extend(providers)
        return self
        
    def with_context(self, context: Context) -> 'AgentBuilder':
        """Set the agent's context.
        
        Args:
            context: The context to use
            
        Returns:
            self for method chaining
        """
        self._context = context
        return self
        
    def with_event_dispatcher(self, dispatcher: EventDispatcher) -> 'AgentBuilder':
        """Set the agent's event dispatcher.
        
        Args:
            dispatcher: The event dispatcher to use
            
        Returns:
            self for method chaining
        """
        self._event_dispatcher = dispatcher
        return self
        
    def with_event_listener(
        self,
        event_type: EventType,
        listener: EventListener
    ) -> 'AgentBuilder':
        """Add an event listener to the agent.
        
        Args:
            event_type: The type of event to listen for
            listener: The callback function to execute when the event occurs
            
        Returns:
            self for method chaining
        """
        self._event_listeners.append((event_type, listener))
        return self
        
    def build(self) -> Agent:
        """Build and return the configured agent.
        
        Returns:
            The constructed Agent instance with all configured components
            
        Note:
            If no event dispatcher was set, a new one will be created.
            Event listeners will be registered with the dispatcher.
            If CLI functions are used without a CLILLMProvider, one will
            be added automatically.
        """
        # Create or use provided event dispatcher
        event_dispatcher = self._event_dispatcher or EventDispatcher()
        
        # Register all event listeners
        for event_type, listener in self._event_listeners:
            event_dispatcher.add_listener(event_type, listener)
            
        # Check if we have CLI functions but no CLILLMProvider
        has_cli_functions = any(
            isinstance(f, CLIFunction) for f in self._functions
        )
        has_cli_provider = any(
            isinstance(p, CLILLMProvider) for p in self._providers
        )
        
        # Add CLILLMProvider if needed
        if has_cli_functions and not has_cli_provider:
            self._providers.append(CLILLMProvider(
                model="gpt-3.5-turbo",
                temperature=0.7
            ))
            
        # Create the agent with all configured components
        return Agent(
            name=self._name,
            instructions=self._instructions,
            functions=self._functions,
            providers=self._providers,
            context=self._context,
            event_dispatcher=event_dispatcher,
        )
