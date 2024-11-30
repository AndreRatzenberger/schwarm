"""Test configuration and shared fixtures."""

import pytest

from schwarm.agent import Agent
from schwarm.agent_builder import AgentBuilder
from schwarm.context import Context
from schwarm.events import EventDispatcher, EventType
from schwarm.function import Function
from schwarm.provider import Provider


class MockProvider(Provider):
    """Mock provider for testing."""
    
    def __init__(self):
        self.initialized = False
        self.calls = []
        
    async def initialize(self) -> None:
        self.initialized = True
        
    async def execute(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return "mock_result"


@pytest.fixture
def context():
    """Provide a fresh Context instance."""
    return Context()


@pytest.fixture
def event_dispatcher():
    """Provide a fresh EventDispatcher instance."""
    return EventDispatcher()


@pytest.fixture
def mock_provider():
    """Provide a MockProvider instance."""
    return MockProvider()


@pytest.fixture
def mock_function():
    """Provide a simple mock Function instance."""
    async def implementation(context: Context, *args, **kwargs):
        return "mock_function_result"
    
    return Function(
        name="mock_function",
        implementation=implementation,
        description="Mock function for testing"
    )


@pytest.fixture
def basic_agent(context, event_dispatcher):
    """Provide a basic Agent instance with context and event dispatcher."""
    return Agent(
        name="test_agent",
        context=context,
        event_dispatcher=event_dispatcher
    )


@pytest.fixture
def agent_builder():
    """Provide an AgentBuilder instance."""
    return AgentBuilder("test_agent")


@pytest.fixture
def full_agent(mock_provider, mock_function):
    """Provide a fully configured Agent instance with all components."""
    return (
        AgentBuilder("test_agent")
        .with_instructions("Test instructions")
        .with_provider(mock_provider)
        .with_function(mock_function)
        .build()
    )


@pytest.fixture
def event_recorder():
    """Provide a helper for recording events."""
    class EventRecorder:
        def __init__(self):
            self.events = []
            
        async def listener(self, event):
            self.events.append(event)
            
        def clear(self):
            self.events.clear()
    
    return EventRecorder()


@pytest.fixture
def agent_with_event_recording(basic_agent, event_recorder):
    """Provide an agent with event recording capability."""
    for event_type in EventType:
        basic_agent.event_dispatcher.add_listener(
            event_type,
            event_recorder.listener
        )
    return basic_agent


@pytest.fixture
def sample_text():
    """Provide a sample text for testing."""
    return """
    The Schwarm Framework is an intuitive and powerful agent framework designed
    to facilitate the creation and combination of AI agents with diverse
    capabilities through the use of providers. The framework emphasizes
    modularity, extensibility, ease of use, and code quality.
    """


@pytest.fixture
def complex_data():
    """Provide complex data structures for testing."""
    return {
        "string": "test",
        "number": 42,
        "list": [1, 2, 3],
        "dict": {"key": "value"},
        "nested": {
            "list": [{"a": 1}, {"b": 2}],
            "dict": {"x": [1, 2, 3]}
        }
    }


@pytest.fixture
def error_provider():
    """Provide a provider that raises errors for testing error handling."""
    class ErrorProvider(Provider):
        async def initialize(self) -> None:
            raise RuntimeError("Initialization error")
            
        async def execute(self, *args, **kwargs):
            raise ValueError("Execution error")
    
    return ErrorProvider()


@pytest.fixture
def stateful_provider():
    """Provide a provider that maintains state for testing."""
    class StatefulProvider(Provider):
        def __init__(self):
            self.state = []
            
        async def initialize(self) -> None:
            self.state = []
            
        async def execute(self, item):
            self.state.append(item)
            return self.state
    
    return StatefulProvider()


@pytest.fixture
def configurable_provider():
    """Provide a provider that can be configured for testing."""
    class ConfigurableProvider(Provider):
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
    
    return ConfigurableProvider
