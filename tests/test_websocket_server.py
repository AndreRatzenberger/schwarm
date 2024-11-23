"""Test websocket server for debugging and testing the WebDebugProvider."""

import asyncio
import json
import signal
import sys
from typing import Any, Set

import websockets
from loguru import logger
from websockets.legacy.server import WebSocketServerProtocol, serve


class TestWebSocketServer:
    """Simple websocket server that logs all received messages."""

    def __init__(self, host: str = "localhost", port: int = 8000):
        """Initialize the test websocket server."""
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.received_messages: list[dict[str, Any]] = []
        logger.remove()
        logger.add(sys.stdout, format="<green>{time:HH:mm:ss}</green> | {message}")

    async def handle_client(self, websocket: WebSocketServerProtocol) -> None:
        """Handle a client connection."""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    self.received_messages.append(data)
                    logger.info(f"Received event: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {message}")
        finally:
            self.clients.remove(websocket)

    async def start(self) -> None:
        """Start the websocket server."""
        self.server = await serve(self.handle_client, self.host, self.port)
        logger.info(f"WebSocket server running at ws://{self.host}:{self.port}")

        # Handle graceful shutdown
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(self.stop()))
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.create_task(self.stop()))

        try:
            await self.server.wait_closed()
        except asyncio.CancelledError:
            await self.stop()

    async def stop(self) -> None:
        """Stop the websocket server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("WebSocket server stopped")

    def get_received_messages(self) -> list[dict[str, Any]]:
        """Get all received messages."""
        return self.received_messages

    def clear_messages(self) -> None:
        """Clear the received messages list."""
        self.received_messages.clear()


async def main() -> None:
    """Run the test websocket server."""
    server = TestWebSocketServer()
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
