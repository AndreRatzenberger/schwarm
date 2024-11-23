"""Debug provider for displaying and logging system information."""

import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import ipywidgets as widgets
from IPython.display import clear_output, display
from loguru import logger
from pydantic import Field
from rich.console import Console
from rich.markdown import Markdown

from schwarm.core.logging import truncate_string
from schwarm.events.event_data import Event, EventType
from schwarm.models.agent import Agent
from schwarm.models.result import Result
from schwarm.provider.base import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.budget_provider import BudgetProvider
from schwarm.provider.provider_context import ProviderContext
from schwarm.provider.provider_manager import ProviderManager
from schwarm.utils.settings import APP_SETTINGS

continue_event = threading.Event()

console = Console()


class DebugConfig(BaseEventHandleProviderConfig):
    """Configuration for the debug provider.

    This configuration includes all display and logging settings,
    controlling what information is shown to the user and how.
    """

    show_instructions: bool = Field(default=True, description="Whether to show agent instructions")
    instructions_wait_for_user_input: bool = Field(
        default=True, description="Whether to wait for user input after showing instructions"
    )
    show_function_calls: bool = Field(default=True, description="Whether to show function calls")
    function_calls_wait_for_user_input: bool = Field(
        default=True, description="Whether to wait for user input after showing function calls"
    )
    function_calls_print_context_variables: bool = Field(
        default=True, description="Whether to print context variables with function calls"
    )
    application_frame: Literal["cli", "jupyter"] = Field(
        default="cli", description="Whether the application is running in a CLI or Jupyter environment"
    )
    show_budget: bool = Field(default=True, description="Whether to show budget information")
    max_length: int = Field(default=-1, description="Maximum length for displayed text (-1 for no limit)")
    save_logs: bool = Field(default=True, description="Whether to save logs to files")
    provider_id: str = Field(default="debug", description="Provider ID")


