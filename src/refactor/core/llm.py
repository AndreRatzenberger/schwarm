"""Simple LLM provider implementation."""

from typing import Any

from litellm import completion

from .types import CompletionResult, Message


class LLMProvider:
    """Simple provider for language model interactions."""

    def __init__(self, model: str, api_key: str | None = None):
        """Initialize the provider."""
        self.model = model
        self.api_key = api_key

    def _format_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        """Format messages for the API."""
        return [{"role": msg.role, "content": msg.content, "tool_calls": msg.tool_calls} for msg in messages]

    def _extract_content(self, response: Any) -> tuple[str, list[dict[str, Any]]]:
        """Extract content and tool calls from a response."""
        content = ""
        tool_calls = []

        try:
            # Try to get the message from the response
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]

                # Try to get content from message
                if hasattr(choice, "message"):
                    message = choice.message
                    content = str(getattr(message, "content", ""))

                    # Try to get tool calls from message
                    raw_tool_calls = getattr(message, "tool_calls", [])
                    if raw_tool_calls:
                        for call in raw_tool_calls:
                            if hasattr(call, "function"):
                                # Handle OpenAI-style responses
                                tool_calls.append({"name": call.function.name, "arguments": call.function.arguments})
                            elif isinstance(call, dict):
                                # Handle dictionary responses
                                if "name" in call and "arguments" in call:
                                    tool_calls.append(call)

                # Fallback to text attribute if no message
                elif hasattr(choice, "text"):
                    content = str(choice.text)

                # Final fallback to string representation
                elif hasattr(choice, "__str__"):
                    content = str(choice)

        except Exception as e:
            content = f"Error parsing response: {e!s}"

        return content, tool_calls

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> CompletionResult:
        """Generate a completion for the given messages."""
        try:
            formatted_messages = self._format_messages(messages)

            # Prepare completion arguments
            completion_args = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
            }

            if self.api_key:
                completion_args["api_key"] = self.api_key

            # Add tools if provided
            if tools:
                completion_args["tools"] = tools
                completion_args["tool_choice"] = "auto"

            # Get completion
            response = completion(**completion_args)

            # Extract content and tool calls
            content, tool_calls = self._extract_content(response)

            # Create result message
            result_message = Message(content=content, role="assistant", tool_calls=tool_calls)

            return CompletionResult(message=result_message, raw_response=response)

        except Exception as e:
            # On error, return a message indicating the failure
            error_message = Message(content=f"Error generating completion: {e!s}", role="assistant")
            return CompletionResult(message=error_message)
