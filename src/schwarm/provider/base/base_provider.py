"""Base provider implementation."""

from abc import ABC
from typing import Literal

from loguru import logger
from pydantic import Field

from schwarm.configs.base.base_config import BaseConfig
from schwarm.models.provider_context import ProviderContextModel

# Type aliases
Scope = Literal["global", "scoped", "jit"]
ProviderType = Literal["event", "llm"]


class BaseProviderConfig(BaseConfig):
    """Base configuration for all providers."""

    scope: Scope = Field(default="scoped", description="Provider lifecycle scope")
    provider_id_override: Scope = Field(default="", description="Override provider ID")
    enabled: bool = Field(default=True, description="Provider enabled status")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(self, config: BaseProviderConfig):
        """Initialize the provider with a configuration."""
        self.config = config
        self.context = ProviderContextModel()
        self.is_enabled = config.enabled
        if not self.config.provider_id_override:
            self._provider_id = self.__class__.__name__.lower()
        else:
            self._provider_id = self.config.provider_id_override

    def __post_init__(self):
        """Post-initialization actions."""
        logger.debug(f"Initialized provider {self.__class__.__name__} with scope: {self.config.scope}")

    def update_context(self, context: ProviderContextModel) -> None:
        """Updates the provider's context with new data."""
        logger.debug(f"Updating context for provider {self.__class__.__name__}")
        self.context = context

    def get_context(self) -> ProviderContextModel:
        """Gets the provider's current context.

        Returns:
            ProviderContext: Current context or raises ValueError if context is not set.

        Raises:
            ValueError: If context has not been set.
        """
        if not self.context:
            raise ValueError("Provider context has not been set")
        return self.context