class DebugProvider(BaseEventHandleProvider):
    """Debug provider that handles display and logging functionality.

    This provider replaces the DisplayService, handling all display and logging
    through the event system. It shows and logs:
    - Agent instructions
    - Function calls and results
    - Budget information
    - General debug information
    """

    config: DebugConfig
    _provider_id: str = Field(default="debug", description="Provider ID")

    def initialize(self):
        """Initialize the debug provider by ensuring the log directory exists."""
        self._ensure_log_directory()

    def handle_event(self, event: Event[ProviderContext]) -> ProviderContext | None:
        """Handle events by showing relevant information."""
        self.context = event.payload
        if event.type == EventType.START:
            self.handle_start(event.payload)
        elif event.type == EventType.MESSAGE_COMPLETION:
            self.handle_message_completion()
        elif event.type == EventType.TOOL_EXECUTION:
            self.handle_tool_execution()
        elif event.type == EventType.POST_TOOL_EXECUTION:
            self.handle_post_tool_execution()

    def handle_start(self, payload: ProviderContext) -> ProviderContext | None:
        """Handle agent start by initializing logging and showing instructions."""
        if self.config.save_logs:
            self._ensure_log_directory()
            self._delete_logs()

        if not self.context:
            logger.warning("No context available for debug provider")
            return

        self._show_instructions(payload)

    def handle_message_completion(self) -> None:
        """Handle message completion to show relevant information."""
        if not self.context:
            return

        # Show budget if configured
        if self.config.show_budget:
            self._show_budget(self.context.current_agent)

    def handle_tool_execution(self) -> None:
        """Handle tool execution to show function calls."""
        if not self.context or not self.context.message_history:
            return

        latest_message = self.context.message_history[-1]
        if not latest_message.tool_calls:
            return

        # Show function call information
        for tool_call in latest_message.tool_calls:
            self._show_function(
                context_variables=self.context.context_variables,
                sender=self.context.current_agent.name,
                function=tool_call.function.name,
                parameters=tool_call.function.arguments,
            )

    def handle_post_tool_execution(self) -> None:
        """Handle post tool execution to show results."""
        if not self.context or not self.context.message_history:
            return

        # Get the tool result message
        result_messages = [
            msg
            for msg in self.context.message_history[-2:]  # Look at last 2 messages
            if msg.role == "tool"  # Tool messages contain results
        ]
        if not result_messages:
            return

        # Show function results
        for msg in result_messages:
            if "result" in msg.additional_info:
                self._show_function(
                    context_variables=self.context.context_variables,
                    sender=self.context.current_agent.name,
                    function="tool_result",
                    result=msg.additional_info["result"],
                )

    def _ensure_log_directory(self) -> None:
        """Ensure the log directory exists."""
        log_path = os.path.normpath(os.path.join(APP_SETTINGS.DATA_FOLDER, "logs"))
        os.makedirs(log_path, exist_ok=True)

    def _delete_logs(self) -> None:
        """Delete all log files in the logs directory."""
        log_dir = Path(APP_SETTINGS.DATA_FOLDER) / "logs"
        if log_dir.exists():
            for file in log_dir.glob("*.log"):
                try:
                    file.unlink(missing_ok=True)
                except (PermissionError, OSError):
                    logger.warning(f"Could not delete log file {file}, it may be in use")
            for file in log_dir.glob("*.csv"):
                try:
                    file.unlink(missing_ok=True)
                except (PermissionError, OSError):
                    logger.warning(f"Could not delete log file {file}, it may be in use")

    def _write_to_log(self, filename: str, content: str, mode: str = "a") -> None:
        """Write content to a log file."""
        if not self.config.save_logs:
            return

        log_path = os.path.normpath(os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", filename))
        os.makedirs(os.path.dirname(log_path), exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content_with_timestamp = f"Timestamp: {timestamp}\n{content}\n"

        # Write to specific log file
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(content_with_timestamp)

        # Write to combined log file
        with open(
            os.path.normpath(os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", "all.log")), mode, encoding="utf-8"
        ) as f:
            f.write(content_with_timestamp)

    def _show_instructions(self, event: ProviderContext) -> None:
        """Show the instructions to the user."""
        if not self.config.show_instructions:
            return
        agent_name = event.current_agent.name

        if callable(event.current_agent.instructions):
            instructions = event.instruction_str
        else:
            instructions = event.current_agent.instructions()
        console.line()
        console.print(Markdown(f"# 📝 Instructing 🤖 {agent_name}"), style="bold orange3")
        console.line()
        if isinstance(instructions, str):
            console.print(Markdown(truncate_string(instructions, self.config.max_length)), style="italic")

        # Write to instructions log
        log_content = f"Agent: {agent_name}\nInstructions:\n{instructions}\n{'=' * 50}\n"
        self._write_to_log("instructions.log", log_content)

        if self.config.instructions_wait_for_user_input:
            if self.config.application_frame == "cli":
                console.line()
                console.input("Press Enter to continue...")
            else:
                self.pause_execution()

    def _show_budget(self, agent: Agent) -> None:
        """Show the budget to the user."""
        if not self.config.show_budget:
            return

        console.line()
        console.print(Markdown(f"# 💰 Budget - {agent.name}"), style="bold orange3")
        manager = ProviderManager()
        budget = manager.get_provider_by_id(agent.name, "budget")

        console.line()
        # Initialize log_content with default empty values
        log_content = f"Agent: {agent.name}\nNo budget information available\n{'=' * 50}\n"

        if isinstance(budget, BudgetProvider):
            console.print(Markdown(f"**- Max Spent:** ${budget.config.max_spent:.5f}"), style="italic")
            console.print(Markdown(f"**- Max Tokens:** {budget.config.max_tokens}"), style="italic")
            console.print(Markdown(f"**- Current Spent:** ${budget.config.current_spent:.5f}"), style="italic")
            console.print(Markdown(f"**- Current Tokens:** {budget.config.current_tokens}"), style="italic")

            # Update log_content with budget information
            log_content = (
                f"Agent: {agent.name}\n"
                f"Max Spent: ${budget.config.max_spent:.5f}\n"
                f"Max Tokens: {budget.config.max_tokens}\n"
                f"Current Spent: ${budget.config.current_spent:.5f}\n"
                f"Current Tokens: {budget.config.current_tokens}\n"
                f"{'=' * 50}\n"
            )

        self._write_to_log("budget.log", log_content)

    def _show_function(
        self,
        context_variables: dict[str, Any],
        sender: str = "",
        receiver: str | None = None,
        function: str | None = "",
        parameters: dict[str, Any] | None = None,
        result: Result | None = None,
    ) -> None:
        """Show the function and parameters to the user."""
        if not self.config.show_function_calls:
            return

        console.line()

        if receiver:
            console.print(Markdown(f"# 🤖 {sender} -> ⚡ {function} -> 🤖 {receiver}"), style="bold green")
            log_header = f"Sender: {sender}\nFunction: {function}\nReceiver: {receiver}\n"
        else:
            console.print(Markdown(f"# 🤖 {sender} -> ⚡ {function}"), style="bold green")
            log_header = f"Sender: {sender}\nFunction: {function}\n"

        log_content = log_header

        # Show parameters if provided
        if parameters:
            console.print(Markdown(f"## Parameters"), style="bold green")
            log_content += "Parameters:\n"

            for key, value in parameters.items():
                if key == APP_SETTINGS.CONTEXT_VARS_KEY:
                    continue
                console.line()
                console.print(Markdown(f"**- {key}**"), style="bold italic")
                console.line()
                console.print(Markdown(f"   {truncate_string(str(value), self.config.max_length)}"), style="italic")
                log_content += f"   {key}: {value}\n"

        # Show result if provided
        if result:
            console.rule()
            console.print(Markdown(f"## Result"), style="bold green")
            log_content += f"{'-' * 20}\nResult:\n"

            dict_result = result.model_dump()
            for key, value in dict_result.items():
                console.line()
                console.print(Markdown(f"**- {key}**"), style="bold italic")
                console.line()
                console.print(Markdown(f"   {truncate_string(str(value), self.config.max_length)}"), style="italic")
                log_content += f"   {key}: {value}\n"

        # Show context variables if configured
        if self.config.function_calls_print_context_variables:
            console.rule()
            console.print(Markdown(f"**- Context Variables**"), style="bold italic")
            log_content += f"{'-' * 20}\n"
            console.print(truncate_string(str(context_variables), self.config.max_length))
            log_content += f"Context Variables: {context_variables}\n"

        log_content += f"{'=' * 50}\n"
        self._write_to_log("functions.log", log_content)

        if self.config.function_calls_wait_for_user_input:
            if self.config.application_frame == "cli":
                console.line()
                console.input("Press Enter to continue...")
            else:
                self.pause_execution()

    def on_button_click(self, b):
        continue_event.set()  # Set the event to continue execution
        clear_output(wait=True)  # Clear the button output
        print("Continuing...")

    def pause_execution(self):
        # Reset the event
        continue_event.clear()

        # Create the button
        button = widgets.Button(description="Continue")
        button.on_click(self.on_button_click)
        display(button)

        # Wait for the event to be set by the button click
        continue_event.wait()
