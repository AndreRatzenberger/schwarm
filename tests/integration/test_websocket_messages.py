"""Integration test server for WebSocket functionality."""

import asyncio
import json
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.websockets import WebSocketDisconnect
from loguru import logger

from schwarm.manager.stream_manager import StreamManager, MessageType
from schwarm.manager.websocket_manager import WebsocketManager
from schwarm.manager.websocket_messages import WebsocketMessage

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint that uses WebsocketManager."""
    websocket_manager = WebsocketManager()
    await websocket_manager.connect(websocket)
    try:
        while True:
            try:
                # Wait for messages but allow for graceful shutdown
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)

@app.websocket("/ws/stream")
async def websocket_stream_endpoint(websocket: WebSocket):
    """Stream WebSocket endpoint that uses StreamManager."""
    stream_manager = StreamManager()
    await stream_manager.connect(websocket)
    try:
        while True:
            try:
                # Wait for messages but allow for graceful shutdown
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                break
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket stream error: {e}")
    finally:
        await stream_manager.disconnect(websocket)

@app.post("/trigger/messages")
async def trigger_messages():
    """REST endpoint to trigger sending messages using WebsocketManager."""
    websocket_manager = WebsocketManager()
    messages = [
        WebsocketMessage(message_type="CHAT_REQUESTED", message="Test chat request"),
        WebsocketMessage(message_type="IS_WAITING", message="Waiting for user input"),
        WebsocketMessage(message_type="EVENT", message="Test event message"),
        WebsocketMessage(message_type="PAUSE_STATUS", message="System paused"),
    ]
    
    for msg in messages:
        await websocket_manager.send_message(msg)
        await asyncio.sleep(0.5)
    
    return {"status": "success", "message": "Messages sent"}

@app.post("/trigger/stream")
async def trigger_stream():
    """REST endpoint to trigger sending stream messages using StreamManager."""
    stream_manager = StreamManager()
    chunks = [
        "This is a ",
        "streaming message ",
        "sent in chunks.",
    ]
    
    for chunk in chunks:
        await stream_manager.write(chunk, MessageType.DEFAULT)
        await asyncio.sleep(0.2)
    
    await stream_manager.close()
    return {"status": "success", "message": "Stream messages sent"}

@app.post("/trigger/all")
async def trigger_all():
    """REST endpoint to trigger both regular and stream messages."""
    messages_result = await trigger_messages()
    stream_result = await trigger_stream()
    
    return {
        "messages": messages_result,
        "stream": stream_result
    }

if __name__ == "__main__":
    print("Starting test WebSocket server on port 8123...")
    uvicorn.run(app, host="127.0.0.1", port=8123)
