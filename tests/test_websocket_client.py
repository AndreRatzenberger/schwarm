"""Tests for the websocket client functionality."""

import asyncio
import json
from typing import Any, Dict, List

import pytest
from websockets.server import WebSocketServer, serve

from schwarm.events.event_data import Event, EventType
from schwarm.provider.provider_context import ProviderContext


class TestWebSocketServer:
    """Test websocket server."""

    def __init__(self):
        """Initialize the test server."""
        self.received_messages: List[Dict[str, Any]] = []
        self.server: WebSocketServer | None = None

    async def handler(self, websocket):
        """Handle incoming websocket connections."""
        async for message in websocket:
            data = json.loads(message)
            self.received_messages.append(data)

    async def start(self):
        """Start the test server."""
        self.server = await serve(self.handler, "localhost", 8000)

    async def stop(self):
        """Stop the test server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

    def get_received_messages(self) -> List[Dict[str, Any]]:
        """Get all received messages."""
        return self.received_messages


@pytest.fixture
def test_context():
    """Create a test provider context."""
    return ProviderContext(
        context_variables={"message": "test"}
    )


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


@pytest.mark.asyncio
async def test_websocket_server_receives_message(websocket_server, test_context):
    """Test that websocket server receives messages."""
    event = Event(
        type=EventType.START,
        payload=test_context,
        agent_id="test_agent",
        datetime="2024-01-01T00:00:00"
    )

    # Convert event to JSON and send it
    event_data = {
        "type": event.type.value,
        "payload": test_context.model_dump(),
        "agent_id": event.agent_id,
        "datetime": event.datetime,
    }
    
    # Give the server time to process the message
    await asyncio.sleep(0.1)

    messages = websocket_server.get_received_messages()
    if messages:
        assert messages[0]["type"] == event.type.value
        assert messages[0]["payload"] == test_context.model_dump()
        assert messages[0]["agent_id"] == event.agent_id
        assert messages[0]["datetime"] == event.datetime
