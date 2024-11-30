# Schwarm Framework

A powerful and intuitive Python framework for creating and combining AI agents with diverse capabilities through providers.

## Features

- **Modular Design**: Clear separation of components for independent development and maintenance
- **Extensible Architecture**: Easy addition of new functionalities through providers and functions
- **Fluent API**: Intuitive builder pattern for constructing agents
- **Event-Driven**: Built-in event system for monitoring and extending agent behavior
- **Type-Safe**: Comprehensive type hints for better development experience
- **Well-Tested**: Extensive test suite ensuring reliability

## Installation

```bash
pip install schwarm
```

## Quick Start

Here's a simple example of using the Schwarm Framework to create an agent that can summarize text:

```python
import asyncio
import os
from schwarm.agent_builder import AgentBuilder
from schwarm.providers.llm_provider import LLMProvider
from schwarm.functions.summarize_function import summarize_function

async def main():
    # Create an LLM provider
    provider = LLMProvider(
        model="gpt-3.5-turbo",
        temperature=0.7
    )
    
    # Build an agent with the provider and summarize function
    agent = (
        AgentBuilder("SummarizerAgent")
        .with_instructions("I am an agent specialized in summarizing text.")
        .with_provider(provider)
        .with_function(summarize_function)
        .build()
    )
    
    # Initialize the agent
    await agent.initialize()
    
    # Store the provider in context for the function to use
    agent.context.set("llm_provider", provider)
    
    # Use the agent to summarize text
    text = """
    Artificial Intelligence (AI) is a broad field of computer science focused on 
    creating intelligent machines that can perform tasks typically requiring human 
    intelligence. These tasks include visual perception, speech recognition, 
    decision-making, and problem-solving.
    """
    
    summary = await agent.execute_function(
        "summarize",
        text,
        max_length=50  # Target length in words
    )
    
    print(f"Summary: {summary}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Core Components

### Agent

The central component that orchestrates behavior and manages state:

```python
from schwarm.agent_builder import AgentBuilder

agent = (
    AgentBuilder("MyAgent")
    .with_instructions("Agent instructions here")
    .with_function(my_function)
    .with_provider(my_provider)
    .build()
)
```

### Function

Encapsulates discrete actions that agents can perform:

```python
from schwarm.function import Function

def greet(context, name: str) -> str:
    return f"Hello, {name}!"

greet_function = Function(
    name="greet",
    implementation=greet,
    description="Greets a user by name"
)
```

### Provider

Interfaces with external capabilities:

```python
from schwarm.provider import Provider

class MyProvider(Provider):
    async def initialize(self) -> None:
        # Setup code here
        pass
        
    async def execute(self, *args, **kwargs):
        # Implementation here
        return "result"
```

### Context

Manages shared state:

```python
from schwarm.context import Context

context = Context()
context.set("user_name", "Alice")
name = context.get("user_name")
```

### Event System

Enables monitoring and middleware:

```python
from schwarm.events import Event, EventType

async def log_execution(event: Event):
    print(f"Function executed: {event.data}")

agent.event_dispatcher.add_listener(
    EventType.AFTER_FUNCTION_EXECUTION,
    log_execution
)
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/schwarm.git
cd schwarm
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Documentation

For more detailed documentation, see the [docs](docs/) directory.

## Examples

Check out the [examples](examples/) directory for more usage examples:

- Basic agent creation
- Custom provider implementation
- Event handling
- Complex function composition
- And more!

## Support

- Issue Tracker: GitHub Issues
- Documentation: [docs/](docs/)
- Community: [Discussions](https://github.com/yourusername/schwarm/discussions)

## Project Status

This project is actively maintained and welcomes contributions. See the [CONTRIBUTING.md](CONTRIBUTING.md) file for more details on how to contribute.
