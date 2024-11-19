"""Utility functions for merging dictionaries."""

from typing import Any


def merge_fields(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Recursively merge source dictionary into target dictionary, concatenating strings and merging nested dictionaries.

    Args:
        target: The target dictionary to merge into
        source: The source dictionary to merge from

    Raises:
        TypeError: If incompatible types are encountered during merge
    """
    for key, value in source.items():
        if isinstance(value, str):
            if key not in target:
                target[key] = ""
            if not isinstance(target[key], str):
                raise TypeError(f"Cannot merge non-string value into string for key: {key}")
            target[key] += value
        elif value is not None and isinstance(value, dict):
            if key not in target:
                target[key] = {}
            if not isinstance(target[key], dict):
                raise TypeError(f"Cannot merge into non-dict value for key: {key}")
            merge_fields(target[key], value)  # type: ignore


def merge_chunk(final_response: dict[str, Any], delta: dict[str, Any]) -> None:
    """Merge a chunk delta into the final response, handling special cases for tool calls.

    Args:
        final_response: The accumulated final response dictionary
        delta: The delta chunk to merge into the final response

    Raises:
        KeyError: If required keys are missing in the delta for tool calls
        TypeError: If incompatible types are encountered during merge
    """
    # Remove role as it's handled separately
    delta.pop("role", None)

    try:
        # Handle tool calls specially
        tool_calls = delta.get("tool_calls")
        if tool_calls and len(tool_calls) > 0:
            # Ensure tool_calls exists in final_response
            if "tool_calls" not in final_response:
                final_response["tool_calls"] = {}

            # Get and remove index from tool call
            index = tool_calls[0].pop("index")
            if index is None:
                raise KeyError("Tool call index is missing")

            # Merge the tool call data

            merge_fields(final_response["tool_calls"][index], tool_calls[0])  # type: ignore
        else:
            # Regular merge for non-tool-call updates
            merge_fields(final_response, delta)
    except (KeyError, TypeError) as e:
        raise type(e)(f"Error merging chunk: {e!s}")
