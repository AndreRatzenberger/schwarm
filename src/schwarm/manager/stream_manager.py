import asyncio
from collections.abc import AsyncIterator
from contextlib import contextmanager
from typing import Optional

from loguru import logger


class StreamManager:
    """Manages streaming of LLM outputs using async iterator pattern.

    This implementation provides:
    - Clean async iteration interface
    - Proper resource cleanup
    - Memory efficient streaming
    - Easy integration with FastAPI
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
        self._queue = asyncio.Queue()
        self._is_streaming = False
        logger.debug("StreamManager initialized")

    async def write(self, chunk: str) -> None:
        """Write a chunk to the stream.

        Args:
            chunk: Text chunk to stream
        """
        if chunk:  # Avoid empty chunks
            await self._queue.put(chunk)
            logger.debug(f"Chunk written to stream: {chunk[:50]}...")

    async def close(self) -> None:
        """Signal the end of the stream."""
        await self._queue.put(None)
        self._is_streaming = False
        logger.debug("Stream closed")

    def reset(self) -> None:
        """Reset the stream state."""
        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._is_streaming = False
        logger.debug("Stream reset")

    async def stream_messages(self) -> AsyncIterator[str]:
        """Stream messages as an async iterator."""
        self._is_streaming = True
        try:
            while self._is_streaming:
                chunk = await self._queue.get()
                if chunk is None:
                    break
                yield chunk
        except asyncio.CancelledError:
            self._is_streaming = False
            logger.warning("Stream iteration cancelled")
            raise
        except Exception as e:
            self._is_streaming = False
            logger.error(f"Error during stream iteration: {e}")
            raise
        finally:
            self._is_streaming = False
            logger.debug("Stream iteration ended")


class StreamToolManager:
    """Manages streaming of LLM outputs using async iterator pattern.

    This implementation provides:
    - Clean async iteration interface
    - Proper resource cleanup
    - Memory efficient streaming
    - Easy integration with FastAPI
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
        self._queue = asyncio.Queue()
        self._is_streaming = False
        logger.debug("StreamManager initialized")

    async def write(self, chunk: str) -> None:
        """Write a chunk to the stream.

        Args:
            chunk: Text chunk to stream
        """
        if chunk:  # Avoid empty chunks
            await self._queue.put(chunk)
            logger.debug(f"Chunk written to stream: {chunk[:50]}...")

    async def close(self) -> None:
        """Signal the end of the stream."""
        await self._queue.put(None)
        self._is_streaming = False
        logger.debug("Stream closed")

    def reset(self) -> None:
        """Reset the stream state."""
        # Clear the queue
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self._is_streaming = False
        logger.debug("Stream reset")

    async def stream_messages(self) -> AsyncIterator[str]:
        """Stream messages as an async iterator."""
        self._is_streaming = True
        try:
            while self._is_streaming:
                chunk = await self._queue.get()
                if chunk is None:
                    break
                yield chunk
        except asyncio.CancelledError:
            self._is_streaming = False
            logger.warning("Stream iteration cancelled")
            raise
        except Exception as e:
            self._is_streaming = False
            logger.error(f"Error during stream iteration: {e}")
            raise
        finally:
            self._is_streaming = False
            logger.debug("Stream iteration ended")


class AsyncLoopManager:
    """Manages async event loops for synchronous contexts."""

    _instance: Optional["AsyncLoopManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loop = None
        return cls._instance

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop

    def run_async(self, coro):
        """Run an async coroutine in the current loop."""
        try:
            return self.loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Error running async code: {e}")
            raise

    @contextmanager
    def loop_context(self):
        """Context manager for handling event loops."""
        loop = self.loop
        try:
            yield loop
        finally:
            if not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending))
