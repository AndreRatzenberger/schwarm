from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.litellm_config import LiteLLMConfig
from schwarm.provider.zep_config import ZepConfig

# Easily define an agent with provider configurations


provider_agent = Agent(
    name="provider_agent", provider_configurations=[LiteLLMConfig(cache=True), ZepConfig(zep_api_key="zepzep")]
)

graphic_agent = Agent(
    name="provider_agent", provider_configurations=[LiteLLMConfig(cache=True), ImageGenerationConfig()]
)

# Create a dynamic system prompt for the agent


def instructions(context_variables: ContextVariables) -> str:
    """Return instructions for the agent."""
    zep = provider_registry.get_typed_provider(provider_agent, ZepProvider)
    saved_text = zep.get_saved_text()
    instruction_text = "I can provide information from the LiteLLM and Zep providers." + saved_text
    return instruction_text


provider_agent.instructions = instructions


# Define functions for the agent and go ham with the providers


def write_batch(context_variables: ContextVariables, text: str) -> Result:
    """Write down your story."""
    zep = provider_agent.get_typed_provider(ZepProvider)
    zep.memory.add(session_id="user_agent", messages=text)
    context_variables["book"] += text
    return Result(value=f"{text}", context_variables=context_variables, agent=graphic_agent)


def generate_image(context_variables: ContextVariables, text: str) -> Result:
    """Generate an image from text."""
    image_gen = graphic_agent.get_typed_provider(ImageGeneration)
    image = image.gen_image(text)
    return Result(value=image, context_variables=context_variables, agent=provider_agent)


provider_agent.functions = [generate_image]
graphic_agent.functions = [write_batch, generate_image]


# Let's take any agent and start it!

result = provider_agent.quickstart()


# Also define your own provider!


class ImageGenerationProvider(BaseEventHandleProvider):
    """Configuration for the ImageGeneration provider."""

    def set_up(self) -> None:
        """Set up the provider."""
        self.external_use = True  # This provider is for external use like in our case in functions outside of the agent

        # or set it up for internal use and define the methods that should be called on what event
        self.internal_use = {
            "on_start": [self.gen_image, self.initialise],
            "on_tool_use": [self.gen_image, self.some_other_method],
        }
