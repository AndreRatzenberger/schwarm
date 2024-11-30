"""Tool registry implementation."""

import asyncio
from datetime import datetime, timedelta
import functools
from typing import Any, Callable, Dict, List, Optional

from .api import ToolConfig, ToolMetadata


class ToolRegistry:
    """Registry for managing and executing tools.
    
    The registry handles tool registration, execution, caching,
    and metadata management.
    """
    
    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: Dict[str, Callable] = {}
        self._configs: Dict[str, ToolConfig] = {}
        self._metadata: Dict[str, ToolMetadata] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    async def register(
        self,
        tool: Callable,
        config: Optional[ToolConfig] = None
    ) -> None:
        """Register a tool with the registry.
        
        Args:
            tool: The tool implementation
            config: Optional tool configuration
            
        Raises:
            ValueError: If tool is already registered
        """
        async with self._lock:
            name = tool.__name__
            if name in self._tools:
                raise ValueError(f"Tool '{name}' already registered")
                
            self._tools[name] = tool
            self._configs[name] = config or ToolConfig()
            self._metadata[name] = self._extract_metadata(tool)
            
    def _extract_metadata(self, tool: Callable) -> ToolMetadata:
        """Extract metadata from tool implementation.
        
        Args:
            tool: The tool implementation
            
        Returns:
            Extracted tool metadata
        """
        # Get tool documentation
        doc = tool.__doc__ or "No description available"
        
        # Get type hints
        hints = tool.__annotations__
        
        # Extract required parameters
        params = {
            k: v for k, v in hints.items()
            if k != 'return'
        }
        
        # Determine required params (those without defaults)
        required = [
            p for p in params
            if p not in (tool.__defaults__ or ())
        ]
        
        return ToolMetadata(
            name=tool.__name__,
            description=doc.strip(),
            parameters=params,
            required_params=required,
            return_type=hints.get('return', Any),
            tags=getattr(tool, '_tags', [])
        )
        
    async def execute(
        self,
        name: str,
        args: Dict[str, Any],
        config: Optional[ToolConfig] = None
    ) -> Any:
        """Execute a registered tool.
        
        Args:
            name: Name of the tool to execute
            args: Tool arguments
            config: Optional execution configuration
            
        Returns:
            Tool execution result
            
        Raises:
            KeyError: If tool not found
            ValueError: If required args missing
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found")
            
        tool = self._tools[name]
        tool_config = config or self._configs[name]
        
        # Check cache
        if tool_config.cache_ttl:
            cache_key = self._make_cache_key(name, args)
            cached = self._get_cached(cache_key, tool_config.cache_ttl)
            if cached is not None:
                return cached
                
        # Validate required parameters
        metadata = self._metadata[name]
        missing = [
            p for p in metadata.required_params
            if p not in args
        ]
        if missing:
            raise ValueError(f"Missing required parameters: {missing}")
            
        # Execute with retry
        result = await self._execute_with_retry(
            tool,
            args,
            tool_config
        )
        
        # Cache result
        if tool_config.cache_ttl:
            self._cache_result(
                cache_key,
                result,
                tool_config.cache_ttl
            )
            
        return result
        
    async def _execute_with_retry(
        self,
        tool: Callable,
        args: Dict[str, Any],
        config: ToolConfig
    ) -> Any:
        """Execute tool with retry logic.
        
        Args:
            tool: Tool implementation
            args: Tool arguments
            config: Tool configuration
            
        Returns:
            Tool execution result
            
        Raises:
            Exception: If all retries fail
        """
        retries = config.retry_count
        last_error = None
        
        while retries >= 0:
            try:
                if config.timeout:
                    return await asyncio.wait_for(
                        tool(**args),
                        timeout=config.timeout
                    )
                return await tool(**args)
            except Exception as e:
                last_error = e
                retries -= 1
                if retries >= 0:
                    # Wait before retry with exponential backoff
                    await asyncio.sleep(2 ** (config.retry_count - retries))
                    
        raise last_error
        
    def _make_cache_key(self, name: str, args: Dict[str, Any]) -> str:
        """Create a cache key from tool name and args.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Cache key string
        """
        # Sort args for consistent keys
        sorted_args = sorted(args.items())
        return f"{name}:{sorted_args}"
        
    def _get_cached(
        self,
        key: str,
        ttl: int
    ) -> Optional[Any]:
        """Get cached result if valid.
        
        Args:
            key: Cache key
            ttl: Cache TTL in seconds
            
        Returns:
            Cached result if valid, None otherwise
        """
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if datetime.utcnow() - entry['time'] > timedelta(seconds=ttl):
            del self._cache[key]
            return None
            
        return entry['result']
        
    def _cache_result(
        self,
        key: str,
        result: Any,
        ttl: int
    ) -> None:
        """Cache a tool execution result.
        
        Args:
            key: Cache key
            result: Result to cache
            ttl: Cache TTL in seconds
        """
        self._cache[key] = {
            'result': result,
            'time': datetime.utcnow()
        }
        
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
        if tag:
            return [
                meta for meta in self._metadata.values()
                if tag in meta.tags
            ]
        return list(self._metadata.values())
        
    async def get_tool_info(
        self,
        name: str
    ) -> Optional[ToolMetadata]:
        """Get information about a specific tool.
        
        Args:
            name: Tool name
            
        Returns:
            Tool metadata if found, None otherwise
        """
        return self._metadata.get(name)
