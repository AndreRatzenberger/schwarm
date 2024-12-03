import asyncio

import websockets
from websockets.exceptions import ConnectionClosed

from schwarm.manager.websocket_messages import WebsocketMessage

clients = set()


class WebsocketManager2:
    """Manages WebSocket connections and message broadcasting."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to ensure only one instance of the manager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def send_message(self, message: WebsocketMessage) -> None:
        """Broadcast a message to all connected WebSocket clients."""
        if clients:
            print(f"Broadcasting message to {len(clients)} clients.")
            await asyncio.gather(*[self._send_safe(client, message) for client in clients])
        else:
            print("No clients connected.")

    async def _send_safe(self, client, message: WebsocketMessage):
        """Safely send a message to a client."""
        try:
            await client.send(message.json())  # Assuming `WebsocketMessage` has `.json()`
        except ConnectionClosed:
            print("Client disconnected.")
            clients.remove(client)

    async def handle_client(self, websocket):
        """Handle new WebSocket connection."""
        print("Client connected")
        clients.add(websocket)
        try:
            async for _ in websocket:  # Keep the connection alive
                pass
        finally:
            print("Client disconnected.")
            clients.remove(websocket)

    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(self.handle_client, "localhost", 8765)
        print("WebSocket server started on ws://localhost:8765")
        await self.server.wait_closed()
