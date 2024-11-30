"""Tests for the Agent class and AgentBuilder."""

import pytest

from schwarm.agent import Agent
from schwarm.agent_builder import AgentBuilder
from schwarm.context import Context
from schwarm.events import Event, EventDispatcher, EventType
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


def test_agent_initialization():
    """Test basic agent initialization."""
    agent = Agent(name="test_agent")
    
    assert agent.name == "test_agent"
    assert isinstance(agent.context, Context)
    assert isinstance(agent.event_dispatcher, EventDispatcher)


def test_agent_with_static_instructions():
    """Test agent with static instructions."""
    instructions = "Test instructions"
    agent = Agent(name="test_agent", instructions=instructions)
    
    assert agent.get_instructions() == instructions


def test_agent_with_dynamic_instructions():
    """Test agent with dynamic instructions."""
    def get_instructions(context: Context) -> str:
        return f"Count: {context.get('count', 0)}"
        
    agent = Agent(name="test_agent", instructions=get_instructions)
    agent.context.set("count", 42)
    
    assert agent.get_instructions() == "Count: 42"


@pytest.mark.asyncio
async def test_agent_initialization_with_providers():
    """Test agent initialization with providers."""
    provider = MockProvider()
    agent = Agent(name="test_agent", providers=[provider])
    
    await agent.initialize()
    assert provider.initialized


@pytest.mark.asyncio
async def test_agent_function_execution():
    """Test executing a function through the agent."""
    async def test_function(context: Context, arg: str) -> str:
        return f"Processed: {arg}"
        
    function = Function(
        name="test_func",
        implementation=test_function
    )
    
    agent = Agent(name="test_agent", functions=[function])
    result = await agent.execute_function("test_func", "test_input")
    
    assert result == "Processed: test_input"


@pytest.mark.asyncio
async def test_agent_provider_execution():
    """Test executing a provider through the agent."""
    provider = MockProvider()
    agent = Agent(name="test_agent", providers=[provider])
    
    await agent.initialize()
    result = await agent.execute_provider(provider, "test_input")
    
    assert result == "mock_result"
    assert provider.calls == [(("test_input",), {})]


def test_agent_function_management():
    """Test adding and removing functions."""
    agent = Agent(name="test_agent")
    
    function = Function(
        name="test_func",
        implementation=lambda ctx: "result"
    )
    
    agent.add_function(function)
    assert "test_func" in agent._functions
    
    agent.remove_function("test_func")
    assert "test_func" not in agent._functions


def test_agent_provider_management():
    """Test adding and removing providers."""
    agent = Agent(name="test_agent")
    provider = MockProvider()
    
    agent.add_provider(provider)
    assert provider in agent._providers
    
    agent.remove_provider(provider)
    assert provider not in agent._providers


@pytest.mark.asyncio
async def test_agent_event_handling():
    """Test that agent properly dispatches events."""
    received_events = []
    
    async def event_listener(event: Event):
        received_events.append(event)
    
    agent = Agent(name="test_agent")
    agent.event_dispatcher.add_listener(
        EventType.BEFORE_FUNCTION_EXECUTION,
        event_listener
    )
    
    function = Function(
        name="test_func",
        implementation=lambda ctx: "result"
    )
    agent.add_function(function)
    
    await agent.execute_function("test_func")
    
    assert len(received_events) > 0
    assert received_events[0].type == EventType.BEFORE_FUNCTION_EXECUTION


def test_agent_builder_basic():
    """Test basic AgentBuilder functionality."""
    agent = (
        AgentBuilder("test_agent")
        .with_instructions("Test instructions")
        .build()
    )
    
    assert agent.name == "test_agent"
    assert agent.get_instructions() == "Test instructions"


def test_agent_builder_with_components():
    """Test AgentBuilder with all component types."""
    function = Function(
        name="test_func",
        implementation=lambda ctx: "result"
    )
    provider = MockProvider()
    context = Context()
    dispatcher = EventDispatcher()
    
    agent = (
        AgentBuilder("test_agent")
        .with_function(function)
        .with_provider(provider)
        .with_context(context)
        .with_event_dispatcher(dispatcher)
        .build()
    )
    
    assert "test_func" in agent._functions
    assert provider in agent._providers
    assert agent.context == context
    assert agent.event_dispatcher == dispatcher


def test_agent_builder_with_multiple_functions():
    """Test AgentBuilder with multiple functions."""
    functions = [
        Function(name=f"func_{i}", implementation=lambda ctx: f"result_{i}")
        for i in range(3)
    ]
    
    agent = (
        AgentBuilder("test_agent")
        .with_functions(functions)
        .build()
    )
    
    assert len(agent._functions) == 3
    assert all(f"func_{i}" in agent._functions for i in range(3))


def test_agent_builder_with_multiple_providers():
    """Test AgentBuilder with multiple providers."""
    providers = [MockProvider() for _ in range(3)]
    
    agent = (
        AgentBuilder("test_agent")
        .with_providers(providers)
        .build()
    )
    
    assert len(agent._providers) == 3
    assert all(provider in agent._providers for provider in providers)


@pytest.mark.asyncio
async def test_agent_builder_with_event_listeners():
    """Test AgentBuilder with event listeners."""
    received_events = []
    
    async def listener(event: Event):
        received_events.append(event)
    
    agent = (
        AgentBuilder("test_agent")
        .with_event_listener(EventType.AGENT_INITIALIZED, listener)
        .build()
    )
    
    await agent.initialize()
    
    assert len(received_events) == 1
    assert received_events[0].type == EventType.AGENT_INITIALIZED


def test_agent_builder_method_chaining():
    """Test that all builder methods return self for chaining."""
    builder = AgentBuilder("test_agent")
    
    # All these methods should return the same builder instance
    assert builder.with_instructions("test") is builder
    assert builder.with_function(
        Function(name="test", implementation=lambda ctx: None)
    ) is builder
    assert builder.with_provider(MockProvider()) is builder
    assert builder.with_context(Context()) is builder
    assert builder.with_event_dispatcher(EventDispatcher()) is builder
