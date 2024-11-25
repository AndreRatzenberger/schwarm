"""Configuration for telemetry."""

from pydantic import BaseModel, Field

from schwarm.models.event import EventType


class TelemetryConfig(BaseModel):
    """Configuration for telemetry."""

    enabled: bool = Field(default=True)
    enable_provider_telemetry: bool = Field(default=True)
    break_on_events: list[EventType] = Field(default=[EventType.START_TURN, EventType.POST_TOOL_EXECUTION])
    log_on_events: list[EventType] = Field(default=[EventType.START_TURN, EventType.POST_TOOL_EXECUTION])
