"""Utility functions for handling data."""

import importlib
import json
from typing import Any


def serialize_callable(obj):
    """Serialize a callable object into a string representation."""
    if callable(obj):
        return f"{obj.__module__}.{obj.__name__}"
    return obj  # Assume it's a string or another serializable object


def deserialize_callable(name):
    """Deserialize a string representation of a callable object."""
    if isinstance(name, str) and "." in name:
        module_name, function_name = name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        return getattr(module, function_name)
    return name  # Assume it's already deserialized


def make_serializable(obj: Any) -> dict | list | tuple | str:
    """Recursively convert an object into a serializable format."""
    if isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(item) for item in obj)
    elif isinstance(obj, set):
        return [make_serializable(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        # For Pydantic models
        return make_serializable(obj.model_dump())
    elif callable(obj):
        # Handle callable objects (functions, methods)
        return f"<function {obj.__name__}>" if hasattr(obj, "__name__") else str(obj)
    elif hasattr(obj, "__dict__"):
        # For objects with __dict__, convert their attributes
        return {"__type__": obj.__class__.__name__, "attributes": make_serializable(obj.__dict__)}

    # Try json serialization as a test
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError, ValueError):
        # If the object can't be serialized, convert it to string
        return str(obj)


def flatten_attributes(obj: Any, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten the attributes of an object into a single-level dictionary.

    Args:
        obj: The object to flatten.
        parent_key: The key path leading to the current level (used internally for recursion).
        sep: The separator to use for nested keys in the flattened dictionary.

    Returns:
        A dictionary with flattened key paths and their corresponding values.
    """
    items = []

    # Recursively process dictionaries
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key
            items.extend(flatten_attributes(value, new_key, sep).items())
    # Recursively process lists and tuples
    elif isinstance(obj, list | tuple):
        for i, value in enumerate(obj):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            items.extend(flatten_attributes(value, new_key, sep).items())
    # For other objects with __dict__, process their attributes
    elif hasattr(obj, "__dict__"):
        obj_dict = make_serializable(obj)
        items.extend(flatten_attributes(obj_dict, parent_key, sep).items())
    else:
        # Base case: not a container, just return the value
        items.append((parent_key, obj))

    return dict(items)
