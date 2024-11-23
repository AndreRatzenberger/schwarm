"""Websocket-based debug provider for sending system information to a websocket endpoint."""

import asyncio
import json
import subprocess
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


class WebDebugProvider(BaseEventHandleProvider):
    """Websocket-based debug provider that sends system information to a websocket endpoint."""

    config: WebDebugConfig
    _provider_id: str = Field(default="web_debug", description="Provider ID")
    _websocket: Any = None
    _connect_lock: asyncio.Lock
    _initialized: bool = False

    def __init__(self, config: WebDebugConfig, **data: Any):
        """Initialize the websocket debug provider."""
        subprocess.run(["npm", "run", "dev"], cwd="src/websocket_ui")

        self.config = config
        self._websocket = None
        self._connect_lock = asyncio.Lock()
        self._initialized = False
        super().__init__(config, **data)

    async def _ensure_connection(self) -> None:
        """Ensure websocket connection is established."""
        async with self._connect_lock:
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
                    raise

    async def _send_event(self, event: Event) -> None:
        """Send event to websocket endpoint."""
        try:
            await self._ensure_connection()
            if self._websocket:
                event_data = {
                    "type": event.type.value,
                    "payload": event.payload,
                    "agent_id": event.agent_id,
                    "datetime": event.datetime,
                }
                await self._websocket.send(json.dumps(event_data))
                logger.debug(f"Sent event to websocket: {event.type}")
            else:
                logger.warning("Websocket connection not available")
        except Exception as e:
            logger.error(f"Failed to send event to websocket: {e}")
            self._websocket = None

    def initialize(self) -> None:
        """Initialize the websocket debug provider."""
        if not self._initialized:
            logger.info(f"Initializing websocket debug provider with target: {self.config.websocket_target}")
            self._initialized = True

    async def handle_event(self, event: Event) -> ProviderContext:
        """Handle events by sending them to the websocket endpoint."""
        self.event_log.append(event)
        await self._send_event(event)
        input("wait....")
        return event.payload

    async def cleanup(self) -> None:
        """Clean up websocket connection."""
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
            logger.info("Closed websocket connection")
