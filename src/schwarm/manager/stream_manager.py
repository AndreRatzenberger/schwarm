"""Manages streaming of LLM outputs using WebSocket."""

from enum import Enum

from fastapi import WebSocket
from loguru import logger

from schwarm.provider.provider_manager import ProviderManager


class MessageType(Enum):
    """Types of messages that can be streamed."""

    DEFAULT = "default"
    TOOL = "tool"


class StreamManager:
    """Manages streaming of LLM outputs using WebSocket.

    This implementation provides:
    - Real-time bi-directional communication
    - Support for multiple concurrent clients
    - Proper resource cleanup
    - Memory efficient streaming
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
        logger.debug("StreamManager initialized")

    async def connect(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug(f"New WebSocket connection established. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        self.active_connections.remove(websocket)
        logger.debug(f"WebSocket connection closed. Remaining connections: {len(self.active_connections)}")

    async def write(self, chunk: str, agent_name: str, message_type: MessageType = MessageType.DEFAULT) -> None:
        """Write a chunk to all connected WebSocket clients.

        Args:
            chunk: Text chunk to stream
            message_type: Type of message (default or tool output)
        """
        if not chunk:  # Avoid empty chunks
            return

        pm = ProviderManager._instance
        if pm and not pm.is_streaming:
            pm.chunk = ""
            pm.is_streaming = True
        if pm:
            pm.chunk += chunk

        message = {"type": message_type.value, "content": chunk, "agent": agent_name}

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

        logger.debug(f"Chunk written to stream: {chunk[:50]}...")

    async def close(self) -> None:
        """Signal the end of the stream to all clients."""
        message = {"type": "close", "content": None}

        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending close signal: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

        pm = ProviderManager._instance
        if pm:
            pm.is_streaming = False

        logger.debug("Stream close signal sent")


class StreamToolManager(StreamManager):
    """Tool-specific streaming manager.

    Uses the WebSocket-based StreamManager with the TOOL message type.
    """

    async def write(self, chunk: str, agent_name: str) -> None:
        """Write a tool output chunk to the stream."""
        await super().write(chunk, agent_name, MessageType.TOOL)
