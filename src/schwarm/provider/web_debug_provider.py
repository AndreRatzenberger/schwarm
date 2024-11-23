import asyncio
import json
import threading
from typing import Any

import websockets
from loguru import logger
from pydantic import Field

from schwarm.events.event_data import Event
from schwarm.provider.base import BaseEventHandleProvider, BaseEventHandleProviderConfig
from schwarm.provider.provider_context import ProviderContext


class WebDebugConfig(BaseEventHandleProviderConfig):
    """Configuration for the websocket debug provider."""

    websocket_target: str = Field(default="ws://localhost:8123", description="Websocket endpoint to send events to")


def make_serializable(obj: Any) -> Any:
    """Recursively convert an object into a serializable format."""
    if isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(make_serializable(item) for item in obj)
    elif isinstance(obj, set):
        return [make_serializable(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        # For Pydantic models
        return make_serializable(obj.model_dump())
    elif callable(obj):
        # Handle callable objects (functions, methods)
        return f"<function {obj.__name__}>" if hasattr(obj, "__name__") else str(obj)
    elif hasattr(obj, "__dict__"):
        # For objects with __dict__, convert their attributes
        return {"__type__": obj.__class__.__name__, "attributes": make_serializable(obj.__dict__)}

    # Try json serialization as a test
    try:
        json.dumps(obj)
        return obj
    except (TypeError, OverflowError, ValueError):
        # If the object can't be serialized, convert it to string
        return str(obj)


class WebDebugProvider(BaseEventHandleProvider):
    """Websocket-based debug provider that sends system information to a websocket endpoint."""

    config: WebDebugConfig
    _provider_id: str = Field(default="web_debug", description="Provider ID")
    _websocket: Any = None
    _connect_lock: threading.Lock
    _initialized: bool = False
    _loop: asyncio.AbstractEventLoop
    _thread: threading.Thread

    def __init__(self, config: WebDebugConfig, **data: Any):
        """Initialize the websocket debug provider."""
        self.config = config
        self._websocket = None
        self._connect_lock = threading.Lock()
        self._initialized = False
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._start_event_loop, daemon=True)
        self._thread.start()
        super().__init__(config, **data)

    def _start_event_loop(self):
        """Start the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _ensure_connection(self) -> None:
        """Ensure websocket connection is established."""
        async with asyncio.Lock():
            if self._websocket is None:
                try:
                    self._websocket = await websockets.connect(
                        self.config.websocket_target,
                        ping_interval=None,  # Disable ping to avoid connection issues
                    )
                    logger.info(f"Connected to websocket at {self.config.websocket_target}")
                except Exception as e:
                    logger.error(f"Failed to connect to websocket: {e}")
                    self._websocket = None
                    raise e

    async def _send_event(self, event: Event) -> None:
        """Send event to websocket endpoint."""
        await self._ensure_connection()
        if self._websocket is None:
            raise ConnectionError("Websocket connection is not available.")

        try:
            # Convert the event to a serializable format
            event_data = {
                "type": event.type.value,
                "payload": make_serializable(event.payload),
                "agent_id": event.agent_id,
                "datetime": event.datetime,
            }

            # Serialize the event data
            event_json = json.dumps(event_data)

            # Send the event data
            await self._websocket.send(event_json)
            logger.debug(f"Sent event to websocket: {event.type}")
        except Exception as e:
            logger.error(f"Failed to send event to websocket: {e}")
            self._websocket = None
            raise e

    def initialize(self) -> None:
        """Initialize the websocket debug provider."""
        if not self._initialized:
            logger.info(f"Initializing websocket debug provider with target: {self.config.websocket_target}")
            self._initialized = True

    def handle_event(self, event: Event) -> ProviderContext:
        """Handle events by sending them to the websocket endpoint."""
        self.event_log.append(event)
        asyncio.run_coroutine_threadsafe(self._send_event(event), self._loop)
        return event.payload

    async def cleanup(self) -> None:
        """Clean up websocket connection."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("Closed websocket connection")
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()
