"""Utility functions for handling data."""

from typing import Any


def make_serializable(obj: Any) -> Any:
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
