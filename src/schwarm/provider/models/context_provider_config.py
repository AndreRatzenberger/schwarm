"""Config for the context provider."""

from schwarm.provider.base.models import BaseEventHandleProviderConfig


class ContextProviderConfig(BaseEventHandleProviderConfig):
    """Configuration for the context provider."""

    def __init__(self):
        """Initialize the context provider configuration."""
        super().__init__(provider_type="event", provider_name="context", provider_lifecycle="singleton")
