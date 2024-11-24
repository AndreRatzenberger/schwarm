"""Base provider implementation."""

from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

from loguru import logger
from opentelemetry.trace import Tracer
from pydantic import Field

from schwarm.configs.base.base_config import BaseConfig
from schwarm.models.provider_context import ProviderContextModel

# Type aliases
Scope = Literal["global", "scoped", "jit"]
ProviderType = Literal["event", "llm"]


class BaseProviderConfig(BaseConfig):
    """Base configuration for all providers."""

    scope: Scope = Field(default="scoped", description="Provider lifecycle scope")
    enabled: bool = Field(default=True, description="Provider enabled status")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True


@dataclass
class BaseProvider(ABC):
    """Base class for all providers."""

    config: BaseProviderConfig
    _provider_id: str = field(default="", init=False)
    context: ProviderContextModel = field(default_factory=ProviderContextModel)
    is_enabled: bool = True
    _tracer: Tracer | None = None

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

    def init_tracer(self, tracer: Tracer | None = None):
        """Initializes the tracer for the provider.

        Args:
            tracer (Optional[Tracer]): Explicit tracer instance. If None, falls back to `TelemetryManager`.

        Note:
            If no tracer is provided and the `TelemetryManager` is not initialized, an error will be logged.
        """
        self._tracer = tracer

    def get_tracer(self) -> Tracer:
        """Retrieves the initialized tracer.

        Returns:
            Tracer: The initialized tracer instance.

        Raises:
            RuntimeError: If the tracer has not been initialized.
        """
        if not self._tracer:
            raise RuntimeError(f"Tracer has not been initialized for provider {self.__class__.__name__}")
        return self._tracer
