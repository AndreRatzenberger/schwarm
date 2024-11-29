import asyncio
from collections.abc import AsyncGenerator
from threading import Lock
from typing import Any


class StreamManager:
    """Manages async and agent-specific streams."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.agent_streams = {}
            cls._instance.lock = Lock()
        return cls._instance

    def __init__(self):
        """Initialize the stream manager."""
        self.agent_streams = {}  # Stores async queues for each agent
        self.lock = Lock()

    def _get_or_create_queue(self, agent_name: str) -> asyncio.Queue:
        """Get or create an asyncio queue for an agent."""
        if agent_name not in self.agent_streams:
            self.agent_streams[agent_name] = asyncio.Queue()
        return self.agent_streams[agent_name]

    async def add_chunk(self, agent_name: str, chunk: str):
        """Add a chunk to the stream for an agent."""
        queue = self._get_or_create_queue(agent_name)
        await queue.put(chunk)

    async def end_stream(self, agent_name: str):
        """Signal the end of the stream for an agent."""
        queue = self._get_or_create_queue(agent_name)
        await queue.put(None)  # Use `None` as a sentinel to signal the end

    async def stream_messages(self, agent_name: str) -> AsyncGenerator[str, Any]:
        """Async generator for streaming messages for a specific agent."""
        queue = self._get_or_create_queue(agent_name)
        while True:
            chunk = await queue.get()
            if chunk is None:  # End of stream
                break
            yield chunk

    def reset_stream(self, agent_name: str):
        """Reset the stream for an agent."""
        with self.lock:
            if agent_name in self.agent_streams:
                del self.agent_streams[agent_name]
