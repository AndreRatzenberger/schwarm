"""Agent builder module providing fluent API for agent creation."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from schwarm.agent import Agent
from schwarm.context import Context
from schwarm.function import Function
from schwarm.provider import Provider


@dataclass
class AgentConfig:
    """Configuration for agent creation."""
    name: str
    instructions: Optional[str | Callable[[Context], str]] = None
    functions: List[Function] = field(default_factory=list)
    providers: List[Provider] = field(default_factory=list)
    memory_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentBuilder:
    """Fluent builder for agent creation.
    
    Example:
        agent = (AgentBuilder()
            .name("assistant")
            .with_instructions("You are a helpful assistant")
            .with_memory(memory_config)
            .with_tool(summarize_tool)
            .with_provider(llm_provider)
            .build())
    """
    
    def __init__(self):
        """Initialize an empty agent builder."""
        self._config = AgentConfig(
            name="",
            instructions=None,
            functions=[],
            providers=[],
            memory_config=None,
            metadata={}
        )
        
    def name(self, name: str) -> 'AgentBuilder':
        """Set the agent's name.
        
        Args:
            name: The name for the agent
            
        Returns:
            The builder instance for chaining
        """
        self._config.name = name
        return self
        
    def with_instructions(
        self,
        instructions: str | Callable[[Context], str]
    ) -> 'AgentBuilder':
        """Set the agent's instructions.
        
        Args:
            instructions: Static string or callable that generates instructions
            
        Returns:
            The builder instance for chaining
        """
        self._config.instructions = instructions
        return self
        
    def with_tool(self, function: Function) -> 'AgentBuilder':
        """Add a tool (function) to the agent.
        
        Args:
            function: The function to add
            
        Returns:
            The builder instance for chaining
        """
        self._config.functions.append(function)
        return self
        
    def with_provider(self, provider: Provider) -> 'AgentBuilder':
        """Add a provider to the agent.
        
        Args:
            provider: The provider to add
            
        Returns:
            The builder instance for chaining
        """
        self._config.providers.append(provider)
        return self
        
    def with_memory(self, config: Dict[str, Any]) -> 'AgentBuilder':
        """Configure the agent's memory system.
        
        Args:
            config: Memory configuration parameters
            
        Returns:
            The builder instance for chaining
        """
        self._config.memory_config = config
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'AgentBuilder':
        """Add metadata to the agent configuration.
        
        Args:
            metadata: Key-value pairs of metadata
            
        Returns:
            The builder instance for chaining
        """
        self._config.metadata.update(metadata)
        return self
        
    def build(self) -> Agent:
        """Build and return the configured agent.
        
        Returns:
            A new Agent instance configured with the builder's settings
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not self._config.name:
            raise ValueError("Agent name is required")
            
        return Agent(
            name=self._config.name,
            instructions=self._config.instructions,
            functions=self._config.functions,
            providers=self._config.providers,
            context=Context()  # TODO: Add memory configuration
        )
