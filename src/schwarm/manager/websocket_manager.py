"""Manages WebSocket communication for sending messages."""

import asyncio

from fastapi import WebSocket
from loguru import logger

from schwarm.manager.websocket_messages import WebsocketMessage


class WebsocketManager:
    """Manages WebSocket communication.

    This implementation provides:
    - Real-time bi-directional communication capability
    - Support for multiple concurrent clients
    - Proper resource cleanup
    - Message-based communication
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize the singleton instance."""
        self.active_connections: set[WebSocket] = set()
        logger.debug("WebsocketManager initialized")

    def send_chat_requested(self):
        """Send a chat request message to all connected WebSocket clients (sync version)."""
        try:
            message = WebsocketMessage(message_type="CHAT_REQUESTED")
            # Create new event loop for sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_message(message))
            loop.close()
        except Exception as e:
            logger.error(f"Error sending chat request: {e}")

    def send_is_waiting(self):
        """Send a waiting status message to all connected WebSocket clients (sync version)."""
        try:
            message = WebsocketMessage(message_type="IS_WAITING")
            # Create new event loop for sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.send_message(message))
            loop.close()
        except Exception as e:
            logger.error(f"Error sending waiting status: {e}")

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        self.active_connections.remove(websocket)
        logger.debug(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")

    async def send_message(self, message: WebsocketMessage) -> None:
        """Send a message to all connected WebSocket clients.

        Args:
            message: WebsocketMessage to send
        """
        if not message:  # Avoid empty messages
            return

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message.model_dump())
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

        logger.debug(f"Message sent: {message.message_type} - {message.message[:50]}...")

    async def close(self) -> None:
        """Close all active connections."""
        close_message = WebsocketMessage(message_type="EVENT", message="Connection closed")

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(close_message.model_dump())
            except Exception as e:
                logger.error(f"Error sending close signal: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

        logger.debug("All WebSocket connections closed")
