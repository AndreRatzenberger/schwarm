"""Provider configuration model."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderConfig(BaseModel):
    """Configuration for a provider.

    Attributes:
        api_key: The API key for authentication with the provider
        api_base: The base URL for API endpoints
        api_version: The API version to use
        organization: The organization identifier
    """

    api_key: str = Field(default="", description="The API key for the provider")
    api_base: str = Field(default="", description="The API endpoint")
    api_version: str = Field(default="", description="The API version")
    organization: str = Field(default="", description="The API organization")

    @field_validator("api_base")
    @classmethod
    def validate_api_base(cls, v: str) -> str:
        """Validate that api_base is a valid URL if provided."""
        if v and not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("API base must start with http:// or https:// if provided")
        return v

    model_config = ConfigDict(frozen=True)  # Make config immutable
