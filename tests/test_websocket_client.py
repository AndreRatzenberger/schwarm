"""Test client to demonstrate the WebDebugProvider."""

import asyncio
from datetime import datetime

from schwarm.events.event_data import Event, EventType
from schwarm.provider.web_debug_provider import WebDebugConfig, WebDebugProvider


async def main():
    """Run test client that sends various events."""
    # Create provider
    config = WebDebugConfig(websocket_target="ws://localhost:8123")
    provider = WebDebugProvider(config=config)

    # Initialize provider
    provider.initialize()

    try:
        # Send a series of test events
        events = [
            Event(
                type=EventType.START,
                payload={"message": "Starting test sequence"},
                agent_id="test_client",
                datetime=datetime.now().isoformat()
            ),
            Event(
                type=EventType.MESSAGE_COMPLETION,
                payload={"message": "Processing message", "status": "success"},
                agent_id="test_client",
                datetime=datetime.now().isoformat()
            ),
            Event(
                type=EventType.TOOL_EXECUTION,
                payload={"tool": "calculator", "input": "2+2", "result": "4"},
                agent_id="test_client",
                datetime=datetime.now().isoformat()
            )
        ]

        for event in events:
            await provider.handle_event(event)
            # Wait a bit between events to see them clearly
            await asyncio.sleep(1)

    finally:
        # Clean up
        await provider.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
