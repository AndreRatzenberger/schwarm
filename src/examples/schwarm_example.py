"""Example demonstrating the use of the Schwarm framework."""

import asyncio

from schwarm.events.events import Event


async def log_event(event: Event) -> None:
    """Simple event listener that logs events to the console."""
    print(f"Event: {event.type.name}")
    if event.data:
        print(f"Data: {event.data}")
    print("---")


async def main() -> None:
    pass


if __name__ == "__main__":
    asyncio.run(main())
