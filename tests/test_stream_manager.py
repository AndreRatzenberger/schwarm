"""Tests for the stream manager."""

import asyncio
import pytest
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from schwarm.manager.stream_manager import StreamManager, StreamToolManager, MessageType


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        manager = StreamManager()
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                await manager.write(data.get("message", ""))
        except WebSocketDisconnect:
            await manager.disconnect(websocket)

    @app.websocket("/ws/tool")
    async def tool_websocket_endpoint(websocket: WebSocket):
        manager = StreamToolManager()
        await manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                await manager.write(data.get("message", ""))
        except WebSocketDisconnect:
            await manager.disconnect(websocket)

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_stream_manager():
    """Reset StreamManager singleton between tests."""
    StreamManager._instance = None
    StreamToolManager._instance = None
    yield


def test_websocket_connection(client):
    """Test WebSocket connection handling."""
    with client.websocket_connect("/ws") as websocket:
        # Connection should be established
        assert len(StreamManager().active_connections) == 1


def test_write_message(client):
    """Test writing messages to WebSocket clients."""
    with client.websocket_connect("/ws") as websocket:
        manager = StreamManager()
        test_message = "Test message"
        
        # Send message through manager
        websocket.send_json({"message": test_message})
        
        # Should receive the message back
        received = websocket.receive_json()
        assert received == {
            "type": MessageType.DEFAULT.value,
            "content": test_message
        }


def test_tool_manager_write(client):
    """Test writing tool messages."""
    with client.websocket_connect("/ws/tool") as websocket:
        manager = StreamToolManager()
        test_message = "Tool output"
        
        # Send message through manager
        websocket.send_json({"message": test_message})
        
        # Should receive the message back
        received = websocket.receive_json()
        assert received == {
            "type": MessageType.TOOL.value,
            "content": test_message
        }


def test_close_stream(client):
    """Test closing the stream."""
    with client.websocket_connect("/ws") as websocket:
        manager = StreamManager()
        
        # Create new event loop for this test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(manager.close())
            
            # Should receive close message
            received = websocket.receive_json()
            assert received == {
                "type": "close",
                "content": None
            }
        finally:
            loop.close()


def test_multiple_clients(client):
    """Test handling multiple WebSocket clients."""
    with client.websocket_connect("/ws") as ws1:
        with client.websocket_connect("/ws") as ws2:
            manager = StreamManager()
            assert len(manager.active_connections) == 2
            
            test_message = "Broadcast test"
            ws1.send_json({"message": test_message})
            
            # Both clients should receive the message
            received1 = ws1.receive_json()
            received2 = ws2.receive_json()
            
            assert received1 == received2 == {
                "type": MessageType.DEFAULT.value,
                "content": test_message
            }


def test_client_disconnect_handling(client):
    """Test handling client disconnections gracefully."""
    manager = StreamManager()
    
    # Connect first client
    ws1 = client.websocket_connect("/ws").__enter__()
    assert len(manager.active_connections) == 1
    
    # Connect second client
    ws2 = client.websocket_connect("/ws").__enter__()
    assert len(manager.active_connections) == 2
    
    try:
        # Close ws1 manually
        ws1.__exit__(None, None, None)
        
        # Give a small delay for the disconnect to process
        import time
        time.sleep(0.1)
        
        # Only ws2 should be in active connections
        assert len(manager.active_connections) == 1
        
        # Send message through remaining client
        test_message = "Test after disconnect"
        ws2.send_json({"message": test_message})
        
        # ws2 should still receive messages
        received = ws2.receive_json()
        assert received == {
            "type": MessageType.DEFAULT.value,
            "content": test_message
        }
    finally:
        # Clean up remaining connection
        ws2.__exit__(None, None, None)
