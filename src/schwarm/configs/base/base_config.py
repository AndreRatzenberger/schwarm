"""Base provider implementation."""

from typing import Literal

from litellm import BaseModel
from pydantic import Field

# Type aliases
Scope = Literal["global", "scoped", "jit"]
ProviderType = Literal["event", "llm"]


class BaseConfig(BaseModel):
    """Base configuration for all providers."""

    config_type: Literal["event_provider", "llm_provider"] = Field(
        default="event_provider", description="Configuration type"
    )

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
