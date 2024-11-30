"""Enhanced LLM provider with fluent API."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from litellm import completion

from ..provider import Provider


@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    timeout: float = 30.0
    retry_count: int = 3
    cache_ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """Response from LLM provider."""
    content: str
    model: str
    usage: Dict[str, int]
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LLMProviderBuilder:
    """Fluent builder for LLM provider configuration.
    
    Example:
        provider = (LLMProviderBuilder()
            .model("gpt-4")
            .temperature(0.7)
            .with_timeout(30)
            .with_retry(3)
            .build())
    """
    
    def __init__(self):
        """Initialize with default configuration."""
        self._config = LLMConfig(
            model="gpt-4",
            temperature=0.7
        )
        
    def model(self, model: str) -> 'LLMProviderBuilder':
        """Set the model.
        
        Args:
            model: Model identifier
            
        Returns:
            Self for chaining
        """
        self._config.model = model
        return self
        
    def temperature(self, temp: float) -> 'LLMProviderBuilder':
        """Set temperature.
        
        Args:
            temp: Temperature value (0-1)
            
        Returns:
            Self for chaining
        """
        self._config.temperature = temp
        return self
        
    def max_tokens(self, tokens: int) -> 'LLMProviderBuilder':
        """Set max tokens.
        
        Args:
            tokens: Maximum tokens
            
        Returns:
            Self for chaining
        """
        self._config.max_tokens = tokens
        return self
        
    def with_timeout(self, seconds: float) -> 'LLMProviderBuilder':
        """Set timeout.
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Self for chaining
        """
        self._config.timeout = seconds
        return self
        
    def with_retry(self, count: int) -> 'LLMProviderBuilder':
        """Set retry count.
        
        Args:
            count: Number of retries
            
        Returns:
            Self for chaining
        """
        self._config.retry_count = count
        return self
        
    def with_cache(self, ttl: int) -> 'LLMProviderBuilder':
        """Enable result caching.
        
        Args:
            ttl: Cache TTL in seconds
            
        Returns:
            Self for chaining
        """
        self._config.cache_ttl = ttl
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'LLMProviderBuilder':
        """Add metadata.
        
        Args:
            metadata: Key-value pairs of metadata
            
        Returns:
            Self for chaining
        """
        self._config.metadata.update(metadata)
        return self
        
    def build(self) -> 'LLMProvider':
        """Build the provider.
        
        Returns:
            Configured LLM provider
        """
        return LLMProvider(self._config)


class LLMProvider(Provider):
    """Enhanced provider for LLM interactions.
    
    Example:
        provider = (LLMProviderBuilder()
            .model("gpt-4")
            .temperature(0.7)
            .build())
            
        response = await provider.complete("Tell me about neural networks")
    """
    
    def __init__(self, config: LLMConfig):
        """Initialize the provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> None:
        """Initialize the provider.
        
        Note:
            Currently no initialization needed as litellm handles
            connection management.
        """
        pass
        
    async def complete(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """Execute an LLM query.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            **kwargs: Additional parameters
            
        Returns:
            Response from the model
            
        Raises:
            Exception: If completion fails
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
            
        # Add user message
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Check cache
        if self.config.cache_ttl:
            cache_key = self._make_cache_key(messages)
            cached = self._get_cached(cache_key)
            if cached:
                return cached
                
        # Prepare parameters
        params = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            **kwargs
        }
        
        if self.config.max_tokens:
            params["max_tokens"] = self.config.max_tokens
            
        # Execute with retry
        response = await self._execute_with_retry(params)
        
        # Create response object
        result = LLMResponse(
            content=response.choices[0].message.content,
            model=self.config.model,
            usage=response.usage,
            metadata=self.config.metadata
        )
        
        # Cache if enabled
        if self.config.cache_ttl:
            self._cache_result(cache_key, result)
            
        return result
        
    async def _execute_with_retry(
        self,
        params: Dict[str, Any]
    ) -> Any:
        """Execute with retry logic.
        
        Args:
            params: Completion parameters
            
        Returns:
            Raw completion response
            
        Raises:
            Exception: If all retries fail
        """
        retries = self.config.retry_count
        last_error = None
        
        while retries >= 0:
            try:
                return await completion(**params)
            except Exception as e:
                last_error = e
                retries -= 1
                if retries >= 0:
                    await asyncio.sleep(2 ** (self.config.retry_count - retries))
                    
        raise last_error
        
    def _make_cache_key(self, messages: List[Dict[str, str]]) -> str:
        """Create cache key from messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Cache key string
        """
        return str(hash(str(messages)))
        
    def _get_cached(self, key: str) -> Optional[LLMResponse]:
        """Get cached response if valid.
        
        Args:
            key: Cache key
            
        Returns:
            Cached response if valid, None otherwise
        """
        if key not in self._cache:
            return None
            
        entry = self._cache[key]
        if (
            datetime.utcnow() - entry['time'] >
            timedelta(seconds=self.config.cache_ttl)
        ):
            del self._cache[key]
            return None
            
        return entry['response']
        
    def _cache_result(self, key: str, response: LLMResponse) -> None:
        """Cache a completion response.
        
        Args:
            key: Cache key
            response: Response to cache
        """
        self._cache[key] = {
            'response': response,
            'time': datetime.utcnow()
        }
