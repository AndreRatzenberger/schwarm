"""Configuration for telemetry."""

from pydantic import BaseModel, Field

from schwarm.models.event import EventType


class TelemetryConfig(BaseModel):
    """Configuration for telemetry."""

    enabled: bool = Field(default=True)
    enable_provider_telemetry: bool = Field(default=True)
    break_on_events: list[EventType] = Field(default=[])
    log_on_events: list[EventType] = Field(
        default=[
            EventType.START_TURN,
            EventType.INSTRUCT,
            EventType.MESSAGE_COMPLETION,
            EventType.POST_MESSAGE_COMPLETION,
            EventType.TOOL_EXECUTION,
            EventType.POST_TOOL_EXECUTION,
            EventType.HANDOFF,
        ]
    )
