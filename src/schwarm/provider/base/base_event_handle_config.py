"""Provider configuration model."""

from collections.abc import Callable

from pydantic import Field

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider_config import BaseProviderConfig


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for a provider.

    Attributes:
        provider_id: The provider id.
    """

    external_use: bool = Field(default=False, description="Whether the provider can be used in tools")
    internal_use: dict[EventType, list[Callable]] = {}
