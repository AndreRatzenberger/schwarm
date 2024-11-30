"""Domain layer implementation of agent behavior."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..context import Context
from ..events import Event, EventType


@dataclass
class AgentState:
    """Internal state of an agent."""
    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    turn_count: int = 0
    last_message_time: Optional[datetime] = None
    token_usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def increment_turn(self) -> None:
        """Increment the turn counter."""
        self.turn_count += 1
        self.last_message_time = datetime.utcnow()

    def add_token_usage(self, count: int, type_: str = "total") -> None:
        """Track token usage."""
        self.token_usage[type_] = self.token_usage.get(type_, 0) + count


class AgentDomain:
    """Core domain logic for agent behavior.
    
    This class encapsulates the complex business logic of agent behavior,
    separated from the presentation layer.
    """
    
    def __init__(self, name: str):
        """Initialize the agent domain.
        
        Args:
            name: The name of the agent
        """
        self.name = name
        self._state = AgentState()
        self._context = Context()
        self._tools: Dict[str, Any] = {}
        self._providers: List[Any] = []
        
    @property
    def state(self) -> AgentState:
        """Get the current agent state."""
        return self._state
        
    async def process_message(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Process an incoming message.
        
        Args:
            content: The message content
            metadata: Optional message metadata
            
        Returns:
            The agent's response
        """
        # Update state
        self._state.increment_turn()
        
        # Process message with providers
        for provider in self._providers:
            try:
                response = await provider.execute(content)
                if response:
                    return response
            except Exception as e:
                # Log error and continue to next provider
                print(f"Provider error: {e}")
                continue
                
        return "No response generated"
        
    async def execute_tool(
        self,
        tool_name: str,
        **kwargs: Any
    ) -> Any:
        """Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
            
        Raises:
            KeyError: If tool not found
        """
        if tool_name not in self._tools:
            raise KeyError(f"Tool '{tool_name}' not found")
            
        tool = self._tools[tool_name]
        return await tool.execute(self._context, **kwargs)
        
    def register_tool(self, name: str, tool: Any) -> None:
        """Register a new tool.
        
        Args:
            name: Tool name
            tool: Tool implementation
        """
        self._tools[name] = tool
        
    def register_provider(self, provider: Any) -> None:
        """Register a new provider.
        
        Args:
            provider: Provider implementation
        """
        self._providers.append(provider)
        
    def update_context(self, key: str, value: Any) -> None:
        """Update the context with new data.
        
        Args:
            key: Context key
            value: Context value
        """
        self._context.set(key, value)
        
    def get_context(self, key: str) -> Optional[Any]:
        """Get a value from context.
        
        Args:
            key: Context key
            
        Returns:
            Context value if found, None otherwise
        """
        return self._context.get(key)
