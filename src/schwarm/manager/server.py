import asyncio
from collections import deque

import websockets
from websockets.exceptions import ConnectionClosed

from schwarm.manager.websocket_messages import WebsocketMessage

clients = set()


class WebsocketManager2:
    """Manages WebSocket connections and message broadcasting."""

    _instance = None
    _message_queue = deque()  # Queue to store messages when no clients are connected

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
            print("No clients connected. Queuing message.")
            self._message_queue.append(message)

    async def _send_safe(self, client, message: WebsocketMessage):
        """Safely send a message to a client."""
        try:
            await client.send(message.json())  # Assuming `WebsocketMessage` has `.json()`
        except ConnectionClosed:
            print("Client disconnected.")
            clients.remove(client)

    async def _send_queued_messages(self, client):
        """Send all queued messages to a newly connected client."""
        if self._message_queue:
            print(f"Sending {len(self._message_queue)} queued messages to new client.")
            while self._message_queue:
                message = self._message_queue.popleft()
                try:
                    await client.send(message.json())
                except ConnectionClosed:
                    print("Client disconnected while sending queued messages.")
                    # Put remaining messages back in queue
                    self._message_queue.appendleft(message)
                    while self._message_queue:
                        self._message_queue.appendleft(self._message_queue.pop())
                    break

    async def handle_client(self, websocket):
        """Handle new WebSocket connection."""
        print("Client connected")
        clients.add(websocket)
        try:
            # Send any queued messages to the new client
            await self._send_queued_messages(websocket)

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
