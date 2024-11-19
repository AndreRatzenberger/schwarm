"""A service to display messages to the user."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown

from schwarm.core.logging import truncate_string
from schwarm.models.display_config import DisplayConfig
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.utils.settings import APP_SETTINGS

console = Console()


class DisplayService:
    """A service to display messages to the user."""

    def __init__(self, display_config: DisplayConfig):
        """Initialize the display service."""
        self.display_config = display_config
        self._ensure_log_directory()

    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        log_path = os.path.join(APP_SETTINGS.DATA_FOLDER, "logs")
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)

    def _write_to_log(self, filename: str, content: str, mode: str = "a"):
        """Write content to a log file."""
        log_path = os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", filename)
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(content + "\n")

        log_path = os.path.join(APP_SETTINGS.DATA_FOLDER, "logs", "all.log")
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(content + "\n")

    def delete_logs(self):
        """Delete all log files in the logs directory."""
        log_dir = Path(APP_SETTINGS.DATA_FOLDER) / "logs"
        if log_dir.exists():
            for file in log_dir.glob("*.log"):
                file.unlink()
            for file in log_dir.glob("*.csv"):
                file.unlink()

    def show_instructions(self, agent_name: str, instructions: str):
        """Show the instructions to the user."""
        if not self.display_config.show_instructions:
            return
        console.line()
        console.print(Markdown(f"# 📝 Instructing 🤖 {agent_name}"), style="bold orange3")
        console.line()
        console.print(Markdown(truncate_string(instructions, self.display_config.max_length)), style="italic")

        # Write to instructions log
        log_content = f"Agent: {agent_name}\nInstructions:\n{instructions}\n{'=' * 50}\n"
        self._write_to_log("instructions.log", log_content)

        if self.display_config.instructions_wait_for_user_input:
            console.line()
            console.input("Press Enter to continue...")

    def show_budget(self, agent: Agent):
        """Show the budget to the user."""
        if not self.display_config.show_budget:
            return
        console.line()
        console.print(Markdown(f"# 💰 Budget - {agent.name}"), style="bold orange3")
        console.line()
        console.print(Markdown(f"**- Max Spent:** ${agent.budget.max_spent:.5f}"), style="italic")
        console.print(Markdown(f"**- Max Tokens:** {agent.budget.max_tokens}"), style="italic")
        console.print(Markdown(f"**- Current Spent:** ${agent.budget.current_spent:.5f}"), style="italic")
        console.print(Markdown(f"**- Current Tokens:** {agent.budget.current_tokens}"), style="italic")

        # Write to budget log
        log_content = (
            f"Agent: {agent.name}\n"
            f"Max Spent: ${agent.budget.max_spent:.5f}\n"
            f"Max Tokens: {agent.budget.max_tokens}\n"
            f"Current Spent: ${agent.budget.current_spent:.5f}\n"
            f"Current Tokens: {agent.budget.current_tokens}\n"
            f"{'=' * 50}\n"
        )
        self._write_to_log("budget.log", log_content)

    def show_budget_table(self, agents: list[Agent]):
        """Show the budget table to the user."""
        if not self.display_config.show_budget:
            return
        console.line()
        console.print(Markdown(f"# 💵Budget Table"), style="bold orange3")
        console.line()
        table = ""
        table += f"**Agent** | **Max Spent** | **Max Tokens** | **Current Spent** | **Current Tokens**\n"
        table += "--- | --- | --- | --- | ---\n"

        # Write to budget log
        log_content = "Budget Table\n"
        log_content += "Agent | Max Spent | Max Tokens | Current Spent | Current Tokens\n"
        log_content += "--- | --- | --- | --- | ---\n"

        spent_sum = 0.0
        token_sum = 0
        for agent in agents:
            table_row = f"{agent.name} | ${agent.budget.max_spent:.5f} | {agent.budget.max_tokens} | ${agent.budget.current_spent:.5f} | {agent.budget.current_tokens}"
            table += table_row + "\n"
            log_content += table_row + "\n"
            spent_sum += agent.budget.current_spent
            token_sum += agent.budget.current_tokens

        table += "||||\n"
        table += f" |  |  | **TOTAL** | ${spent_sum:.5f} | {token_sum}\n"
        console.print(Markdown(table))
        log_content += f"{'=' * 50}\n"
        self._write_to_log("budget_table.log", log_content)

    def show_function(
        self,
        context_variables: ContextVariables | None,
        sender: str = "",
        receiver: str | None = None,
        function: str = "",
        parameters: dict[str, Any] = {},
        result: Result | None = None,
    ):
        """Show the function and parameters to the user."""
        if not self.display_config.show_function_calls:
            return
        console.line()

        if receiver:
            console.print(Markdown(f"# 🤖 {sender} -> ⚡ {function} -> 🤖 {receiver}"), style="bold green")
            log_header = f"Sender: {sender}\nFunction: {function}\nReceiver: {receiver}\n"
        else:
            console.print(Markdown(f"# 🤖 {sender} -> ⚡ {function}"), style="bold green")
            log_header = f"Sender: {sender}\nFunction: {function}\n"

        console.print(Markdown(f"## Parameters"), style="bold green")

        # Prepare log content
        log_content = log_header + "Parameters:\n"
        # pprint(parameters, expand_all=True, max_string=500)
        for key, value in parameters.items():
            if key == APP_SETTINGS.CONTEXT_VARS_KEY:
                continue
            # pprint((key, value), expand_all=True, max_string=500)
            console.line()
            console.print(Markdown(f"**- {key}**"), style="bold italic")
            console.line()
            console.print(Markdown(f"   {truncate_string(str(value), self.display_config.max_length)}"), style="italic")
            log_content += f"   {key}: {value}\n"

        if result:
            console.rule()
            console.print(Markdown(f"## Result"), style="bold green")
            log_content += f"{'-' * 20}\n"
            log_content = log_content + "Result:\n"
            dict_result = result.model_dump()
            # pprint(dict_result, expand_all=True, max_string=500)
            for key, value in dict_result.items():
                console.line()
                console.print(Markdown(f"**- {key}**"), style="bold italic")
                console.line()
                # pprint(f"  {truncate_string(str(value), self.display_config.max_length)}")
                console.print(
                    Markdown(f"   {truncate_string(str(value), self.display_config.max_length)}"), style="italic"
                )
                log_content += f"   {key}: {value}\n"

        if self.display_config.function_calls_print_context_variables:
            console.rule()
            console.print(Markdown(f"**- Context Variables**"), style="bold italic")
            log_content += f"{'-' * 20}\n"
            console.print(truncate_string(str(context_variables), self.display_config.max_length))
            if context_variables:
                log_content += f"Context Variables: {context_variables}\n"

        log_content += f"{'=' * 50}\n"
        self._write_to_log("functions.log", log_content)

        if self.display_config.function_calls_wait_for_user_input:
            console.line()
            console.input("Press Enter to continue...")
