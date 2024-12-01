"""Core orchestrator for agent conversations."""

import json
import logging
from typing import Any

from .agent import Agent
from .llm import LLMProvider
from .types import ConversationResult, Message


class Orchestrator:
    """Orchestrates conversations between agents and tools."""

    def __init__(self):
        """Initialize the orchestrator."""
        self.logger = logging.getLogger(__name__)

    def _execute_tool(self, agent: Agent, tool_calls: list[dict[str, Any]], context: dict[str, Any]) -> list[Message]:
        """Execute tool calls and return their results as messages."""
        tool_messages = []

        for tool_call in tool_calls:
            try:
                name = tool_call["name"]
                args = tool_call.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"input": args}

                # Execute the tool
                result = agent.execute_tool(name, **args)

                # Convert result to string if needed
                if not isinstance(result, str):
                    result = str(result)

                # Create tool response message
                tool_messages.append(Message(content=result, role="tool"))

            except Exception as e:
                error_msg = f"Error executing tool {name}: {e!s}"
                self.logger.error(error_msg)
                tool_messages.append(Message(content=error_msg, role="tool"))

        return tool_messages

    def run_conversation(
        self, agent: Agent, messages: list[Message], context: dict[str, Any] | None = None, max_turns: int = 10
    ) -> ConversationResult:
        """Run a conversation with an agent."""
        context = context or {}
        conversation = list(messages)  # Copy initial messages
        current_turn = 0

        # Create LLM provider for the agent
        llm = LLMProvider(model=agent.config.model, api_key=agent.config.api_key)

        # Add system message
        system_msg = agent.get_system_message(context)
        conversation.insert(0, system_msg)

        while current_turn < max_turns:
            # Get completion from LLM
            tools = agent.get_tool_descriptions()
            result = llm.complete(messages=conversation, tools=tools, temperature=agent.config.temperature)

            # Add assistant's message to conversation
            conversation.append(result.message)

            # Check for tool calls
            if result.message.tool_calls:
                # Execute tools and get results
                tool_messages = self._execute_tool(agent=agent, tool_calls=result.message.tool_calls, context=context)

                # Add tool results to conversation
                conversation.extend(tool_messages)
            else:
                # No tool calls, end conversation
                break

            current_turn += 1

        return ConversationResult(
            messages=conversation[1:],  # Exclude system message
            context=context,
        )

    def run_single_turn(self, agent: Agent, message: str, context: dict[str, Any] | None = None) -> ConversationResult:
        """Run a single turn conversation with an agent."""
        return self.run_conversation(agent=agent, messages=[Message(content=message)], context=context, max_turns=1)
