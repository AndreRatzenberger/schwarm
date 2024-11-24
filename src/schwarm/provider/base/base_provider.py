"""Base provider implementation."""

from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

from litellm import BaseModel
from opentelemetry.trace import Tracer
from pydantic import Field

from schwarm.models.provider_context import ProviderContext

# Type aliases
Scope = Literal["global", "scoped", "jit"]
ProviderType = Literal["event", "llm"]


class BaseProviderConfig(BaseModel):
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
    context: ProviderContext = field(default_factory=ProviderContext)
    is_enabled: bool = True
    _tracer: Tracer | None = None

    def update_context(self, context: ProviderContext) -> None:
        """Updates the provider's context with new data."""
        self.context = context

    def get_context(self) -> ProviderContext:
        """Gets the provider's current context.

        Returns:
            ProviderContext: Current context or raises ValueError if context is not set.

        Raises:
            ValueError: If context has not been set.
        """
        if not self.context:
            raise ValueError("Provider context has not been set")
        return self.context

    def set_tracer(self, tracer: Tracer):
        """Sets the tracer for the provider."""
        self._tracer = tracer
        return self
