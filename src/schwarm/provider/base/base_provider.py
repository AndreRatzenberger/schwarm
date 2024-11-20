"""Base class for providers."""

import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from loguru import logger

from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base.models import BaseProviderConfig

if TYPE_CHECKING:
    from schwarm.models.agent import Agent


class BaseProvider(ABC):
    """Abstract base class for providers."""

    config: BaseProviderConfig
    agent: "Agent"
    provider_id: str = ""
    provider_name: str = ""
    context: ProviderContext | None = None

    def __init__(self, agent: "Agent", config: BaseProviderConfig):
        """Initializes the provider."""
        self.config = config
        self.agent = agent
        self.provider_name = self.config.provider_name
        self.provider_id = self.provider_name + str(uuid.uuid4())
        self.initialize()

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
