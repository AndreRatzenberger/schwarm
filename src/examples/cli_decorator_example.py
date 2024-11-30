"""Example demonstrating CLI decorator usage."""

import asyncio

from schwarm.agents.agent_builder import AgentBuilder
from schwarm.context.context import Context
from schwarm.functions.cli.decorators import cli_command, cli_param
from schwarm.providers.cli_llm_provider import CLILLMProvider


# Example 1: Explicit parameter definition
@cli_command(name="image-gen", description="Generate images from text descriptions")
@cli_param("-p", "The image description/prompt", required=True)
@cli_param("--style", "The style to generate in", choices=["realistic", "anime"])
async def generate_image(context: Context, p: str, style: str = "realistic") -> str:
    """Generate an image from a text prompt."""
    return f"Generated {style} image from prompt: {p}"


# Example 2: Lazy parameter creation from function signature
@cli_command(lazy=True)
async def search(
    context: Context, query: str, limit: int = 10, sort: str = "relevance", tags: list[str] | None = None
) -> list[str]:
    """Search for items in the database.

    Args:
        query: The search query string
        limit: Maximum number of results to return
        sort: Sort order (relevance, date, popularity)
        tags: Optional tags to filter results
    """
    tags_str = f" with tags {tags}" if tags else ""
    return [f"Result {i} for: {query} (sort: {sort}){tags_str}" for i in range(limit)]


# Example 3: Lazy parameter creation with minimal docstring
@cli_command(lazy=True)
async def summarize(context: Context, text: str, max_length: int = 100) -> str:
    """Summarize text to a specified length."""
    return f"Summary of '{text[:20]}...' with max length {max_length}"


async def main():
    # Create an agent with our CLI functions
    agent = (
        AgentBuilder("CLIAgent")
        .with_instructions("I am an agent that can generate images, search, and summarize text.")
        .with_function(generate_image)  # Explicit parameters
        .with_function(search)  # Lazy parameters
        .with_function(summarize)  # Lazy parameters
        .build()
    )

    # Initialize the agent
    await agent.initialize()

    # Example 1: Generate an image (explicit parameters)
    result = await agent.execute_function(
        "image-gen", context=agent.context, p="cat sitting on windowsill", style="anime"
    )
    print(f"\nImage Generation: {result}")

    # Example 2: Search with lazy parameters
    result = await agent.execute_function(
        "search", context=agent.context, query="python tutorials", limit=5, sort="date", tags=["beginner", "web"]
    )
    print(f"\nSearch: {result}")

    # Example 3: Summarize with lazy parameters
    result = await agent.execute_function(
        "summarize",
        context=agent.context,
        text="This is a long piece of text that needs to be summarized.",
        max_length=50,
    )
    print(f"\nSummary: {result}")

    # The agent's CLILLMProvider can also parse command strings
    provider = next(p for p in agent._providers if isinstance(p, CLILLMProvider))

    # Test command parsing for explicit parameters
    command1 = "image-gen -p 'dog in park' --style realistic"
    is_valid, error = await provider.validate_command(command1, agent._functions["image-gen"])

    if is_valid:
        result = await agent._functions["image-gen"].execute_cli(agent.context, command1)
        print(f"\nCLI Execution (explicit): {result}")

    # Test command parsing for lazy parameters
    command2 = "search --query 'python async' --limit 3 --sort date"
    is_valid, error = await provider.validate_command(command2, agent._functions["search"])

    if is_valid:
        result = await agent._functions["search"].execute_cli(agent.context, command2)
        print(f"\nCLI Execution (lazy): {result}")


if __name__ == "__main__":
    asyncio.run(main())
