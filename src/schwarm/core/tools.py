"""Contains the ToolHandler class for handling tool calls."""

import json
from typing import Any

from litellm import ChatCompletionMessageToolCall

from schwarm.models.types import AgentFunction, Message, Response, Result

# Constants
CONTEXT_VARS_KEY = "context_variables"
TOOL_ROLE = "tool"


class ToolHandler:
    """Handles tool call execution and result processing."""

    def __init__(
        self,
    ):
        """Initialize the ToolHandler."""

    @staticmethod
    def handle_function_result(result: Any) -> Result:
        """Handle the result returned by a function call.

        Args:
            result: The raw result from the function
            debug: Whether to print debug messages

        Returns:
            A Result object containing the processed result

        Raises:
            TypeError: If the result cannot be properly processed
        """
        from schwarm.models.agent import Agent

        match result:
            case Result() as result:
                return result
            case Agent() as agent:
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = (
                        f"Failed to cast response to string: {result}. "
                        f"Make sure agent functions return a string or Result object. "
                        f"Error: {e!s}"
                    )
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        current_agent: str,
        tool_calls: list[ChatCompletionMessageToolCall],
        functions: list[AgentFunction],
        context_variables: dict[str, Any],
        provider_context: Any,
    ) -> Response:
        """Handle a series of tool calls from the agent.

        Args:
            current_agent: The name of the current agent
            tool_calls: List of tool calls to process
            functions: List of available functions
            context_variables: Variables available to the functions
            debug: Whether to print debug messages

        Returns:
            A Response object containing the results of the tool calls
        """
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(messages=[], agent=None, context_variables={})

        for tool_call in tool_calls:
            name = tool_call.function.name
            if name not in function_map:
                msg = Message(role=TOOL_ROLE, content=f"Error: Tool {name} not found.")
                msg.additional_info = {"tool_call_id": tool_call.id, "tool_name": name}
                partial_response.messages.append(msg)
                continue

            args = json.loads(tool_call.function.arguments)

            func = function_map[name]
            if CONTEXT_VARS_KEY in func.__code__.co_varnames:
                args[CONTEXT_VARS_KEY] = context_variables

            raw_result = func(**args)
            result: Result = self.handle_function_result(raw_result)
            provider_context.current_tool_result = result
            msg = Message(role=TOOL_ROLE, content=result.value)
            msg.additional_info = {"tool_call_id": tool_call.id, "tool_name": name}
            msg.tool_call_id = tool_call.id
            partial_response.messages.append(msg)
            partial_response.context_variables.update(result.context_variables)

            receiver = None
            if result.agent:
                partial_response.agent = result.agent
                receiver = result.agent.name

            # if self.display_service:
            #     self.display_service.show_function(
            #         sender=current_agent,
            #         receiver=receiver,
            #         function=name,
            #         parameters=args,
            #         result=result,
            #         context_variables=context_variables,
            #     )

        return partial_response
