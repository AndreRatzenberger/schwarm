"""Tests for the stream manager."""

import asyncio
import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from websockets.client import connect
from websockets.exceptions import ConnectionClosed

from schwarm.manager.stream_manager import StreamManager, StreamToolManager, MessageType


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    stream_manager = StreamManager()
    tool_manager = StreamToolManager()

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await stream_manager.connect(websocket)
        try:
            while True:
                await asyncio.sleep(1)
        except Exception:
            await stream_manager.disconnect(websocket)

    @app.websocket("/ws/tool")
    async def tool_websocket_endpoint(websocket: WebSocket):
        await tool_manager.connect(websocket)
        try:
            while True:
                await asyncio.sleep(1)
        except Exception:
            await tool_manager.disconnect(websocket)

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_websocket_connection(app, client):
    """Test WebSocket connection handling."""
    async with connect("ws://testserver/ws") as websocket:
        # Connection should be established
        assert StreamManager()._instance.active_connections


@pytest.mark.asyncio
async def test_write_message(app, client):
    """Test writing messages to WebSocket clients."""
    async with connect("ws://testserver/ws") as websocket:
        manager = StreamManager()
        test_message = "Test message"
        await manager.write(test_message)
        
        # Should receive the message
        message = await websocket.recv()
        data = eval(message)  # Safe since we control the test data
        assert data == {
            "type": MessageType.DEFAULT.value,
            "content": test_message
        }


@pytest.mark.asyncio
async def test_tool_manager_write(app, client):
    """Test writing tool messages."""
    async with connect("ws://testserver/ws/tool") as websocket:
        manager = StreamToolManager()
        test_message = "Tool output"
        await manager.write(test_message)
        
        # Should receive the message
        message = await websocket.recv()
        data = eval(message)
        assert data == {
            "type": MessageType.TOOL.value,
            "content": test_message
        }


@pytest.mark.asyncio
async def test_close_stream(app, client):
    """Test closing the stream."""
    async with connect("ws://testserver/ws") as websocket:
        manager = StreamManager()
        await manager.close()
        
        # Should receive close message
        message = await websocket.recv()
        data = eval(message)
        assert data == {
            "type": "close",
            "content": None
        }
        
        # Connection should be closed after this
        with pytest.raises(ConnectionClosed):
            await websocket.recv()


@pytest.mark.asyncio
async def test_multiple_clients(app, client):
    """Test handling multiple WebSocket clients."""
    async with connect("ws://testserver/ws") as ws1, \
               connect("ws://testserver/ws") as ws2:
        manager = StreamManager()
        test_message = "Broadcast test"
        await manager.write(test_message)
        
        # Both clients should receive the message
        for ws in [ws1, ws2]:
            message = await ws.recv()
            data = eval(message)
            assert data == {
                "type": MessageType.DEFAULT.value,
                "content": test_message
            }


@pytest.mark.asyncio
async def test_client_disconnect_handling(app, client):
    """Test handling client disconnections gracefully."""
    async with connect("ws://testserver/ws") as ws1, \
               connect("ws://testserver/ws") as ws2:
        manager = StreamManager()
        
        # Close ws1 to simulate disconnect
        await ws1.close()
        
        test_message = "Test after disconnect"
        await manager.write(test_message)
        
        # ws2 should still receive messages
        message = await ws2.recv()
        data = eval(message)
        assert data == {
            "type": MessageType.DEFAULT.value,
            "content": test_message
        }
        
        # ws1 should be removed from active connections
        assert len(manager.active_connections) == 1
