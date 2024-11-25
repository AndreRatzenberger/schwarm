"""Agent class."""

import copy
import sys
from collections import defaultdict
from typing import Any, Literal

from loguru import logger

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.core.logging import log_function_call, setup_logging
from schwarm.core.tools import ToolHandler
from schwarm.events.event import EventType
from schwarm.models.event import create_event, create_full_event
from schwarm.models.message import Message
from schwarm.models.provider_context import ProviderContextModel
from schwarm.models.types import Agent, Response
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProviderConfig
from schwarm.provider.provider_manager import ProviderManager
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter
from schwarm.telemetry.sqlite_telemetry_exporter import SqliteTelemetryExporter
from schwarm.telemetry.telemetry_manager import TelemetryManager
from schwarm.utils.function import function_to_json
from schwarm.utils.settings import APP_SETTINGS

logger.add(
    f"{APP_SETTINGS.DATA_FOLDER}/logs/debug.log",
    format="{time} {level} {message}",
    level="DEBUG",
    rotation="10 MB",
)


class Schwarm:
    """Agent orchestrator class."""

    def __init__(
        self, agent_list: list[Agent] = [], telemetry_exporters: list[TelemetryExporter] = [], server_mode: bool = False
    ):
        """Initialize the orchestrator."""
        logger.remove()
        self._default_handler = logger.add(sys.stderr, level="DEBUG")

        self._agents = agent_list
        if telemetry_exporters:
            self._telemetry_manager = TelemetryManager(telemetry_exporters, enabled_providers=["all"])
        else:
            self._telemetry_manager = TelemetryManager([SqliteTelemetryExporter()], enabled_providers=["all"])
        self._provider_manager = ProviderManager(telemetry_manager=self._telemetry_manager)

        logger.info("Schwarm instance initialized")
        if server_mode:
            logger.info("Server mode enabled")
            input("Press Enter to continue...")

    def register_agent(self, agent: Agent):
        """Register an agent."""
        if any(a.name == agent.name for a in self._agents):
            logger.warning(f"Agent with name {agent.name} already exists.")
            return
        self._agents.append(agent)
        logger.info(f"Agent {agent.name} registered successfully.")

    def chat(
        self,
        messages: list[Message],
        context_variables: dict[str, Any],
        model_override: str,
    ) -> Message | None:
        """Chat with an agent (method implementation pending)."""
        pass

    @log_function_call(log_level="debug")
    def quickstart(
        self,
        agent: Agent,
        input_text: str = "",
        context_variables: dict[str, Any] | None = None,
        model_override: str = "",
        mode: Literal["auto", "interactive"] = "interactive",
    ) -> Response:
        """Run a single agent input."""
        return self.run(
            agent,
            messages=[Message(role="user", content=input_text)],
            context_variables=context_variables or {},
            model_override=model_override,
            max_turns=100,
            execute_tools=True,
            show_logs=True,
        )

    @log_function_call(log_level="debug")
    def run(
        self,
        agent: Agent,
        messages: list[Message],
        context_variables: dict[str, Any],
        model_override: str | None = None,
        max_turns: int = 10,
        execute_tools: bool = True,
        show_logs: bool = True,
    ) -> Response:
        """Run the agent through a conversation."""
        setup_logging(is_logging_enabled=show_logs, log_level="trace")
        self._provider_context = ProviderContextModel()
        with self._telemetry_manager.global_tracer.start_as_current_span(f"SCHWARM_START") as span:
            while True:
                with self._telemetry_manager.global_tracer.start_as_current_span(f"{agent.name}") as span:
                    span.set_attribute("agent_id", agent.name)
                    self._setup_context(agent, messages, context_variables, max_turns)
                    self._trigger_event(EventType.START_TURN)
                    logger.info(f"Processing turn {self._provider_context.current_turn}/{max_turns}")
                    self._process_turn(agent, context_variables, model_override, execute_tools)
                    self._provider_context.current_turn += 1
                    if not self._can_continue_conversation():
                        break
                    else:
                        messages = self._provider_context.message_history
                        agent = self._provider_context.current_agent
                        context_variables = self._provider_context.context_variables
                        max_turns = self._provider_context.max_turns

            logger.info(f"Agent run completed after {self._provider_context.current_turn} turns")
            self._restore_logging(show_logs)

            return Response(
                messages=self._provider_context.message_history[len(messages) :],
                agent=self._provider_context.current_agent,
                context_variables=self._provider_context.context_variables,
            )

    def create_provider_configs(self, agent: Agent):
        """Create provider configurations for an agent."""
        for config in agent.configs:
            if isinstance(config, BaseProviderConfig):
                provider = self._provider_manager.create_provider(agent.name, config)
                agent.provider_names.append(provider.provider_name)
            if isinstance(config, TelemetryConfig):
                self._telemetry_manager.add_agent(agent.name, config)

    def _setup_context(
        self,
        agent: Agent,
        messages: list[Message],
        context_variables: dict[str, Any],
        max_turns: int,
    ):
        """Initialize the provider context."""
        if self._provider_context.current_turn == 0:
            self._provider_context = ProviderContextModel()
            self._provider_context.current_turn = 0
            self._provider_context.available_agents = [agent]
            self._provider_context.available_tools = agent.functions
            self.create_provider_configs(agent)
        else:
            if agent not in self._provider_context.available_agents:
                self._provider_context.available_agents.append(agent)
                self.create_provider_configs(agent)
            for function in agent.functions:
                if function not in self._provider_context.available_tools:
                    self._provider_context.available_tools.append(function)

        self._provider_context.max_turns = max_turns
        self._provider_context.current_agent = agent
        self._provider_context.context_variables = copy.deepcopy(context_variables)
        self._provider_context.message_history = copy.deepcopy(messages)
        self._provider_context.available_providers = self._provider_manager.get_all_provider_cfgs_as_dict()
        self._trigger_event(EventType.START)

    def _set_instructions(self, agent: Agent):
        """Set agent instructions in the context."""
        if callable(agent.instructions):
            self._provider_context.instruction_func = agent.instructions
            self._provider_context.instruction_str = agent.instructions(self._provider_context.context_variables)
        else:
            self._provider_context.instruction_func = None
            self._provider_context.instruction_str = agent.instructions

    def _can_continue_conversation(self):
        """Check if the conversation can continue."""
        return self._provider_context.current_turn < self._provider_context.max_turns

    def _process_turn(
        self, agent: Agent, context_variables: dict[str, Any], model_override: str | None, execute_tools: bool
    ):
        """Process a single turn in the conversation."""
        completion = self._complete_agent_request(agent, context_variables, model_override)
        self._provider_context.current_message = completion
        self._provider_context.message_history.append(completion)

        self._trigger_event(EventType.POST_MESSAGE_COMPLETION)

        if not completion.tool_calls or not execute_tools:
            logger.info("No tools to execute or tool execution disabled")
            return

        self._trigger_event(EventType.TOOL_EXECUTION)

        partial_response = ToolHandler().handle_tool_calls(
            current_agent=agent.name,
            tool_calls=completion.tool_calls,
            functions=agent.functions,
            context_variables=context_variables,
        )

        self._provider_context.message_history.extend(partial_response.messages)
        self._provider_context.context_variables.update(partial_response.context_variables)
        self._trigger_event(EventType.POST_TOOL_EXECUTION)
        if partial_response.agent and partial_response.agent != agent:
            logger.info(f"Agent handoff: {agent.name} -> {partial_response.agent.name}")
            self._provider_context.current_agent = partial_response.agent
            self._provider_context.previous_agent = agent
            self._trigger_event(EventType.HANDOFF)

    def _restore_logging(self, show_logs: bool):
        """Restore logging settings if modified."""
        if not show_logs:
            self._default_handler = logger.add(sys.stderr, level="DEBUG")

    @log_function_call(log_level="DEBUG")
    def _complete_agent_request(self, agent: Agent, context_variables: dict[str, Any], override_model: str) -> Message:
        """Complete an agent request."""
        context_variables = defaultdict(str, context_variables)

        self._set_instructions(agent)
        self._trigger_event(EventType.INSTRUCT)

        system_msg = Message(role="system", content=self._provider_context.instruction_str)
        messages = [system_msg, *self._provider_context.message_history]

        tools = [function_to_json(f) for f in agent.functions]
        self._filter_context_vars_from_tools(tools)
        self._trigger_event(EventType.MESSAGE_COMPLETION)
        provider = self._provider_manager.get_first_llm_provider(agent.name)
        if isinstance(provider, BaseLLMProvider):
            result = provider.complete(
                messages,
                override_model=override_model,
                tools=tools,
                tool_choice=str(agent.tool_choice),
                parallel_tool_calls=agent.parallel_tool_calls,
            )

        return result

    def _filter_context_vars_from_tools(self, tools: list[dict]):
        """Remove context variables from tool parameters."""
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(APP_SETTINGS.CONTEXT_VARS_KEY, None)
            if APP_SETTINGS.CONTEXT_VARS_KEY in params["required"]:
                params["required"].remove(APP_SETTINGS.CONTEXT_VARS_KEY)

    def _trigger_event(self, event_type: EventType):
        """Trigger a specific event."""
        logger.debug(f"Event triggered: {event_type}")

        if self._telemetry_manager:
            event = create_event(self._provider_context, event_type)
            if event:
                self._telemetry_manager.send_trace(event)
        if self._provider_context:
            event = create_full_event(self._provider_context, event_type)
            if event:
                self._provider_manager.trigger_event(event)
