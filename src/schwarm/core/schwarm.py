"""Agent class."""

import copy
import sys
from collections import defaultdict
from typing import Any, Literal

from loguru import logger

from schwarm.core.logging import log_function_call, setup_logging
from schwarm.core.tools import ToolHandler
from schwarm.events import EventType
from schwarm.models.message import Message
from schwarm.models.types import Agent, Response
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.provider_context import ProviderContext
from schwarm.provider.provider_manager import ProviderManager
from schwarm.utils.function import function_to_json
from schwarm.utils.settings import APP_SETTINGS

ContextVariables = dict[str, Any]
logger.add(
    APP_SETTINGS.DATA_FOLDER + "/logs/debug.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB"
)


class Schwarm:
    """Agent class."""

    def __init__(self, agent_list: list[Agent] = []):
        """Initialize the orchestrator."""
        # Remove default handler to control logging output
        logger.remove()
        # Add a default handler that we can control
        self._default_handler = logger.add(sys.stderr, level="DEBUG")
        self._agents: list[Agent] = agent_list
        self._manager = ProviderManager()
        logger.info("Schwarm instance initialized")

    def register_agent(self, agent: Agent):
        """Register an agent."""
        if any(existing_agent.name == agent.name for existing_agent in self._agents):
            logger.warning(f"Agent with name {agent.name} already exists.")
            return
        self._agents.append(agent)
        logger.info(f"Agent {agent.name} registered successfully.")

    def chat(
        self,
        messages: list[Message],
        context_variables: ContextVariables,
        model_override: str,
    ) -> Message | None:
        """Chat with the agent with no handoff.

        Args:
            messages (list[Message]): List of messages.
            context_variables (ContextVariables): Contextual variables for the chat.
            model_override (str): Model to override the default one.

        Returns:
            Message | None: The response message or None if no response.
        """
        pass

    @log_function_call(log_level="debug")
    def quickstart(
        self,
        agent: Agent,
        input_text: str = "",
        context_variables: ContextVariables | None = None,
        model_override: str = "",
        mode: Literal["auto", "interactive"] = "interactive",
    ) -> Response:
        """Run the agent with a single input text."""
        if context_variables is None:
            context_variables = {}
        if mode == "auto":
            return self.run(
                agent,
                messages=[Message(role="user", content=input_text)],
                context_variables=context_variables,
                model_override=model_override,
                max_turns=100,
                execute_tools=True,
                show_logs=True,
            )
        else:
            return self.run(
                agent,
                messages=[Message(role="user", content=input_text)],
                context_variables=context_variables,
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
        context_variables: ContextVariables,
        model_override: str | None = None,
        max_turns: int = 10,
        execute_tools: bool = True,
        show_logs: bool = True,
    ) -> Response:
        """Run the agent.

        Args:
            agent: The agent to run.
            messages: List of messages.
            context_variables: Contextual variables for the chat.
            model_override: Model to override the default one.
            max_turns: Maximum number of turns in the conversation.
            execute_tools: Whether to execute tools.
            show_logs: Whether to show loguru logs in the console.

        Returns:
            Response object containing messages, agent, and context variables.
        """
        setup_logging(is_logging_enabled=show_logs, log_level="trace")
        # Context Store
        self._provider_context = ProviderContext()

        self._provider_context.max_turns = max_turns

        # initialize the active agent and its providers
        active_agent = agent
        self._provider_context.current_agent = active_agent
        self._provider_context.available_agents.append(active_agent)
        self._provider_context.available_tools = active_agent.functions

        for config in agent.provider_configurations:
            if config.enabled:
                self._manager.create_provider_and_register(agent.name, config)

        self._provider_context.available_providers = self._manager.get_all_provider_cfgs_as_dict()

        # Copy the context variables and history for the context store
        self._provider_context.context_variables = copy.deepcopy(context_variables)
        self._provider_context.message_history = copy.deepcopy(messages)
        init_len = len(messages)

        self._provider_context.trigger_event(EventType.INSTRUCT)

        if callable(active_agent.instructions):
            self._provider_context.instruction_func = active_agent.instructions
            self._provider_context.instruction_str = active_agent.instructions(context_variables)
        else:
            self._provider_context.instruction_func = None
            self._provider_context.instruction_str = active_agent.instructions

        self._provider_context.trigger_event(EventType.POST_INSTRUCT)

        while len(self._provider_context.message_history) - init_len < max_turns and active_agent:
            current_turn = len(self._provider_context.message_history) - init_len + 1
            logger.info(f"Processing turn {current_turn}/{max_turns}")

            self._manager.trigger_event(EventType.MESSAGE_COMPLETION, self._provider_context)
            completion = self._complete_agent_request(
                agent=active_agent,
                context_variables=self._provider_context.context_variables,
                history=self._provider_context.message_history,
                override_model=model_override,
            )
            self._manager.trigger_event(EventType.POST_MESSAGE_COMPLETION, self._provider_context)
            completion.sender = active_agent.name
            logger.debug(f"Completion received from {completion.sender}")

            self._provider_context.message_history.append(completion)

            if not completion.tool_calls or not execute_tools:
                logger.info("No tools to execute or tool execution disabled")
                break

            logger.info(f"Executing {len(completion.tool_calls)} tool calls")
            partial_response = ToolHandler().handle_tool_calls(
                current_agent=active_agent.name,
                tool_calls=completion.tool_calls,
                functions=active_agent.functions,
                context_variables=context_variables,
            )

            self._provider_context.message_history.extend(partial_response.messages)
            self._provider_context.context_variables.update(partial_response.context_variables)

            if partial_response.agent and partial_response.agent != active_agent:
                logger.info(f"Agent handoff: {active_agent.name} -> {partial_response.agent.name}")
                self._provider_context.current_agent = partial_response.agent

        logger.info(f"Agent run completed after {current_turn} turns")

        # Restore logging if it was disabled
        if not show_logs and not self._logging_enabled:
            self._default_handler = logger.add(sys.stderr, level="DEBUG")
            self._logging_enabled = True
            logger.info("Console logging restored")

        return Response(
            messages=self._provider_context.message_history[init_len:],
            agent=self._provider_context.current_agent,
            context_variables=self._provider_context.context_variables,
        )

    @log_function_call(log_level="DEBUG")
    def _complete_agent_request(
        self, agent: Agent, context_variables: ContextVariables, history: list[Message], override_model: str
    ) -> Message:
        """Complete an agent request."""
        context_variables = defaultdict(str, context_variables)

        if callable(agent.instructions):
            self._provider_context.instruction_func = agent.instructions
            self._provider_context.instruction_str = agent.instructions(context_variables)
        else:
            self._provider_context.instruction_func = None
            self._provider_context.instruction_str = agent.instructions

        self._provider_context.current_message = history[-1]
        self._provider_context.context_variables = context_variables
        self._provider_context.current_agent = agent
        self._manager.trigger_event(EventType.INSTRUCT, self._provider_context)

        # Get the agent instructions to set system prompt
        instructions = agent.instructions(context_variables) if callable(agent.instructions) else agent.instructions

        self._provider_context.instruction_str = instructions
        self._manager.trigger_event(EventType.POST_INSTRUCT, self._provider_context)

        logger.debug(f"Generated instructions for agent '{agent.name}'")

        # Set the system prompt and add history
        system_msg = Message(role="system", content=instructions)
        messages = [system_msg, *history]
        logger.debug(f"Prepared {len(messages)} messages for completion")

        # tools to json
        tools = [function_to_json(f) for f in agent.functions]
        logger.debug(f"Prepared {len(tools)} tools for completion")

        # Remove context variables from tool parameters
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(APP_SETTINGS.CONTEXT_VARS_KEY, None)
            if APP_SETTINGS.CONTEXT_VARS_KEY in params["required"]:
                params["required"].remove(APP_SETTINGS.CONTEXT_VARS_KEY)

        logger.info(f"Requesting completion from provider with model override: {override_model}")

        provider = self._manager.get_first_llm_provider(agent.name)
        if isinstance(provider, BaseLLMProvider):
            result = provider.complete(
                messages,
                override_model=override_model,
                tools=tools,
                tool_choice=str(agent.tool_choice),
                parallel_tool_calls=agent.parallel_tool_calls,
            )

        logger.debug("Completion received from provider")

        return result
