"""Example demonstrating event-based provider usage."""

from schwarm.models.types import Agent, Result
from schwarm.provider.image_generation_provider import ImageGenerationConfig, ImageGenerationProvider


def generate_art_instructions(context: dict) -> str:
    """Dynamic instructions for art generation."""
    return "You are an AI artist that specializes in creating " "unique and creative images based on text descriptions."


def create_artwork(context: dict, description: str) -> Result:
    """Create artwork using the image generation provider."""
    agent = context.get("agent")
    if not agent:
        raise ValueError("Agent not provided in context")

    # Get the image generation provider
    image_gen = agent.get_typed_provider(ImageGenerationProvider)

    # Generate the image
    image_path = image_gen.generate_image(description)

    return Result(value=f"Created artwork at: {image_path}", context_variables=context)


def main():
    # Create an art generation agent
    art_agent = Agent(
        name="artist",
        provider_configurations=[ImageGenerationConfig(api_key="your-api-key", size=(1024, 1024))],
        instructions=generate_art_instructions,
    )

    # Add the art generation function
    art_agent.functions = [create_artwork]
    # Run the agent
    result = art_agent.quickstart(
        "Create a surreal landscape with floating islands and crystal waterfalls",
        context_variables={"agent": art_agent},
    )

    print(result.value)


if __name__ == "__main__":
    main()
