# Schwarm Documentation

Welcome to the Schwarm documentation! This directory contains comprehensive documentation for the Schwarm agent framework.

## Documentation Structure

### [Concepts](concepts.md)
Core concepts and architecture of the framework:
- Agents and their capabilities
- Provider system overview
- Event system
- Architecture and design

### [Providers](providers.md)
Detailed documentation of the provider system:
- Provider types and lifecycles
- Event handling
- Built-in providers
- Creating custom providers
- Best practices

### [Examples](examples.md)
Practical examples and common patterns:
- Basic usage examples
- Advanced patterns
- Testing strategies
- Performance optimization
- Common solutions

## Quick Start

1. Install Schwarm:
```bash
pip install schwarm
```

2. Create a simple agent:
```python
from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent
from schwarm.provider.models.lite_llm_config import LiteLLMConfig

# Create agent
agent = Agent(
    name="my_agent",
    model="gpt-4",
    instructions="You are a helpful assistant.",
    providers=[
        LiteLLMConfig(
            provider_name="lite_llm",
            provider_lifecycle="singleton"
        )
    ]
)

# Run agent
schwarm = Schwarm()
response = schwarm.quickstart(
    agent=agent,
    input_text="Hello!",
    mode="auto"
)

print(response.messages[-1].content)
```

## Key Features

- **Modular Provider System**: Extend agent capabilities through providers
- **Event-Driven Architecture**: React to system events for complex behaviors
- **State Management**: Handle state through provider lifecycles
- **Tool Integration**: Execute functions and integrate with external systems
- **Budget Control**: Track and limit API costs
- **Debug Support**: Rich debugging and logging capabilities

## Best Practices

1. **Provider Usage**:
   - Use appropriate provider lifecycle modes
   - Combine providers for complex functionality
   - Handle provider events properly

2. **State Management**:
   - Use context provider for shared state
   - Clean up resources properly
   - Handle state transitions carefully

3. **Error Handling**:
   - Use debug provider for logging
   - Implement proper error recovery
   - Handle budget limits appropriately

4. **Testing**:
   - Mock providers for testing
   - Use appropriate test contexts
   - Test event handling thoroughly

## Contributing

1. **Adding Providers**:
   - Follow provider design patterns
   - Include proper documentation
   - Add tests for new functionality

2. **Documentation**:
   - Update relevant docs
   - Include examples
   - Follow documentation style

3. **Testing**:
   - Add unit tests
   - Include integration tests
   - Test with different configurations

## Support

- GitHub Issues: Report bugs and request features
- Documentation: Read detailed guides and examples
- Examples Directory: Check practical examples

## License

MIT License - See LICENSE file for details
