# Schwarm Framework

An intuitive and powerful agent framework that lets you create and combine AI agents with different capabilities through providers.

## Core Concepts

### Agents & Providers

Agents in Schwarm are configurations rather than persistent objects. They define what capabilities (providers) they have access to and how they should behave.

```python
from schwarm.models.types import Agent
from schwarm.provider.configs import LiteLLMConfig, ZepConfig

# Create an agent with specific providers
research_agent = Agent(
    name="researcher",
    provider_configurations=[
        LiteLLMConfig(cache=True),
        ZepConfig(zep_api_key="your-key")
    ]
)
```

### Dynamic Instructions

Agents can have dynamic instructions that use their providers:

```python
def researcher_instructions(context: dict) -> str:
    """Dynamic instructions using providers."""
    zep = research_agent.get_typed_provider(ZepProvider)
    memory = zep.get_memory()
    return f"You are a researcher with access to this context: {memory}"

research_agent.instructions = researcher_instructions
```

### Tools & Provider Access

Tools can easily access any provider the agent has configured:

```python
def research_topic(context: dict, query: str) -> Result:
    """Research a topic using multiple providers."""
    llm = research_agent.get_typed_provider(LiteLLMProvider)
    zep = research_agent.get_typed_provider(ZepProvider)
    
    # Use providers with full type safety
    memory = zep.search_memory(query)
    response = llm.complete([f"Analyze this: {memory}"])
    
    return Result(value=response)

research_agent.functions = [research_topic]
```

### Agent Handoff

Agents can hand off tasks to other agents with different capabilities:

```python
image_agent = Agent(
    name="artist",
    provider_configurations=[
        LiteLLMConfig(cache=True),
        ImageGenerationConfig()
    ]
)

def analyze_then_draw(context: dict, topic: str) -> Result:
    """Research topic then generate image."""
    llm = research_agent.get_typed_provider(LiteLLMProvider)
    analysis = llm.complete([f"Analyze {topic}"])
    
    # Hand off to image agent
    return Result(
        value=analysis,
        context_variables=context,
        agent=image_agent  # Hands off to image agent
    )
```

## Creating Custom Providers

### Provider Types
Providers can be either external (used in tools) or internal (event-based):

```python
from enum import Enum
from typing import Callable, List

class EventType(Enum):
    START = "on_start"
    TOOL_USE = "on_tool_use"
    MESSAGE = "on_message"

class ImageGenerationProvider(BaseEventHandleProvider):
    def set_up(self) -> None:
        # For use in tools
        self.external_use = True
        
        # For internal event handling
        self.internal_use: dict[EventType, List[Callable]] = {
            EventType.START: [self.initialize_model],
            EventType.TOOL_USE: [self.generate_image]
        }
    
    def generate_image(self, prompt: str) -> str:
        """Generate image from prompt."""
        # Implementation
        pass
```

### Provider Configuration

Each provider needs a configuration:

```python
class ImageGenerationConfig(BaseProviderConfig):
    model: str = "stable-diffusion"
    api_key: str
    size: tuple[int, int] = (512, 512)
    
    def __init__(self, **data):
        super().__init__(
            provider_name="image_gen",
            provider_type="generation",
            **data
        )
```

## Running Agents

Start any agent with the quickstart method:

```python
# Simple start
result = research_agent.quickstart(
    "Research the history of AI"
)

# With specific configuration
result = research_agent.quickstart(
    input_text="Generate an image of a sunset",
    context_variables={"style": "watercolor"},
    mode="auto"  # or "interactive"
)
```

## Best Practices

1. **Provider Access**
   - Use `get_typed_provider()` for type-safe provider access
   - Keep provider usage close to where it's needed

2. **Agent Design**
   - Give agents focused capabilities
   - Use handoff for different tasks
   - Keep instructions dynamic

3. **Provider Design**
   - Clear separation between external and internal use
   - Type-safe event mappings
   - Clear configuration

## Example: Research & Visualization System

```python
# Create specialized agents
research_agent = Agent(
    name="researcher",
    provider_configurations=[
        LiteLLMConfig(cache=True),
        ZepConfig(zep_api_key="key")
    ]
)

viz_agent = Agent(
    name="visualizer",
    provider_configurations=[
        LiteLLMConfig(cache=True),
        ImageGenerationConfig(api_key="key"),
        PlotGenerationConfig()
    ]
)

# Research function
def analyze_topic(context: dict, topic: str) -> Result:
    llm = research_agent.get_typed_provider(LiteLLMProvider)
    zep = research_agent.get_typed_provider(ZepProvider)
    
    # Research
    memory = zep.search_memory(topic)
    analysis = llm.complete([f"Analyze: {topic}\nContext: {memory}"])
    
    # Hand off for visualization
    return Result(
        value=analysis,
        context_variables=context,
        agent=viz_agent
    )

# Visualization function
def create_visualization(context: dict, data: str) -> Result:
    image_gen = viz_agent.get_typed_provider(ImageGenerationProvider)
    plot_gen = viz_agent.get_typed_provider(PlotGenerationProvider)
    
    if "numerical_data" in data:
        viz = plot_gen.create_plot(data)
    else:
        viz = image_gen.generate_image(data)
    
    return Result(value=viz)

# Set up agents
research_agent.functions = [analyze_topic]
viz_agent.functions = [create_visualization]

# Run system
result = research_agent.quickstart("Research and visualize AI trends")
```

This shows how to create a complete system with specialized agents that work together through handoffs while maintaining clean, type-safe code.


Current todos:
 - Current orchestration happens with Schwarm.run(agent) instead with agent.run()
 - rework the shitty implenmentation right now into the elegant shit above