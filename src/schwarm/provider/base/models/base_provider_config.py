"""Provider configuration model."""

from typing import Literal

from pydantic import BaseModel, Field

from schwarm.provider.base.models.provider_scope import ProviderScope


class BaseProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes:
        provider_type: The type of provider (llm or event)
        provider_name: The unique name for the provider
        scope: The lifecycle scope of the provider
    """

    provider_type: Literal["llm", "event"] = Field(
        default="event", description="The type of provider. LLM provider or EventHandler provider"
    )
    provider_name: str = Field(default="", description="The unique name for the provider")
    scope: ProviderScope = Field(default=ProviderScope.SCOPED, description="The lifecycle scope of the provider")
