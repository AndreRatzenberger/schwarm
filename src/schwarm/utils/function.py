"""Utility for converting a python function into a openai function JSON format."""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def function_to_json(func: Callable[..., T]) -> dict[str, Any]:
    """Convert a Python function into a JSON-serializable dictionary describing its signature.

    This is used to describe available tools/functions to the AI model.

    Args:
        func: The function to convert to JSON format

    Returns:
        A dictionary containing the function's name, description, and parameter information

    Raises:
        ValueError: If unable to get function signature
        KeyError: If unknown type annotation is encountered
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        type(None): "null",
    }

    try:
        signature = inspect.signature(func)
    except ValueError as e:
        raise ValueError(f"Failed to get signature for function {func.__name__}: {e!s}")

    parameters: dict[str, dict[str, str]] = {}
    required: list[str] = []

    for param_name, param in signature.parameters.items():
        # Handle required parameters
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

        # Get parameter type
        param_type = "string"  # default type
        if param.annotation != inspect.Signature.empty:
            try:
                param_type = type_map.get(param.annotation, "string")
            except KeyError as e:
                raise KeyError(f"Unknown type annotation {param.annotation} for parameter {param_name}: {e!s}")

        # Add parameter info
        parameters[param_name] = {"type": param_type}

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": parameters,
                "required": required,
            },
        },
    }
