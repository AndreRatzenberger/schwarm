"""Handling Streaming Responses and Chunk Processing."""

from collections import defaultdict
from collections.abc import Generator
from typing import Any

import orjson

from schwarm.utils.merge import merge_chunk
from schwarm.utils.settings import APP_SETTINGS

# Constants


class StreamHandler:
    """Handles streaming responses and chunk processing."""

    @staticmethod
    def _process_chunk(chunk: Any, message: dict[str, Any], agent_name: str) -> dict[str, Any]:
        """Process a single chunk from the streaming response.

        Args:
            chunk: The chunk to process
            message: The current message being built
            agent_name: The name of the current agent

        Returns:
            The processed delta for yielding
        """
        delta = orjson.loads(chunk.choices[0].delta.json())
        if delta.get("role") == APP_SETTINGS.ASSISTANT_ROLE:
            delta["sender"] = agent_name
        return delta

    @staticmethod
    def create_empty_message(agent_name: str) -> dict[str, Any]:
        """Create an empty message structure for accumulating streaming response.

        Args:
            agent_name: The name of the agent

        Returns:
            An empty message dictionary with default values
        """
        return {
            "content": "",
            "sender": agent_name,
            "role": APP_SETTINGS.ASSISTANT_ROLE,
            "function_call": None,
            "tool_calls": defaultdict(
                lambda: {
                    "function": {"arguments": "", "name": ""},
                    "id": "",
                    "type": "",
                }
            ),
        }

    def process_stream(
        self,
        completion: Any,
        message: dict[str, Any],
        agent_name: str,
    ) -> Generator[dict[str, Any], None, None]:
        """Process a streaming completion response.

        Args:
            completion: The streaming completion to process
            message: The message being built
            agent_name: The name of the current agent

        Yields:
            Processed chunks and delimiters
        """
        yield {"delim": "start"}

        for chunk in completion:
            delta = self._process_chunk(chunk, message, agent_name)
            yield delta
            merge_chunk(message, delta)

        yield {"delim": "end"}

    @staticmethod
    def finalize_message(message: dict[str, Any], debug: bool) -> None:
        """Finalize a message after streaming is complete.

        Args:
            message: The message to finalize
            debug: Whether to print debug messages
        """
        message["tool_calls"] = list(message.get("tool_calls", {}).values()) or None
