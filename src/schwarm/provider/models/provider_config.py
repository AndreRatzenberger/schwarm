"""Provider configuration model."""

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes:
        provider_id: The provider id.
    """

    provider_id: str = Field(default="", description="The provider id for the provider")
