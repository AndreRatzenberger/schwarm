"""Tests for the Function class."""

import pytest

from schwarm.context.context import Context
from schwarm.functions.function import Function


def test_function_initialization():
    """Test that a function is properly initialized."""
    def implementation(context):
        return "result"
        
    function = Function(
        name="test",
        implementation=implementation,
        description="Test function"
    )
    
    assert function.name == "test"
    assert function.description == "Test function"
    assert function._implementation == implementation


def test_function_str_representation():
    """Test the string representation of a function."""
    function = Function(
        name="test",
        implementation=lambda ctx: None,
        description="Test function"
    )
    
    expected = "Function(name='test', description='Test function')"
    assert str(function) == expected


def test_function_repr():
    """Test the detailed string representation of a function."""
    def test_impl(context):
        pass
        
    function = Function(
        name="test",
        implementation=test_impl,
        description="Test function"
    )
    
    expected = (
        "Function(name='test', "
        "implementation=test_impl, "
        "description='Test function')"
    )
    assert repr(function) == expected


def test_default_description():
    """Test that a default description is provided if none is given."""
    function = Function(
        name="test",
        implementation=lambda ctx: None
    )
    
    assert function.description == "No description provided"


@pytest.mark.asyncio
async def test_sync_function_execution():
    """Test executing a synchronous function."""
    def implementation(context, arg1, arg2=None):
        return f"Result: {arg1}, {arg2}"
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    result = await function.execute(context, "value1", arg2="value2")
    assert result == "Result: value1, value2"


@pytest.mark.asyncio
async def test_async_function_execution():
    """Test executing an asynchronous function."""
    async def implementation(context, arg):
        return f"Async result: {arg}"
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    result = await function.execute(context, "test_value")
    assert result == "Async result: test_value"


@pytest.mark.asyncio
async def test_function_with_context_access():
    """Test a function that accesses the context."""
    def implementation(context, key):
        return context.get(key)
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    context.set("test_key", "test_value")
    
    result = await function.execute(context, "test_key")
    assert result == "test_value"


@pytest.mark.asyncio
async def test_function_with_context_modification():
    """Test a function that modifies the context."""
    def implementation(context, key, value):
        context.set(key, value)
        return context.get(key)
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    result = await function.execute(context, "new_key", "new_value")
    
    assert result == "new_value"
    assert context.get("new_key") == "new_value"


@pytest.mark.asyncio
async def test_function_with_multiple_arguments():
    """Test a function with multiple arguments of different types."""
    def implementation(context, arg1: str, arg2: int, arg3: dict):
        return {
            "str_arg": arg1,
            "int_arg": arg2,
            "dict_arg": arg3
        }
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    test_dict = {"key": "value"}
    result = await function.execute(
        context,
        "string",
        42,
        test_dict
    )
    
    assert result == {
        "str_arg": "string",
        "int_arg": 42,
        "dict_arg": test_dict
    }


@pytest.mark.asyncio
async def test_function_error_handling():
    """Test that function errors are properly propagated."""
    def implementation(context):
        raise ValueError("Test error")
        
    function = Function(
        name="test",
        implementation=implementation
    )
    
    context = Context()
    with pytest.raises(ValueError, match="Test error"):
        await function.execute(context)
