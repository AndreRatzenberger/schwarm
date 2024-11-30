"""Example showcasing fluent API with DDD architecture."""

import asyncio
from typing import Any, Dict

from schwarm.agent_builder import AgentBuilder
from schwarm.events import Event, EventType
from schwarm.memory.service import MemoryService
from schwarm.providers.llm_provider import LLMProviderBuilder
from schwarm.tools.registry import ToolRegistry


async def main():
    """Example of using the fluent API."""
    
    # Create LLM provider with fluent API
    llm = (
        LLMProviderBuilder()
        .model("gpt-4")
        .temperature(0.7)
        .with_timeout(30)
        .with_retry(3)
        .with_cache(ttl=3600)
        .build()
    )
        
    # Initialize tool registry
    registry = ToolRegistry()
    
    # Create memory service
    memory = MemoryService(
        model_name="all-MiniLM-L6-v2",
        similarity_threshold=0.7
    )
    
    # Create agent with fluent builder
    agent = (
        AgentBuilder()
        .name("assistant")
        .with_instructions("You are a helpful assistant.")
        .with_provider(llm)
        .with_memory({
            "service": memory,
            "max_tokens": 1000
        })
        .build()
    )
        
    # Store memory with fluent API
    await (
        agent.memory.store("The capital of France is Paris")
        .with_metadata({
            "type": "fact",
            "source": "user"
        })
        .execute_store()
    )
    
    # Search memory
    memories = await (
        agent.memory.search("Paris")
        .limit(5)
        .with_threshold(0.8)
        .execute()
    )
        
    # Execute LLM with fluent API
    response = await llm.complete(
        "Tell me about neural networks",
        system_message="You are a helpful AI teacher."
    )
    
    # Set context variables
    await (
        agent.context.set("user_id", "123")
        .with_metadata({"source": "auth"})
        .execute_set()
    )
        
    # Get context with type checking
    user_id = await (
        agent.context.get("user_id")
        .with_default("anonymous")
        .with_type(str)
        .execute()
    )
        
    # Register tool with fluent API
    await (
        agent.tools.register(summarize_tool)
        .with_timeout(30)
        .with_retry(3)
        .with_cache(ttl=3600)
        .execute_registration()
    )
        
    # Execute tool
    result = await (
        agent.tools.execute("summarize")
        .with_args(text="Long text to summarize")
        .with_timeout(60)
        .execute_tool()
    )
        
    # Subscribe to events with fluent API
    (
        agent.events.on(EventType.TOOL_ERROR)
        .with_filter(lambda e: e.data["severity"] == "high")
        .do(handle_error)
    )


async def summarize_tool(context: Dict[str, Any], text: str) -> str:
    """Example tool implementation."""
    return f"Summary of: {text[:100]}..."


async def handle_error(event: Event) -> None:
    """Example error handler."""
    print(f"Error occurred: {event.data}")


if __name__ == "__main__":
    asyncio.run(main())
