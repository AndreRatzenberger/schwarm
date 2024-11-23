"""Tests for the WebDebugProvider."""

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest
from websockets.exceptions import WebSocketException

from schwarm.events.event_data import Event, EventType
from schwarm.provider.web_debug_provider import WebDebugConfig, WebDebugProvider
from tests.test_websocket_server import TestWebSocketServer


@pytest.fixture
def config():
    """Create a test configuration."""
    return WebDebugConfig(websocket_target="ws://localhost:8000/ws")


@pytest.fixture
def provider(config):
    """Create a test provider."""
    return WebDebugProvider(config=config)


@pytest.fixture
async def websocket_server():
    """Create and run a test websocket server."""
    server = TestWebSocketServer()
    server_task = asyncio.create_task(server.start())
    # Give the server time to start
    await asyncio.sleep(0.1)
    yield server
    await server.stop()
    await server_task


# Unit Tests

@pytest.mark.asyncio
async def test_websocket_connection(provider):
    """Test websocket connection is established."""
    mock_websocket = AsyncMock()
    mock_websocket.open = True

    with patch("websockets.connect", return_value=mock_websocket) as mock_connect:
        await provider._ensure_connection()
        mock_connect.assert_called_once_with(provider.config.websocket_target)
        assert provider._websocket == mock_websocket


@pytest.mark.asyncio
async def test_websocket_connection_failure(provider):
    """Test websocket connection failure is handled."""
    with patch("websockets.connect", side_effect=WebSocketException("Connection failed")):
        with pytest.raises(WebSocketException):
            await provider._ensure_connection()
        assert provider._websocket is None


@pytest.mark.asyncio
async def test_send_event(provider):
    """Test sending event to websocket."""
    mock_websocket = AsyncMock()
    mock_websocket.open = True
    provider._websocket = mock_websocket

    event = Event(
        type=EventType.START,
        payload={"message": "test"},
        agent_id="test_agent",
        datetime="2024-01-01T00:00:00"
    )

    await provider._send_event(event)

    expected_data = {
        "type": event.type.value,
        "payload": event.payload,
        "agent_id": event.agent_id,
        "datetime": event.datetime,
    }
    mock_websocket.send.assert_called_once_with(json.dumps(expected_data))


@pytest.mark.asyncio
async def test_handle_event(provider):
    """Test handling event."""
    provider._send_event = AsyncMock()
    event = Event(
        type=EventType.START,
        payload={"message": "test"},
        agent_id="test_agent",
        datetime="2024-01-01T00:00:00"
    )

    result = await provider.handle_event(event)

    provider._send_event.assert_called_once_with(event)
    assert result == event.payload
    assert event in provider.event_log


@pytest.mark.asyncio
async def test_cleanup(provider):
    """Test cleanup closes websocket connection."""
    mock_websocket = AsyncMock()
    provider._websocket = mock_websocket

    await provider.cleanup()

    mock_websocket.close.assert_called_once()
    assert provider._websocket is None


def test_initialize(provider):
    """Test provider initialization."""
    provider.initialize()
    assert provider._initialized is True


# Integration Tests with Real WebSocket Server

@pytest.mark.asyncio
async def test_integration_send_event(websocket_server, provider):
    """Test sending event to real websocket server."""
    event = Event(
        type=EventType.START,
        payload={"message": "integration test"},
        agent_id="test_agent",
        datetime="2024-01-01T00:00:00"
    )

    await provider.handle_event(event)
    # Give the server time to process the message
    await asyncio.sleep(0.1)

    messages = websocket_server.get_received_messages()
    assert len(messages) == 1
    assert messages[0]["type"] == event.type.value
    assert messages[0]["payload"] == event.payload
    assert messages[0]["agent_id"] == event.agent_id
    assert messages[0]["datetime"] == event.datetime


@pytest.mark.asyncio
async def test_integration_multiple_events(websocket_server, provider):
    """Test sending multiple events to real websocket server."""
    events = [
        Event(
            type=EventType.START,
            payload={"message": f"test {i}"},
            agent_id="test_agent",
            datetime=f"2024-01-01T00:00:0{i}"
        )
        for i in range(3)
    ]

    for event in events:
        await provider.handle_event(event)
    
    # Give the server time to process all messages
    await asyncio.sleep(0.1)

    messages = websocket_server.get_received_messages()
    assert len(messages) == len(events)
    
    for event, message in zip(events, messages):
        assert message["type"] == event.type.value
        assert message["payload"] == event.payload
        assert message["agent_id"] == event.agent_id
        assert message["datetime"] == event.datetime
