"""Tests for the Context class."""

import pytest

from schwarm.context import Context


def test_context_initialization():
    """Test that a new context is properly initialized."""
    context = Context()
    assert context.get_all() == {}


def test_set_and_get():
    """Test setting and getting values."""
    context = Context()
    context.set("key", "value")
    assert context.get("key") == "value"


def test_get_with_default():
    """Test getting a non-existent key with a default value."""
    context = Context()
    assert context.get("nonexistent", "default") == "default"


def test_remove():
    """Test removing a value."""
    context = Context()
    context.set("key", "value")
    context.remove("key")
    assert context.get("key") is None


def test_remove_nonexistent():
    """Test removing a non-existent key."""
    context = Context()
    # Should not raise an exception
    context.remove("nonexistent")


def test_clear():
    """Test clearing all values."""
    context = Context()
    context.set("key1", "value1")
    context.set("key2", "value2")
    context.clear()
    assert context.get_all() == {}


def test_contains():
    """Test checking if a key exists."""
    context = Context()
    context.set("key", "value")
    assert context.contains("key") is True
    assert context.contains("nonexistent") is False


def test_get_all():
    """Test getting all variables."""
    context = Context()
    test_data = {"key1": "value1", "key2": "value2"}
    
    for key, value in test_data.items():
        context.set(key, value)
        
    assert context.get_all() == test_data


def test_get_all_copy():
    """Test that get_all returns a copy of the variables."""
    context = Context()
    context.set("key", "value")
    
    variables = context.get_all()
    variables["new_key"] = "new_value"
    
    assert "new_key" not in context.get_all()


def test_complex_values():
    """Test handling of complex data types."""
    context = Context()
    test_data = {
        "string": "text",
        "number": 42,
        "list": [1, 2, 3],
        "dict": {"nested": "value"},
        "none": None,
    }
    
    for key, value in test_data.items():
        context.set(key, value)
        assert context.get(key) == value
