"""Example demonstrating CLI-style tool usage with LLMs."""

import asyncio

from schwarm.agents.agent import Agent
from schwarm.context.context import Context
from schwarm.functions.cli.cli_function import CLIFunction
from schwarm.functions.cli.command import Parameter
from schwarm.providers.cli_llm_provider import CLILLMProvider


async def generate_image(context: Context, p: str, style: str | None = "realistic") -> str:
    """Example function that simulates image generation.

    Args:
        context: The shared context
        p: The image prompt
        style: The style to generate in

    Returns:
        A message describing the generated image
    """
    return f"Generated {style} image from prompt: {p}"


def create_image_function() -> CLIFunction:
    """Create an example image generation function with CLI parameters."""
    return CLIFunction(
        name="image-gen",
        implementation=generate_image,
        description="Generate images from text descriptions",
        parameters=[
            Parameter("-p", "The image description/prompt", required=True),
            Parameter("--style", "The style to generate in", choices=["realistic", "anime"]),
        ],
    )


async def main() -> None:
    """Run the CLI tool example."""
    # Create the CLI-aware LLM provider
    provider = CLILLMProvider(model="gpt-3.5-turbo", temperature=0.7)

    # Create an agent with our CLI function
    image_function = create_image_function()
    agent = Agent(
        name="image-generator",
        instructions="You are an image generation assistant.",
        functions=[image_function],
        providers=[provider],
    )

    # Initialize the agent
    await agent.initialize()

    # Example user request
    user_request = "Generate an anime-style image of a cat sitting on a windowsill"

    # Step 1: Select the appropriate tool
    cli_provider = provider  # type: CLILLMProvider
    tool_name = await cli_provider.select_tool(
        user_request,
        [image_function],  # List of available CLI functions
    )

    # Get the selected tool
    tool = agent._functions.get(tool_name)
    if not isinstance(tool, CLIFunction):
        raise ValueError(f"Selected tool {tool_name} is not a CLI function")

    # Step 2: Generate the command
    command = await cli_provider.generate_command(user_request, tool)

    # Step 3: Validate the command
    is_valid, error = await cli_provider.validate_command(command, tool)

    # Step 4: Fix the command if needed
    while not is_valid and error:
        print(f"Invalid command: {error}")
        command = await cli_provider.fix_command(command, error, tool)
        is_valid, error = await cli_provider.validate_command(command, tool)

    # Step 5: Execute the command
    result = await tool.execute_cli(agent.context, command)
    print(f"\nResult: {result}")


if __name__ == "__main__":
    asyncio.run(main())
