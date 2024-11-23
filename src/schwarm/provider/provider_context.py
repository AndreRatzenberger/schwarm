"""Defines the context available to providers."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from schwarm.events.event_data import EventType
from schwarm.models.message import Message


class ProviderContext(BaseModel):
    """Context available to providers.

    This class encapsulates all the data that providers might need access to,
    including message history, available agents, tools, and other providers.

    ProviderContext has to be serializable to JSON
    """

    Event: EventType = Field(default=EventType.HANDOFF, description="The current event type")
    max_turns: int = Field(default=10, description="Maximum number of turns in a conversation")
    current_turn: int = Field(default=0, description="Current turn in the conversation")
    model_override: str | None = Field(default=None, description="Model override for the current conversation")
    message_history: list[Message] = Field(
        default_factory=list, description="History of all messages in the current conversation"
    )
    current_message: Message | None = Field(default=None, description="The current message being processed")
    current_agent: Any = Field(default=None, description="The agent currently using this provider")  # TODO str?
    available_agents: list[Any] = Field(default_factory=list, description="Map of all available agents by name")
    available_tools: list[Any] = Field(default_factory=list, description="List of all available tools/functions")
    available_providers: dict[str, Any] = Field(
        default_factory=dict, description="Map of all available providers by name"
    )
    context_variables: dict[str, Any] = Field(default_factory=dict, description="Current context variables")
    instruction_func: Callable[..., str] | None = Field(
        default=None, description="Current instruction being processed (always text)"
    )
    instruction_str: str | None = Field(default=None, description="Resolved instruction (always text)")
    model_config = {"arbitrary_types_allowed": True}

    # Define the model config
    model_config = {"arbitrary_types_allowed": True}

    # Dictionary to hold the on_change callbacks for each property
    _on_change_callbacks: dict[str, Callable[[str, Any, Any], None]] = {}

    def __setattr__(self, name: str, value: Any):
        if name in self.__fields__:
            # Get the old value
            old_value = getattr(self, name, None)

            # Set the new value
            super().__setattr__(name, value)

            # If the value has changed, trigger the on_change event
            if old_value != value:
                callback = self._on_change_callbacks.get(name)
                if callback:
                    callback(name, old_value, value)
        else:
            # Handle attributes not defined as fields
            super().__setattr__(name, value)

    def register_on_change(self, field_name: str, callback: Callable[[str, Any, Any], None]):
        """Register an on_change callback for a specific field.

        Args:
            field_name (str): The field to monitor.
            callback (Callable[[str, Any, Any], None]): The callback function.
        """
        if field_name not in self.__fields__:
            raise ValueError(f"Field {field_name} is not defined in the model.")
        self._on_change_callbacks[field_name] = callback

    # def trigger_event(self, event_type: EventType) -> Any:
    #     """Trigger an event on the context.

    #     Args:
    #         event_type (EventType): The event type to trigger.

    #     Returns:
    #         Any: The result of the event.
    #     """
    #     ProviderManager().trigger_event(event_type, self)
