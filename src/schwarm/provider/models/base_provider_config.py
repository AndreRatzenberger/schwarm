"""Provider configuration model."""

from typing import Literal

from pydantic import BaseModel, Field


class BaseProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes:
        provider_id: The provider id.
    """

    provider_type: Literal["llm", "event"] = Field(
        default="", description="The type of provider. LLM provider or EventHandler provider"
    )
    provider_name: str = Field(default="", description="The provider id for the provider")
    provider_lifecycle: Literal["singleton", "scoped", "stateless"] = Field(
        default="", description="The type of provider. LLM provider or EventHandler provider"
    )
