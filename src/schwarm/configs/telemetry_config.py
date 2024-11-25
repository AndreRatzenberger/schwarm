"""Configuration for telemetry."""

from pydantic import Field

from schwarm.configs.base.base_config import BaseConfig
from schwarm.models.event import EventType


class TelemetryConfig(BaseConfig):
    """Configuration for telemetry."""

    enabled: bool = Field(default=True)
    enable_provider_telemetry: bool = Field(default=True)
    break_on_events: list[EventType] = Field(default=[])
    log_on_events: list[EventType] = Field(default=[])

    def __init__(self, **kwargs):
        """Initialize the telemetry config."""
        super().__init__(**kwargs)
