"""Event types and targets for the event system."""

from enum import Enum


class EventType(Enum):
    """Core system events."""

    START = "on_start"
    HANDOFF = "on_handoff"
    MESSAGE_COMPLETION = "on_message_completion"
    POST_MESSAGE_COMPLETION = "on_post_message_completion"
    TOOL_EXECUTION = "on_tool_execution"
    POST_TOOL_EXECUTION = "on_post_tool_execution"
    INSTRUCT = "on_instruct"
    POST_INSTRUCT = "on_post_instruct"
