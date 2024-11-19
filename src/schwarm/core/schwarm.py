"""Agent orchestration and execution engine."""

import copy
import sys
from typing import Any, Literal

from loguru import logger

from schwarm.core.logging import log_function_call
from schwarm.core.tools import ToolHandler
from schwarm.models.display_config import DisplayConfig
from schwarm.models.message import Message
from schwarm.models.types import Agent, Response
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.utils.function import function_to_json
from schwarm.utils.settings import APP_SETTINGS

logger.add(
    APP_SETTINGS.DATA_FOLDER + "/logs/debug.log", format="{time} {level} {message}", level="DEBUG", rotation="10 MB"
)


class Schwarm:
    """Agent orchestration and execution engine."""

    def __init__(self, agent_list: list[Agent] = []):
        """Initialize the orchestrator."""
        # Remove default handler to control logging output
        logger.remove()
        # Add a default handler that we can control
        self._default_handler = logger.add(sys.stderr, level="DEBUG")
        self._logging_enabled = True
        self._agents: list[Agent] = agent_list

        logger.info("Schwarm instance initialized")

    def register_agent(self, agent: Agent):
        """Register an agent."""
        if any(existing_agent.name == agent.name for existing_agent in self._agents):
            logger.warning(f"Agent with name {agent.name} already exists.")
            return
        self._agents.append(agent)
        logger.info(f"Agent {agent.name} registered successfully.")

    @log_function_call(log_level="debug")
    def quickstart(
        self,
        agent: Agent,
        input_text: str,
        context_variables: dict[str, Any] | None = None,
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
                display_config=DisplayConfig(
                    show_function_calls=True,
                    function_calls_wait_for_user_input=False,
                    show_instructions=True,
                    instructions_wait_for_user_input=False,
                    max_length=-1,
                ),
                show_logs=False,
            )
        else:
            return self.run(
                agent,
                messages=[Message(role="user", content=input_text)],
                context_variables=context_variables,
                model_override=model_override,
                max_turns=100,
                execute_tools=True,
                display_config=DisplayConfig(
                    show_function_calls=True,
                    function_calls_wait_for_user_input=True,
                    show_instructions=True,
                    instructions_wait_for_user_input=True,
                    max_length=-1,
                ),
                show_logs=False,
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
        display_config: DisplayConfig | None = None,
        show_logs: bool = True,
    ) -> Response:
        """Run the agent with provider-based capabilities.

        This method orchestrates the agent's execution flow, managing providers and their
        lifecycle events while processing messages and tools.

        Args:
            agent: The agent to run
            messages: List of conversation messages
            context_variables: Variables available to the agent
            model_override: Optional model override
            max_turns: Maximum conversation turns
            execute_tools: Whether to execute tools
            display_config: Display configuration
            show_logs: Whether to show logs

        Returns:
            Response containing messages, final agent state and context
        """
        # Configure logging
        self._configure_logging(show_logs)

        # Initialize execution state
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        logger.info(f"Starting agent run with {active_agent.name}, max_turns: {max_turns}")
        logger.debug(f"Initial context variables: {context_variables}")
        logger.debug(f"Initial message history length: {init_len}")

        # Initialize providers for the agent
        active_agent.initialize_providers()

        # Trigger provider start events
        self._trigger_provider_event(active_agent, "on_start")

        # Main execution loop
        while len(history) - init_len < max_turns and active_agent:
            current_turn = len(history) - init_len + 1
            logger.info(f"Processing turn {current_turn}/{max_turns}")

            # Generate completion
            completion = self._complete_agent_request(
                agent=active_agent, context_variables=context_variables, history=history, override_model=model_override
            )

            completion.sender = active_agent.name
            logger.debug(f"Completion received from {completion.sender}")

            history.append(completion)

            # Handle tool execution if needed
            if completion.tool_calls and execute_tools:
                logger.info(f"Executing {len(completion.tool_calls)} tool calls")

                # Trigger pre-tool execution events
                self._trigger_provider_event(active_agent, "on_tool_execution")

                partial_response = ToolHandler(display_config).handle_tool_calls(
                    current_agent=active_agent.name,
                    tool_calls=completion.tool_calls,
                    functions=active_agent.functions,
                    context_variables=context_variables,
                )

                # Update state with tool results
                history.extend(partial_response.messages)
                context_variables.update(partial_response.context_variables)

                # Trigger post-tool execution events
                self._trigger_provider_event(active_agent, "on_post_tool_execution")

                # Handle agent handoff if needed
                if partial_response.agent and partial_response.agent != active_agent:
                    logger.info(f"Agent handoff: {active_agent.name} -> {partial_response.agent.name}")
                    next_agent = partial_response.agent

                    # Allow providers to modify/veto handoff
                    next_agent = self._trigger_provider_event(active_agent, "on_handoff", next_agent=next_agent)
                    if next_agent:
                        active_agent = next_agent
                        # Initialize providers for new agent
                        active_agent.initialize_providers()
                        self._trigger_provider_event(active_agent, "on_start")
            else:
                logger.info("No tools to execute or tool execution disabled")
                break

        logger.info(f"Agent run completed after {len(history) - init_len} turns")

        # Restore logging if it was disabled
        if not show_logs and not self._logging_enabled:
            self._default_handler = logger.add(sys.stderr, level="DEBUG")
            self._logging_enabled = True
            logger.info("Console logging restored")

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )

    def _configure_logging(self, show_logs: bool):
        """Configure logging based on show_logs parameter."""
        if not show_logs and self._logging_enabled:
            logger.info("Disabling console logging")
            logger.remove(self._default_handler)
            self._logging_enabled = False
        elif show_logs and not self._logging_enabled:
            logger.info("Enabling console logging")
            self._default_handler = logger.add(sys.stderr, level="DEBUG")
            self._logging_enabled = True

    def _trigger_provider_event(self, agent: Agent, event_name: str, **kwargs: Any) -> Any:
        """Trigger an event on all of an agent's event handling providers.

        Args:
            agent: The agent whose providers should handle the event
            event_name: Name of the event to trigger
            **kwargs: Additional event data

        Returns:
            The result from the last provider's event handler
        """
        result = None
        for provider_config in agent.providers:
            provider = agent.get_provider(provider_config.provider_name)
            if provider and isinstance(provider, BaseEventHandleProvider):
                try:
                    result = provider.handle_event(event_name, **kwargs)
                except Exception as e:
                    logger.error(f"Error in provider {provider_config.provider_name} handling {event_name}: {e}")
        return result

    @log_function_call(log_level="DEBUG")
    def _complete_agent_request(
        self, agent: Agent, context_variables: dict[str, Any], history: list[Message], override_model: str | None = None
    ) -> Message:
        """Complete an agent request using the appropriate LLM provider.

        Args:
            agent: The agent making the request
            context_variables: Context variables
            history: Message history
            override_model: Optional model override

        Returns:
            The completion message
        """
        # Trigger pre-completion events
        self._trigger_provider_event(agent, "on_message_completion")

        # Get agent instructions
        instructions = agent.instructions(context_variables) if callable(agent.instructions) else agent.instructions
        logger.debug(f"Generated instructions for agent '{agent.name}'")

        # Prepare messages and tools
        system_msg = Message(role="system", content=instructions)
        messages = [system_msg, *history]
        logger.debug(f"Prepared {len(messages)} messages for completion")

        tools = [self._prepare_tool(f) for f in agent.functions]
        logger.debug(f"Prepared {len(tools)} tools for completion")

        # Get LLM provider and generate completion
        provider = agent.get_llm_provider()
        if not provider:
            raise ValueError("No LLM provider found for agent")

        result = provider.complete(
            messages,
            override_model=override_model,
            tools=tools,
            tool_choice=str(agent.tool_choice),
            parallel_tool_calls=agent.parallel_tool_calls,
        )

        # Trigger post-completion events
        self._trigger_provider_event(agent, "on_post_message_completion")

        logger.debug("Completion received from provider")
        return result

    def _prepare_tool(self, tool_function: Any) -> dict[str, Any]:
        """Prepare a tool function specification."""
        tool = function_to_json(tool_function)
        # Remove context variables from parameters
        params = tool["function"]["parameters"]
        params["properties"].pop(APP_SETTINGS.CONTEXT_VARS_KEY, None)
        if APP_SETTINGS.CONTEXT_VARS_KEY in params["required"]:
            params["required"].remove(APP_SETTINGS.CONTEXT_VARS_KEY)
        return tool
