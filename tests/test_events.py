"""Tests for the events system."""

import pytest

from schwarm.events.events import Event, EventDispatcher, EventType


def test_event_creation():
    """Test that events are properly created with all attributes."""
    event = Event(
        type=EventType.AGENT_INITIALIZED,
        data={"key": "value"},
        source="test_source"
    )
    
    assert event.type == EventType.AGENT_INITIALIZED
    assert event.data == {"key": "value"}
    assert event.source == "test_source"


def test_event_optional_attributes():
    """Test that events can be created without optional attributes."""
    event = Event(type=EventType.AGENT_INITIALIZED)
    
    assert event.type == EventType.AGENT_INITIALIZED
    assert event.data is None
    assert event.source is None


def test_event_dispatcher_initialization():
    """Test that a new event dispatcher is properly initialized."""
    dispatcher = EventDispatcher()
    assert dispatcher._listeners == {}


@pytest.mark.asyncio
async def test_add_and_dispatch_listener():
    """Test adding and dispatching to a listener."""
    dispatcher = EventDispatcher()
    received_events = []
    
    async def listener(event: Event):
        received_events.append(event)
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener)
    
    event = Event(
        type=EventType.AGENT_INITIALIZED,
        data={"test": "data"}
    )
    await dispatcher.dispatch(event)
    
    assert len(received_events) == 1
    assert received_events[0] == event


@pytest.mark.asyncio
async def test_multiple_listeners():
    """Test dispatching to multiple listeners for the same event type."""
    dispatcher = EventDispatcher()
    received_events_1 = []
    received_events_2 = []
    
    async def listener1(event: Event):
        received_events_1.append(event)
        
    async def listener2(event: Event):
        received_events_2.append(event)
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener1)
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener2)
    
    event = Event(type=EventType.AGENT_INITIALIZED)
    await dispatcher.dispatch(event)
    
    assert len(received_events_1) == 1
    assert len(received_events_2) == 1


@pytest.mark.asyncio
async def test_remove_listener():
    """Test removing a listener."""
    dispatcher = EventDispatcher()
    received_events = []
    
    async def listener(event: Event):
        received_events.append(event)
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener)
    dispatcher.remove_listener(EventType.AGENT_INITIALIZED, listener)
    
    event = Event(type=EventType.AGENT_INITIALIZED)
    await dispatcher.dispatch(event)
    
    assert len(received_events) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_listener():
    """Test removing a listener that wasn't registered."""
    dispatcher = EventDispatcher()
    
    async def listener(event: Event):
        pass
    
    # Should not raise an exception
    dispatcher.remove_listener(EventType.AGENT_INITIALIZED, listener)


@pytest.mark.asyncio
async def test_dispatch_to_nonexistent_event_type():
    """Test dispatching an event with no registered listeners."""
    dispatcher = EventDispatcher()
    
    event = Event(type=EventType.AGENT_INITIALIZED)
    # Should not raise an exception
    await dispatcher.dispatch(event)


def test_clear_listeners():
    """Test clearing all listeners for an event type."""
    dispatcher = EventDispatcher()
    
    async def listener1(event: Event):
        pass
        
    async def listener2(event: Event):
        pass
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener1)
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener2)
    
    dispatcher.clear_listeners(EventType.AGENT_INITIALIZED)
    
    assert EventType.AGENT_INITIALIZED not in dispatcher._listeners


def test_clear_all_listeners():
    """Test clearing all listeners for all event types."""
    dispatcher = EventDispatcher()
    
    async def listener(event: Event):
        pass
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener)
    dispatcher.add_listener(EventType.AGENT_DESTROYED, listener)
    
    dispatcher.clear_listeners()
    
    assert len(dispatcher._listeners) == 0


@pytest.mark.asyncio
async def test_listener_exception_handling():
    """Test that exceptions in listeners don't affect other listeners."""
    dispatcher = EventDispatcher()
    received_events = []
    
    async def failing_listener(event: Event):
        raise Exception("Test exception")
        
    async def working_listener(event: Event):
        received_events.append(event)
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, failing_listener)
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, working_listener)
    
    event = Event(type=EventType.AGENT_INITIALIZED)
    # Should not raise an exception and working_listener should still receive event
    await dispatcher.dispatch(event)
    
    assert len(received_events) == 1


@pytest.mark.asyncio
async def test_event_type_isolation():
    """Test that listeners only receive events they subscribed to."""
    dispatcher = EventDispatcher()
    received_events = []
    
    async def listener(event: Event):
        received_events.append(event)
    
    dispatcher.add_listener(EventType.AGENT_INITIALIZED, listener)
    
    # Dispatch an event of a different type
    event = Event(type=EventType.AGENT_DESTROYED)
    await dispatcher.dispatch(event)
    
    assert len(received_events) == 0
