"""Example demonstrating the use of the Schwarm framework."""

import asyncio
import os
from typing import Optional


from schwarm.agents.agents.agent_builder import AgentBuilder
from schwarm.events.events import Event, EventType
from schwarm.functions.text_functions import summarize_function
from schwarm.providers.simple_llm_provider import SimpleLLMProvider


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