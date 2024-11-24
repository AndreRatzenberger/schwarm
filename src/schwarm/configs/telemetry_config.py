"""Configuration for telemetry."""

from pydantic import Field

from schwarm.configs.base.base_config import BaseConfig


class TelemetryConfig(BaseConfig):
    """Configuration for telemetry."""

    enable_telemetry: bool = Field(default=True)
    enable_provider_telemetry: bool = Field(default=True)

    def __init__(self):
        """Initialize the telemetry config."""
