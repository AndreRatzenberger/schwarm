"""Debug provider for displaying and logging system information."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from rich.console import Console
from rich.markdown import Markdown

from schwarm.core.logging import truncate_string
from schwarm.models.types import Agent, Result
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.budget_provider import BudgetProvider
from schwarm.provider.models.debug_provider_config import DebugProviderConfig
from schwarm.utils.settings import APP_SETTINGS

console = Console()


class DebugProvider(BaseEventHandleProvider):
    """Debug provider that handles display and logging functionality.

    This provider replaces the DisplayService, handling all display and logging
    through the event system. It shows and logs:
    - Agent instructions
    - Function calls and results
    - Budget information
    - General debug information
    """

    config: DebugProviderConfig

    def handle_start(self) -> None:
        """Handle agent start by initializing logging and showing instructions."""
        if self.config.save_logs:
            self._ensure_log_directory()
            self._delete_logs()

        if not self.context:
            logger.warning("No context available for debug provider")
            return

        # Show initial instructions
        instructions = (
            self.context.current_agent.instructions(self.context.context_variables)
            if callable(self.context.current_agent.instructions)
            else self.context.current_agent.instructions
        )
        self._show_instructions(self.context.current_agent.name, instructions)

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
        log_path = os.path.join(APP_SETTINGS.DATA_FOLDER, "logs")
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def _delete_logs(self) -> None:
        """Delete all log files in the logs directory."""
        log_dir = Path(APP_SETTINGS.DATA_FOLDER) / "logs"
        if log_dir.exists():
            for file in log_dir.glob("*.log"):
                file.unlink()
            for file in log_dir.glob("*.csv"):
                file.unlink()

    def _write_to_log(self, filename: str, content: str, mode: str = "a") -> None:
        """Write content to a log file."""
        if not self.config.save_logs:
            return

        log_path = os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", filename)
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content_with_timestamp = f"Timestamp: {timestamp}\n{content}\n"

        # Write to specific log file
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(content_with_timestamp)

        # Write to combined log file
        with open(os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", "all.log"), mode, encoding="utf-8") as f:
            f.write(content_with_timestamp)

    def _show_instructions(self, agent_name: str, instructions: str) -> None:
        """Show the instructions to the user."""
        if not self.config.show_instructions:
            return

        console.line()
        console.print(Markdown(f"# 📝 Instructing 🤖 {agent_name}"), style="bold orange3")
        console.line()
        console.print(Markdown(truncate_string(instructions, self.config.max_length)), style="italic")

        # Write to instructions log
        log_content = f"Agent: {agent_name}\nInstructions:\n{instructions}\n{'=' * 50}\n"
        self._write_to_log("instructions.log", log_content)

        if self.config.instructions_wait_for_user_input:
            console.line()
            console.input("Press Enter to continue...")

    def _show_budget(self, agent: Agent) -> None:
        """Show the budget to the user."""
        if not self.config.show_budget:
            return

        console.line()
        console.print(Markdown(f"# 💰 Budget - {agent.name}"), style="bold orange3")

        budget = agent.get_provider("budget")

        console.line()
        if isinstance(budget, BudgetProvider):
            console.print(Markdown(f"**- Max Spent:** ${budget.config.max_spent:.5f}"), style="italic")
            console.print(Markdown(f"**- Max Tokens:** {budget.config.max_tokens}"), style="italic")
            console.print(Markdown(f"**- Current Spent:** ${budget.config.current_spent:.5f}"), style="italic")
            console.print(Markdown(f"**- Current Tokens:** {budget.config.current_tokens}"), style="italic")

        # Write to budget log
        if isinstance(budget, BudgetProvider):
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
        function: str = "",
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
            console.line()
            console.input("Press Enter to continue...")
