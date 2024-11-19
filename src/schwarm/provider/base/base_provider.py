"""Base class for providers."""

from abc import ABC, abstractmethod

from loguru import logger

from schwarm.models.provider_context import ProviderContext
from schwarm.models.types import Agent
from schwarm.provider.models import BaseProviderConfig


class BaseProvider(ABC):
    """Abstract base class for providers."""

    config: BaseProviderConfig
    agent: Agent
    context: ProviderContext | None = None

    def __init__(self, agent: Agent, config: BaseProviderConfig):
        """Initializes the provider."""
        self.config = config
        self.agent = agent
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        """Run when an agent is started."""
        logger.info(f"Initializing {self.config.provider_name} provider")

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
