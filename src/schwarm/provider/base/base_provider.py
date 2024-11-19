"""Base class for providers."""

from abc import ABC, abstractmethod

from schwarm.models.types import Agent
from schwarm.provider.models import BaseProviderConfig


class BaseProvider(ABC):
    """Abstract base class for providers."""

    config: BaseProviderConfig
    agent: Agent

    def __init__(self, agent: Agent, config: BaseProviderConfig):
        """Initializes the provider."""
        self.config = config
        self.agent = agent
        self.initialize()

    @abstractmethod
    def initialize(self) -> None:
        """Run when an agent is started."""
        pass
