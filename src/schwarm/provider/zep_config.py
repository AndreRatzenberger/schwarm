"""Configuration for Zep memory provider."""

from pydantic import Field

from schwarm.provider.base.base_provider_config import BaseProviderConfig, ProviderScope


class ZepConfig(BaseProviderConfig):
    """Configuration for Zep memory provider."""

    zep_api_key: str = Field(..., description="API key for Zep service")
    zep_api_url: str = Field(default="http://localhost:8000", description="URL for Zep service")
    min_fact_rating: float = Field(default=0.7, description="Minimum rating for facts to be considered")
    on_completion_save_completion_to_memory: bool = Field(
        default=True, description="Whether to save completions to memory"
    )

    def __init__(self, **data):
        """Initialize with defaults."""
        data.update(
            {
                "provider_name": "zep",
                "provider_type": "memory",
                "provider_class": "schwarm.provider.zep_provider.ZepProvider",
                "scope": ProviderScope.AGENT,
            }
        )
        super().__init__(**data)
