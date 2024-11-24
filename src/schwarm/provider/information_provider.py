"""Debug provider for displaying and logging system information."""

import csv
import threading
from collections.abc import Callable
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
from schwarm.events.event import Event, EventType
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContextModel
from schwarm.models.result import Result
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.utils.settings import APP_SETTINGS

console = Console()


class InformationConfig(BaseEventHandleProviderConfig):
    """Configuration for the debug provider."""

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
    max_length: int = Field(default=-1, description="Maximum length for displayed text (-1 for no limit)")
    save_logs: bool = Field(default=True, description="Whether to save logs to files")
    provider_id: str = Field(default="debug", description="Provider ID")
    save_budget: bool = Field(default=True, description="Whether to save budget to CSV")
    show_budget: bool = Field(default=False, description="Whether to show budget in display")
    effect_on_exceed: Literal["warning", "error", "nothing"] = Field(
        default="warning", description="Action on limit exceed"
    )
    max_spent: float = Field(default=10.0, description="Maximum allowed spend")
    max_tokens: int = Field(default=10000, description="Maximum allowed tokens")
    current_spent: float = Field(default=0.0, description="Current amount spent")
    current_tokens: int = Field(default=0, description="Current tokens used")


class InformationProvider(BaseEventHandleProvider):
    """Debug provider that handles display and logging functionality."""

    config: InformationConfig
    _provider_id: str = Field(default="debug", description="Provider ID")
    _log_dir: Path = Path(APP_SETTINGS.DATA_FOLDER) / "logs"

    def initialize(self) -> None:
        """Initialize the debug provider."""
        self._ensure_log_directory()

    def handle_event(self, event: Event) -> ProviderContextModel | None:
        """Handle events by showing relevant information."""
        if not event.context:
            logger.warning("No context available for debug provider")
            return None

        self.context = event.context
        handlers: dict[EventType, Callable] = {
            EventType.START: self._handle_start,
            EventType.INSTRUCT: self._handle_instruct,
            EventType.POST_MESSAGE_COMPLETION: self._handle_message_completion,
            EventType.TOOL_EXECUTION: self._handle_tool_execution,
            EventType.POST_TOOL_EXECUTION: self._handle_post_tool_execution,
            EventType.HANDOFF: self._handle_handoff,
        }

        handler = handlers.get(event.type)
        if handler:
            return handler(event.context)
        return None

    def _handle_start(self, context: ProviderContextModel) -> None:
        """Handle agent start."""
        if self.config.save_logs:
            self._ensure_log_directory()

    def _handle_instruct(self, context: ProviderContextModel) -> None:
        """Handle instruction events."""
        if not self.config.show_instructions:
            return

        agent_name = context.current_agent.name if context.current_agent else "Unknown"
        instructions = context.instruction_str if isinstance(context.instruction_str, str) else ""

        self._display_section(
            title=f"📝 Instructing 🤖 {agent_name}",
            content=instructions,
            style="italic",
            log_file="instructions.log",
            log_prefix=f"Agent: {agent_name}\nInstructions:\n",
            wait_for_input=self.config.instructions_wait_for_user_input,
        )

    def _handle_message_completion(self, context: ProviderContextModel) -> dict:
        """Handle message completion events."""
        if not self.context or not self.context.message_history:
            return {}

        latest_message = self.context.message_history[-1]
        if not isinstance(latest_message, Message) or not latest_message.info:
            return {}

        return self._update_budget(latest_message)

    def _handle_tool_execution(self, context: ProviderContextModel) -> None:
        """Handle tool execution events."""
        if not self.context or not self.context.message_history:
            return

        latest_message = self.context.message_history[-1]
        if not latest_message.tool_calls:
            return

        for tool_call in latest_message.tool_calls:
            function_name = tool_call.get("function", {}).get("name")
            function_args = tool_call.get("function", {}).get("arguments")
            self._show_function_details(
                sender=self.context.current_agent.name,
                function=function_name,
                parameters=function_args,
            )

    def _handle_post_tool_execution(self, context: ProviderContextModel) -> None:
        """Handle post tool execution events."""
        if not self.context or not self.context.message_history:
            return

        result_messages = [msg for msg in self.context.message_history[-2:] if msg.role == "tool"]
        for msg in result_messages:
            if "result" in msg.additional_info:
                self._show_function_details(
                    sender=self.context.current_agent.name,
                    function="tool_result",
                    result=msg.additional_info["result"],
                )

    def _handle_handoff(self, context: ProviderContextModel) -> Any:
        """Handle agent handoff events."""
        next_agent = context.current_agent
        if not next_agent or not self.context:
            return next_agent

        for provider in next_agent.provider_configurations:
            if isinstance(provider, InformationConfig):
                provider.current_spent = self.config.current_spent
                provider.current_tokens = self.config.current_tokens
                logger.debug(
                    f"Transferred budget state to {next_agent.name}: "
                    f"spent=${self.config.current_spent:.2f}, "
                    f"tokens={self.config.current_tokens}"
                )
                break

        return next_agent

    def _ensure_log_directory(self) -> None:
        """Ensure the log directory exists."""
        self._log_dir.mkdir(parents=True, exist_ok=True)

    def _write_to_log(self, filename: str, content: str, mode: str = "a") -> None:
        """Write content to log files."""
        if not self.config.save_logs:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content_with_timestamp = f"Timestamp: {timestamp}\n{content}\n"

        # Write to specific log file
        log_path = self._log_dir / filename
        with log_path.open(mode=mode, encoding="utf-8") as f:
            f.write(content_with_timestamp)

        # Write to combined log
        all_log_path = self._log_dir / "all.log"
        with all_log_path.open(mode=mode, encoding="utf-8") as f:
            f.write(content_with_timestamp)

    def _update_budget(self, message: Message) -> dict[str, Any]:
        """Update budget tracking."""
        if not message.info:
            return {}

        self.config.current_spent += message.info.completion_cost
        self.config.current_tokens += message.info.token_counter

        result = {"current_spent": self.config.current_spent, "current_tokens": self.config.current_tokens}

        if self.config.save_budget:
            self._save_budget_to_csv()

        self._check_budget_limits()
        return result

    def _save_budget_to_csv(self) -> None:
        """Save current budget state to CSV."""
        filepath = self._log_dir / f"{self.context.current_agent.name}_budget.csv"
        file_exists = filepath.exists()

        with filepath.open(mode="a", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "current_spent", "max_spent", "current_tokens", "max_tokens"])
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    self.config.current_spent,
                    self.config.max_spent,
                    self.config.current_tokens,
                    self.config.max_tokens,
                ]
            )

    def _check_budget_limits(self) -> None:
        """Check if budget or token limits are exceeded."""
        if self.config.current_spent > self.config.max_spent:
            self._handle_limit_exceed(
                f"Budget exceeded: current_spent={self.config.current_spent}, max_spent={self.config.max_spent}"
            )

        if self.config.current_tokens > self.config.max_tokens:
            self._handle_limit_exceed(
                f"Token limit exceeded: current_tokens={self.config.current_tokens}, max_tokens={self.config.max_tokens}"
            )

    def _handle_limit_exceed(self, message: str) -> None:
        """Handle exceeded limits based on configuration."""
        if self.config.effect_on_exceed == "warning":
            logger.warning(message)
        elif self.config.effect_on_exceed == "error":
            logger.error(message)
            raise ValueError(message)

    def _display_section(
        self,
        title: str,
        content: str,
        style: str = "italic",
        log_file: str | None = None,
        log_prefix: str = "",
        wait_for_input: bool = False,
    ) -> None:
        """Display a section with consistent formatting."""
        console.line()
        console.print(Markdown(f"# {title}"), style="bold orange3")
        console.line()
        console.print(Markdown(truncate_string(content, self.config.max_length)), style=style)

        if log_file and log_prefix:
            log_content = f"{log_prefix}{content}\n{'=' * 50}\n"
            self._write_to_log(log_file, log_content)

        if wait_for_input:
            self._wait_for_user_input()

    def _show_function_details(
        self,
        sender: str,
        function: str | None = None,
        parameters: dict[str, Any] | Any | None = None,
        result: Result | None = None,
    ) -> None:
        """Show function details with consistent formatting."""
        if not self.config.show_function_calls:
            return

        title = f"🤖 {sender} -> ⚡ {function}"
        log_content = [f"Sender: {sender}", f"Function: {function}"]

        if parameters:
            log_content.extend(self._format_parameters(parameters))

        if result:
            log_content.extend(self._format_result(result))

        if self.config.function_calls_print_context_variables and self.context:
            log_content.extend(self._format_context_variables())

        self._display_section(
            title=title,
            content="\n".join(log_content),
            log_file="functions.log",
            wait_for_input=self.config.function_calls_wait_for_user_input,
        )

    def _format_parameters(self, parameters: dict[str, Any] | Any) -> list[str]:
        """Format parameters for display."""
        if not parameters:
            return []

        result = ["## Parameters"]
        if isinstance(parameters, dict):
            for key, value in parameters.items():
                if key == APP_SETTINGS.CONTEXT_VARS_KEY:
                    continue
                result.extend([f"**- {key}**", f"   {truncate_string(str(value), self.config.max_length)}"])
        else:
            result.append(truncate_string(str(parameters), self.config.max_length))
        return result

    def _format_result(self, result: Result) -> list[str]:
        """Format result for display."""
        formatted = ["## Result"]
        dict_result = result.model_dump()
        for key, value in dict_result.items():
            formatted.extend([f"**- {key}**", f"   {truncate_string(str(value), self.config.max_length)}"])
        return formatted

    def _format_context_variables(self) -> list[str]:
        """Format context variables for display."""
        return ["**- Context Variables**", truncate_string(str(self.context.context_variables), self.config.max_length)]

    def _wait_for_user_input(self) -> None:
        """Wait for user input based on application frame."""
        if self.config.application_frame == "cli":
            console.line()
            console.input("Press Enter to continue...")
        else:
            self._jupyter_pause_execution()

    def _jupyter_pause_execution(self) -> None:
        """Handle pausing execution in Jupyter environment."""
        continue_event = threading.Event()
        continue_event.clear()

        def on_button_click(b):
            continue_event.set()
            clear_output(wait=True)
            print("Continuing...")

        button = widgets.Button(description="Continue")
        button.on_click(on_button_click)
        display(button)
        continue_event.wait()
