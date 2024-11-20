"""Base provider implementation."""

import uuid
from abc import ABC, abstractmethod

from loguru import logger

from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base.base_provider_config import BaseProviderConfig


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
