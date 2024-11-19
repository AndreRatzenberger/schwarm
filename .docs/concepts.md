# Schwarm Agent Framework

Schwarm is a flexible and extensible agent framework designed for building complex AI agent systems. It provides a robust foundation for creating, managing, and orchestrating AI agents with a focus on modularity and extensibility through its provider-based architecture.

## Core Concepts

### Agents

Agents are the core building blocks of the Schwarm framework. Each agent:
- Has a specific role and set of capabilities
- Can use multiple providers for extended functionality
- Can communicate with other agents
- Can execute tools/functions
- Maintains its own state and context

Key agent features:
- **Instructions**: Static or dynamic instructions that define the agent's behavior
- **Tools**: Functions the agent can call to perform actions
- **Providers**: Modular components that add capabilities to the agent
- **Model**: The underlying LLM model used by the agent
- **Context**: Access to shared state and message history

### Providers

Providers are modular components that add capabilities to agents. The provider system is designed to be:
- **Extensible**: Easy to add new provider types
- **Modular**: Each provider handles a specific concern
- **Event-driven**: Providers react to system events
- **Lifecycle-aware**: Providers can be singleton, scoped, or stateless

Built-in providers include:
- **LLM Providers**: Handle interactions with language models
- **Budget Provider**: Tracks API costs and token usage
- **Context Provider**: Manages shared state and context
- **Debug Provider**: Handles logging and display
- **API Provider**: Provides external API access
- **Message Bus Provider**: Handles inter-agent communication
- **Zep Provider**: Provides infinite memory capabilities

### Event System

The event system enables providers to react to key points in the agent lifecycle:
- **on_start**: When an agent starts
- **on_handoff**: When transitioning between agents
- **on_message_completion**: Before/after message processing
- **on_tool_execution**: Before/after tool execution

Events flow from the Schwarm orchestrator through agents to their providers, allowing providers to:
- Monitor agent activities
- Modify behavior at key points
- Maintain state
- Coordinate with other providers

### Provider Lifecycle

Providers support three lifecycle modes:
1. **Singleton**: One instance shared across all agents
2. **Scoped**: New instance for each agent
3. **Stateless**: Created on-demand

This allows for flexible state management:
- Share state across agents (singleton)
- Isolate state per agent (scoped)
- Avoid state entirely (stateless)

## Architecture

### Core Components

```
schwarm/
├── core/           # Core framework components
│   ├── schwarm.py  # Main orchestration engine
│   └── tools.py    # Tool handling system
├── models/         # Data models and types
├── provider/       # Provider system
│   ├── base/       # Base provider classes
│   └── models/     # Provider configurations
└── utils/          # Utility functions
```

### Provider Architecture

The provider system uses a layered architecture:
1. **Base Provider**: Core provider functionality
2. **Event Handler**: Event system integration
3. **Specific Providers**: Concrete implementations

Each provider:
- Has a configuration class defining its settings
- Inherits from appropriate base classes
- Implements needed event handlers
- Has access to agent context

### Event Flow

1. Schwarm orchestrator triggers events
2. Events flow to the current agent
3. Agent dispatches to its providers
4. Providers handle events they care about
5. Results flow back up the chain

## Usage Examples

### Creating an Agent

```python
from schwarm.models.types import Agent
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.provider.models.debug_provider_config import DebugProviderConfig

agent = Agent(
    name="my_agent",
    model="gpt-4",
    instructions="You are a helpful agent",
    providers=[
        LiteLLMConfig(
            provider_name="lite_llm",
            provider_lifecycle="singleton"
        ),
        DebugProviderConfig(
            provider_name="debug",
            provider_lifecycle="scoped"
        )
    ]
)
```

### Running an Agent

```python
from schwarm.core.schwarm import Schwarm
from schwarm.models.message import Message

schwarm = Schwarm()
response = schwarm.run(
    agent=agent,
    messages=[Message(role="user", content="Hello!")],
    context_variables={},
    max_turns=10
)
```

### Creating a Custom Provider

```python
from schwarm.provider.base.base_event_handle_provider import BaseEventHandleProvider

class MyProvider(BaseEventHandleProvider):
    """Custom provider that handles specific events."""
    
    def handle_message_completion(self) -> None:
        """Handle message completion event."""
        if not self.context:
            return
            
        # Access context data
        latest_message = self.context.message_history[-1]
        
        # Do something with the message
        print(f"Message from {latest_message.sender}: {latest_message.content}")
```

## Best Practices

1. **Provider Design**:
   - Keep providers focused on a single responsibility
   - Use appropriate lifecycle mode for state management
   - Handle relevant events explicitly
   - Use context for accessing shared data

2. **Agent Design**:
   - Give agents clear, specific roles
   - Use appropriate providers for needed capabilities
   - Structure instructions clearly
   - Consider tool parallelization needs

3. **Event Handling**:
   - Subscribe only to needed events
   - Keep event handlers focused
   - Use proper error handling
   - Consider event ordering

4. **State Management**:
   - Use context for shared state
   - Choose appropriate provider lifecycle
   - Handle state transitions in handoffs
   - Clean up state when needed

## Advanced Features

### Tool Parallelization

Agents can execute tools in parallel when:
- `parallel_tool_calls=True` is set
- Tools are independent
- Provider support exists

### Budget Tracking

The budget provider offers:
- Cost tracking
- Token counting
- Usage limits
- CSV logging

### Debug Support

The debug provider provides:
- Rich console output
- Function call logging
- State inspection
- User interaction points

### Context Management

The context provider manages:
- Shared variables
- Message history
- Agent state
- Tool results

## Extending the Framework

### Adding New Providers

1. Create provider config:
```python
from schwarm.provider.models import BaseEventHandleProviderConfig

class MyProviderConfig(BaseEventHandleProviderConfig):
    """Configuration for my provider."""
    
    my_setting: str = "default"
```

2. Create provider class:
```python
from schwarm.provider.base import BaseEventHandleProvider

class MyProvider(BaseEventHandleProvider):
    """My custom provider."""
    
    config: MyProviderConfig
    
    def handle_start(self) -> None:
        """Handle agent start."""
        print(f"Starting with setting: {self.config.my_setting}")
```

3. Register provider:
```python
agent = Agent(
    name="my_agent",
    providers=[
        MyProviderConfig(
            provider_name="my_provider",
            provider_lifecycle="scoped",
            my_setting="custom"
        )
    ]
)
```

### Custom Event Types

While the framework provides core events, you can add custom events:

1. Define event in provider:
```python
def trigger_custom_event(self, **kwargs):
    """Trigger a custom event."""
    self.handle_event("custom_event", **kwargs)
```

2. Handle in other providers:
```python
def handle_custom_event(self, **kwargs):
    """Handle custom event."""
    print(f"Custom event with data: {kwargs}")
```

## Testing

The framework is designed for testability:
- No global state
- Clear component boundaries
- Event-driven architecture
- Mockable providers

Example test:
```python
def test_agent_with_mock_provider():
    # Create mock provider
    mock_provider = MockProvider()
    
    # Create agent with mock
    agent = Agent(
        name="test_agent",
        providers=[mock_provider.config]
    )
    
    # Run agent
    schwarm = Schwarm()
    response = schwarm.run(agent, messages=[...])
    
    # Assert provider was called
    assert mock_provider.handle_start.called
