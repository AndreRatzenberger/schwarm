"""Tests for the Provider base class and provider implementations."""

import pytest

from schwarm.provider import Provider


def test_provider_is_abstract():
    """Test that Provider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        Provider()


def test_provider_requires_implementation():
    """Test that concrete providers must implement abstract methods."""
    class IncompleteProvider(Provider):
        pass
    
    with pytest.raises(TypeError):
        IncompleteProvider()


class MockProvider(Provider):
    """A concrete provider implementation for testing."""
    
    def __init__(self):
        self.initialized = False
        self.execution_count = 0
        self.last_args = None
        self.last_kwargs = None
        
    async def initialize(self) -> None:
        self.initialized = True
        
    async def execute(self, *args, **kwargs):
        self.execution_count += 1
        self.last_args = args
        self.last_kwargs = kwargs
        return "mock_result"


@pytest.mark.asyncio
async def test_mock_provider_initialization():
    """Test that a concrete provider can be initialized."""
    provider = MockProvider()
    assert provider.initialized is False
    
    await provider.initialize()
    assert provider.initialized is True


@pytest.mark.asyncio
async def test_mock_provider_execution():
    """Test that a concrete provider can be executed."""
    provider = MockProvider()
    result = await provider.execute("arg1", "arg2", kwarg1="value1")
    
    assert result == "mock_result"
    assert provider.execution_count == 1
    assert provider.last_args == ("arg1", "arg2")
    assert provider.last_kwargs == {"kwarg1": "value1"}


@pytest.mark.asyncio
async def test_mock_provider_multiple_executions():
    """Test that a provider can be executed multiple times."""
    provider = MockProvider()
    
    await provider.execute("first")
    await provider.execute("second")
    await provider.execute("third")
    
    assert provider.execution_count == 3
    assert provider.last_args == ("third",)


class ErrorProvider(Provider):
    """A provider that raises errors for testing error handling."""
    
    async def initialize(self) -> None:
        raise RuntimeError("Initialization error")
        
    async def execute(self, *args, **kwargs):
        raise ValueError("Execution error")


@pytest.mark.asyncio
async def test_provider_initialization_error():
    """Test that provider initialization errors are properly raised."""
    provider = ErrorProvider()
    
    with pytest.raises(RuntimeError, match="Initialization error"):
        await provider.initialize()


@pytest.mark.asyncio
async def test_provider_execution_error():
    """Test that provider execution errors are properly raised."""
    provider = ErrorProvider()
    
    with pytest.raises(ValueError, match="Execution error"):
        await provider.execute()


class ConfigurableProvider(Provider):
    """A provider that can be configured for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.initialized = False
        
    async def initialize(self) -> None:
        self.initialized = True
        
    async def execute(self, *args, **kwargs):
        return {
            "config": self.config,
            "args": args,
            "kwargs": kwargs
        }


@pytest.mark.asyncio
async def test_configurable_provider():
    """Test a provider with configuration options."""
    config = {
        "option1": "value1",
        "option2": "value2"
    }
    
    provider = ConfigurableProvider(config)
    await provider.initialize()
    
    result = await provider.execute("test")
    
    assert result["config"] == config
    assert result["args"] == ("test",)
    assert result["kwargs"] == {}


class StatefulProvider(Provider):
    """A provider that maintains state between executions."""
    
    def __init__(self):
        self.state = []
        
    async def initialize(self) -> None:
        self.state = []
        
    async def execute(self, item):
        self.state.append(item)
        return self.state


@pytest.mark.asyncio
async def test_stateful_provider():
    """Test a provider that maintains state."""
    provider = StatefulProvider()
    await provider.initialize()
    
    result1 = await provider.execute("item1")
    assert result1 == ["item1"]
    
    result2 = await provider.execute("item2")
    assert result2 == ["item1", "item2"]
    
    # Test that state persists between executions
    assert provider.state == ["item1", "item2"]


@pytest.mark.asyncio
async def test_provider_reinitialization():
    """Test that a provider can be reinitialized."""
    provider = StatefulProvider()
    
    await provider.initialize()
    await provider.execute("item1")
    await provider.execute("item2")
    
    # Reinitialize should clear the state
    await provider.initialize()
    assert provider.state == []
    
    result = await provider.execute("new_item")
    assert result == ["new_item"]
