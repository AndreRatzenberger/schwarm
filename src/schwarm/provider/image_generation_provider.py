"""Provider for image generation with event handling."""

from typing import Any

from pydantic import Field

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig, ProviderScope


class ImageGenerationConfig(BaseProviderConfig):
    """Configuration for image generation provider."""

    model: str = Field(default="stable-diffusion", description="Model to use for generation")
    api_key: str = Field(..., description="API key for the service")
    size: tuple[int, int] = Field(default=(512, 512), description="Image size (width, height)")

    def __init__(self, **data):
        """Initialize with defaults."""
        data.update(
            {
                "provider_name": "image_gen",
                "provider_type": "generation",
                "provider_class": "schwarm.provider.image_generation_provider.ImageGenerationProvider",
                "scope": ProviderScope.AGENT,
            }
        )
        super().__init__(**data)


class ImageGenerationProvider(BaseEventHandleProvider):
    """Provider for generating images with event handling."""

    def __init__(self, config: ImageGenerationConfig):
        """Initialize the provider."""
        super().__init__(config)
        self.config: ImageGenerationConfig = config
        self.model = None

    def set_up(self) -> None:
        """Configure for both external use and event handling."""
        # Allow use in tools
        self.external_use = True

        # Set up event handlers
        self.internal_use = {
            EventType.START: [self.initialize_model],
            EventType.TOOL_EXECUTION: [self.generate_image],
            EventType.POST_TOOL_EXECUTION: [self.cleanup_generation],
        }

    def initialize_model(self) -> None:
        """Initialize the image generation model."""
        # Here you would initialize your actual model
        # For example with diffusers:
        # from diffusers import StableDiffusionPipeline
        # self.model = StableDiffusionPipeline.from_pretrained(
        #     self.config.model,
        #     use_auth_token=self.config.api_key
        # )
        pass

    def generate_image(self, prompt: str, **kwargs: dict[str, Any]) -> str:
        """Generate an image from a prompt.

        Args:
            prompt: Text description of the image to generate
            **kwargs: Additional generation parameters

        Returns:
            Path to the generated image
        """
        # Here you would use your model to generate the image
        # For example:
        # image = self.model(prompt).images[0]
        # path = f"generated_{hash(prompt)}.png"
        # image.save(path)
        # return path
        return f"Generated image from: {prompt}"

    def cleanup_generation(self, **kwargs: dict[str, Any]) -> None:
        """Clean up any temporary files or resources after generation."""
        pass

    def complete(self, messages: list[str]) -> str:
        """Override complete to use generate_image."""
        if not messages:
            raise ValueError("At least one message is required")
        return self.generate_image(messages[0])
