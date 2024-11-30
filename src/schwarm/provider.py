"""Base provider interface and common functionality."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Protocol, TypeVar

T = TypeVar('T')


@dataclass
class ProviderConfig:
    """Base configuration for providers."""
    name: str
    timeout: float = 30.0
    retry_count: int = 3
    cache_ttl: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Base response from providers."""
    content: Any
    metadata: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


class ProviderProtocol(Protocol[T]):
    """Protocol defining provider behavior."""
    
    @property
    def config(self) -> ProviderConfig:
        """Provider configuration."""
        ...

    async def initialize(self) -> None:
        """Initialize provider resources."""
        ...

    async def execute(self, *args: Any, **kwargs: Any) -> T:
        """Execute provider functionality."""
        ...

    async def cleanup(self) -> None:
        """Cleanup provider resources."""
        ...


class Provider(ABC):
    """Base class for providers with common functionality.
    
    Providers encapsulate external services or functionality that can be
    used by agents. They handle their own initialization, execution,
    and cleanup.
    """
    
    def __init__(self, config: ProviderConfig):
        """Initialize the provider.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self._initialized = False
        
    @property
    def name(self) -> str:
        """Get provider name."""
        return self.config.name
        
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized."""
        return self._initialized
        
    async def initialize(self) -> None:
        """Initialize provider resources.
        
        This method should be overridden by providers that need
        initialization. The base implementation just marks as initialized.
        """
        self._initialized = True
        
    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute provider functionality.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Provider-specific response
            
        This method must be implemented by concrete providers.
        """
        pass
        
    async def cleanup(self) -> None:
        """Cleanup provider resources.
        
        This method should be overridden by providers that need cleanup.
        The base implementation just marks as not initialized.
        """
        self._initialized = False


class ProviderBuilder(Protocol[T]):
    """Protocol for provider builders."""
    
    def build(self) -> T:
        """Build and return the provider."""
        ...


class BaseProviderBuilder:
    """Base implementation of provider builder."""
    
    def __init__(self, config_class: type[ProviderConfig]):
        """Initialize the builder.
        
        Args:
            config_class: Class to use for configuration
        """
        self._config_class = config_class
        self._config_data: Dict[str, Any] = {
            'name': '',
            'timeout': 30.0,
            'retry_count': 3,
            'cache_ttl': None,
            'metadata': {}
        }
        
    def name(self, name: str) -> 'BaseProviderBuilder':
        """Set provider name.
        
        Args:
            name: Provider name
            
        Returns:
            Self for chaining
        """
        self._config_data['name'] = name
        return self
        
    def with_timeout(self, seconds: float) -> 'BaseProviderBuilder':
        """Set timeout.
        
        Args:
            seconds: Timeout in seconds
            
        Returns:
            Self for chaining
        """
        self._config_data['timeout'] = seconds
        return self
        
    def with_retry(self, count: int) -> 'BaseProviderBuilder':
        """Set retry count.
        
        Args:
            count: Number of retries
            
        Returns:
            Self for chaining
        """
        self._config_data['retry_count'] = count
        return self
        
    def with_cache(self, ttl: int) -> 'BaseProviderBuilder':
        """Enable result caching.
        
        Args:
            ttl: Cache TTL in seconds
            
        Returns:
            Self for chaining
        """
        self._config_data['cache_ttl'] = ttl
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'BaseProviderBuilder':
        """Add metadata.
        
        Args:
            metadata: Key-value pairs of metadata
            
        Returns:
            Self for chaining
        """
        self._config_data['metadata'].update(metadata)
        return self
        
    def _build_config(self) -> ProviderConfig:
        """Build configuration object.
        
        Returns:
            Provider configuration
            
        Raises:
            ValueError: If required configuration is missing
        """
        if not self._config_data['name']:
            raise ValueError("Provider name is required")
            
        return self._config_class(**self._config_data)
