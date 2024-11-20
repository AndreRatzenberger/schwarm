"""Base provider implementation."""

import uuid
from abc import ABC, abstractmethod
from typing import Literal

from litellm import BaseModel
from loguru import logger
from pydantic import Field

from schwarm.models.provider_context import ProviderContext


class BaseProviderConfig(BaseModel):
    """Base configuration for all providers."""

    provider_name: str = Field(..., description="Unique identifier for the provider")
    provider_type: str = Field(..., description="Type of provider (e.g., 'llm', 'memory', etc.)")
    provider_class: str | None = Field(None, description="Full path to provider class")
    scope: Literal["singleton", "scoped", "jit"] = Field(default="scoped", description="Provider lifecycle scope")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")

    def get_provider_class(self) -> type:
        """Get the provider class for this configuration."""
        if not self.provider_class:
            raise ValueError("Provider class not specified in configuration")

        # Import the provider class dynamically
        module_path, class_name = self.provider_class.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(self, config: BaseProviderConfig):
        """Initialize the provider."""
        self.config = config
        self.provider_name = self.config.provider_name
        self.provider_id = self.provider_name + str(uuid.uuid4())

    @abstractmethod
    def initialize(self) -> None:
        """Run when an agent is started."""
        logger.info(f"Initializing {self.provider_name} ({self.provider_id}) provider")

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
