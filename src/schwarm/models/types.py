"""Core types for the Schwarm framework."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field
from rich.console import Console
from rich.json import JSON
from rich.table import Table
from rich.text import Text

from schwarm.models.agent import Agent
from schwarm.models.message import Message
from schwarm.models.result import Result

# Type aliases
ContextVariables = dict[str, Any]
AgentFunction = Callable[..., "str | Agent | dict[str, Any] | Result"]


class Response(BaseModel):
    """Encapsulates the complete response from an agent interaction.

    Attributes:
        messages: List of message exchanges during the interaction
        agent: The final agent state after the interaction
        context_variables: Updated context variables after the interaction
    """

    messages: list[Message] = Field(
        default_factory=list,
        description="List of messages exchanged during the interaction",
    )
    agent: Agent | None = Field(default=None, description="Final agent state after interaction")
    context_variables: ContextVariables = Field(
        default_factory=dict, description="Updated context variables after interaction"
    )

    def render_response(self) -> None:
        console = Console()

        # Create a main table to summarize the response
        table = Table(title="Response Summary", show_header=True, header_style="bold magenta")
        table.add_column("Property", style="dim", width=20)
        table.add_column("Details", width=80)

        # Render messages
        messages = self.messages
        if messages:
            messages_table = Table(title="Messages", show_header=True, header_style="bold cyan")
            messages_table.add_column("Role", style="green")
            messages_table.add_column("Content")
            messages_table.add_column("Sender")
            for message in messages:
                messages_table.add_row(message.role, message.content, message.sender)
            table.add_row("Messages", messages_table)
        else:
            table.add_row("Messages", "No messages found")

        # Render agent details
        agent = self.agent
        if agent:
            agent_table = Table(title="Agent Details", show_header=False)
            agent_table.add_row("Name", agent.name)
            agent_table.add_row("Model", agent.model)
            agent_table.add_row("Description", agent.description or "N/A")
            table.add_row("Agent", agent_table)

        # Render context variables
        if self.context_variables:
            try:
                context_json = JSON.from_data(response_object.context_variables)  # type: ignore  # noqa: F821
                table.add_row("Context Variables", context_json)
            except Exception:
                context_text = Text(str(self.context_variables), style="italic red")
                table.add_row("Context Variables", context_text)
        else:
            table.add_row("Context Variables", "No context variables found")

        # Render additional_info if available
        additional_info = getattr(self.messages[0], "additional_info", None)
        if additional_info:
            additional_table = Table(title="Additional Info", show_header=True, header_style="bold blue")
            additional_table.add_column("Key")
            additional_table.add_column("Value")
            for key, value in additional_info.items():
                try:
                    value_display = JSON.from_data(value) if isinstance(value, dict) else str(value)
                except Exception:
                    value_display = repr(value)
                additional_table.add_row(str(key), value_display)
            table.add_row("Additional Info", additional_table)
        else:
            table.add_row("Additional Info", "No additional info found")

        # Render configurations
        if self.agent.configs:  # type: ignore
            config_table = Table(title="Provider Configurations", show_header=True, header_style="bold yellow")
            config_table.add_column("Type")
            config_table.add_column("Details")
            for config in self.agent.configs:  # type: ignore
                config_table.add_row(
                    config.__class__.__name__,
                    repr(config),  # Fallback to repr for non-serializable data
                )
            table.add_row("Configurations", config_table)
        else:
            table.add_row("Configurations", "No configurations found")

        # Print the table
        console.print(table)


# Re-export moved classes for backward compatibility
__all__ = ["Agent", "Result", "Response", "ContextVariables", "AgentFunction"]
