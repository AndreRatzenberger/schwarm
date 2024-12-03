"""Integration test server for WebSocket functionality."""

import asyncio
from threading import Thread
from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi.websockets import WebSocketDisconnect
from loguru import logger

from schwarm.manager.server import WebsocketManager2
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

# WebSocket manager singleton
ws_manager = WebsocketManager2()


@app.on_event("startup")
async def startup_event():
    """Start WebSocket server in the background on FastAPI startup."""
    asyncio.create_task(ws_manager.start())


@app.post("/trigger/messages")
async def trigger_messages():
    """Trigger WebSocket messages via HTTP."""
    messages = [
        WebsocketMessage(message_type="STREAM", message="##START##"),
        WebsocketMessage(message_type="STREAM", message="CHUNK "),
        WebsocketMessage(message_type="STREAM", message="STREAM "),
        WebsocketMessage(message_type="STREAM", message="Test"),
        WebsocketMessage(message_type="BREAK", message="Waiting for user input"),
        WebsocketMessage(message_type="EVENT", message="Test event message"),
        WebsocketMessage(message_type="CHAT", message="System paused"),
    ]

    for msg in messages:
        await ws_manager.send_message(msg)
        await asyncio.sleep(0.5)

    return {"status": "success", "message": "Messages sent"}



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8123)
    
