"""Config for the zep provider."""

from schwarm.provider.models import BaseEventHandleProviderConfig


class ZepConfig(BaseEventHandleProviderConfig):
    """Configuration for the Zep provider."""

    zep_api_key: str = "zepzep"
    zep_url: str = "http://localhost:8000"
    min_fact_rating: float = 0.3
