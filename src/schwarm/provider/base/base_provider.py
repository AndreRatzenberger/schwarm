"""Base provider implementation."""

import uuid
from abc import ABC, abstractmethod

from litellm import BaseModel
from loguru import logger
from pydantic import Field

from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base import Scope

# Type aliases


class BaseProviderConfig(BaseModel):
    """Base configuration for all providers."""

    # provider_name: str = Field(default="", description="Unique identifier for the provider")
    # provider_type: ProviderType = Field(default="", description="Type of provider (e.g., 'llm', 'memory', etc.)")
    scope: Scope = Field(default="scoped", description="Provider lifecycle scope")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


class BaseProvider(ABC):
    """Base class for all providers."""

    _provider_id: str
    scope: str
    config: BaseProviderConfig
    context: ProviderContext

    def __init__(self, config: BaseProviderConfig, id: str = ""):
        """Initialize the provider."""
        self.config = config
        self.context
        if not id:
            self._provider_id = f"{self.__class__.__name__}_{uuid.uuid4()}"
        else:
            self._provider_id = id

    @abstractmethod
    def initialize(self) -> None:
        """Run when an agent is started."""
        logger.info(f"Initializing {self._provider_id} ({self._provider_id}) provider")

    def update_context(self, context: ProviderContext) -> None:
        """Updates the provider's context with new data.

        Args:
            context: New context data
        """
        self.context = context

    def get_context(self) -> ProviderContext:
        """Gets the provider's current context.

        Returns:
            Current context or raises ValueError if context not set

        Raises:
            ValueError: If context has not been set
        """
        if not self.context:
            raise ValueError("Provider context has not been set")
        return self.context
