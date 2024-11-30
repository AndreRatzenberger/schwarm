"""Fluent API for tool management."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TypeVar

from ..context import Context

T = TypeVar('T')


@dataclass
class ToolMetadata:
    """Metadata for tool registration."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]
    return_type: type
    tags: List[str] = field(default_factory=list)


@dataclass
class ToolConfig:
    """Configuration for tool execution."""
    timeout: Optional[float] = None
    retry_count: int = 0
    cache_ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolFluentAPI:
    """Fluent interface for tool operations.
    
    Example:
        # Register a tool
        agent.tools.register(summarize_tool)
            .with_timeout(30)
            .with_retry(3)
            .with_cache(ttl=3600)
            .execute()
            
        # Execute a tool
        result = await agent.tools.execute("summarize")
            .with_args(text=long_text)
            .with_timeout(60)
            .execute()
    """
    
    def __init__(self, registry: 'ToolRegistry'):
        """Initialize the tool API.
        
        Args:
            registry: The underlying tool registry
        """
        self._registry = registry
        self._reset_state()
        
    def _reset_state(self) -> None:
        """Reset the builder state."""
        self._current_tool: Optional[str] = None
        self._current_config = ToolConfig()
        self._current_args: Dict[str, Any] = {}
        
    def register(self, tool: Callable[..., T]) -> 'ToolFluentAPI':
        """Start tool registration.
        
        Args:
            tool: The tool implementation to register
            
        Returns:
            Self for chaining
        """
        self._current_tool = tool.__name__
        return self
        
    def with_timeout(self, seconds: float) -> 'ToolFluentAPI':
        """Set tool timeout.
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Self for chaining
        """
        self._current_config.timeout = seconds
        return self
        
    def with_retry(self, count: int) -> 'ToolFluentAPI':
        """Set retry count.
        
        Args:
            count: Number of retries
            
        Returns:
            Self for chaining
        """
        self._current_config.retry_count = count
        return self
        
    def with_cache(self, ttl: int) -> 'ToolFluentAPI':
        """Enable result caching.
        
        Args:
            ttl: Cache TTL in seconds
            
        Returns:
            Self for chaining
        """
        self._current_config.cache_ttl = ttl
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'ToolFluentAPI':
        """Add tool metadata.
        
        Args:
            metadata: Key-value pairs of metadata
            
        Returns:
            Self for chaining
        """
        self._current_config.metadata.update(metadata)
        return self
        
    async def execute_registration(self) -> None:
        """Complete tool registration.
        
        Raises:
            ValueError: If no tool was set
            
        Note:
            Resets the builder state after execution
        """
        if not self._current_tool:
            raise ValueError("No tool set for registration")
            
        try:
            await self._registry.register(
                self._current_tool,
                config=self._current_config
            )
        finally:
            self._reset_state()
            
    def execute(self, tool_name: str) -> 'ToolFluentAPI':
        """Start tool execution.
        
        Args:
            tool_name: Name of tool to execute
            
        Returns:
            Self for chaining
        """
        self._current_tool = tool_name
        return self
        
    def with_args(self, **kwargs: Any) -> 'ToolFluentAPI':
        """Set tool arguments.
        
        Args:
            **kwargs: Tool arguments
            
        Returns:
            Self for chaining
        """
        self._current_args.update(kwargs)
        return self
        
    async def execute_tool(self) -> Any:
        """Execute the tool.
        
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If no tool was set
            
        Note:
            Resets the builder state after execution
        """
        if not self._current_tool:
            raise ValueError("No tool set for execution")
            
        try:
            return await self._registry.execute(
                self._current_tool,
                args=self._current_args,
                config=self._current_config
            )
        finally:
            self._reset_state()
            
    async def list_tools(
        self,
        tag: Optional[str] = None
    ) -> List[ToolMetadata]:
        """List registered tools.
        
        Args:
            tag: Optional tag to filter by
            
        Returns:
            List of tool metadata
        """
        return await self._registry.list_tools(tag)
        
    async def get_tool_info(
        self,
        tool_name: str
    ) -> Optional[ToolMetadata]:
        """Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool metadata if found, None otherwise
        """
        return await self._registry.get_tool_info(tool_name)
