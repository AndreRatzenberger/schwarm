from typing import Literal

from pydantic import BaseModel, Field


class WebsocketMessage(BaseModel):
    """Core system events."""

    message_type: Literal["CHAT", "BREAK", "ERROR", "EVENT", "STREAM"] = Field(
        default="EVENT", description="Type of message"
    )
    message: str = Field(default="", description="Message content")

    @classmethod
    def chat_requested(cls, message: str = "Test chat request"):
        """Create a chat request message."""
        return cls(message_type="CHAT", message=message)

    @classmethod
    def is_waiting(cls, message: str = "Waiting for user input"):
        """Create a waiting status message."""
        return cls(message_type="BREAK", message=message)

    @classmethod
    def event(cls, message: str = "Test event message"):
        """Create an event message."""
        return cls(message_type="EVENT", message=message)

    @classmethod
    def stream(cls, message: str = "Test event message"):
        """Create an event message."""
        return cls(message_type="STREAM", message=message)
