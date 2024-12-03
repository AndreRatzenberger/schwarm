from typing import Literal

from pydantic import BaseModel, Field


class WebsocketMessage(BaseModel):
    """Core system events."""

    message_type: Literal["CHAT_REQUESTED", "IS_WAITING", "CHAT_INPUT", "EVENT", "PAUSE_STATUS", "PAUSE_REQUEST"] = (
        Field(default="EVENT", description="Type of message")
    )
    message: str = Field(default="", description="Message content")
