# Provider System

The provider system is the core extensibility mechanism in Schwarm. It allows agents to be enhanced with additional capabilities through a modular, event-driven architecture.

## Provider Types

### LLM Providers
Handle interactions with language models:
- Message completion
- Tool/function calling
- Model selection
- Caching
- Token counting

Example: LiteLLMProvider supports multiple LLM backends through a unified interface.

### Event Handler Providers
React to system events and provide functionality:
- Budget tracking
- Context management
- Debugging/logging
- State persistence
- API integration

Example: BudgetProvider tracks costs and token usage by handling message completion events.

## Provider Lifecycle

### Singleton
- One instance shared across all agents
- Good for shared resources (e.g., API clients)
- State persists across agent interactions
- Example: LLM provider with shared cache

```python
LiteLLMConfig(
    provider_name="lite_llm",
    provider_lifecycle="singleton",
    enable_cache=True
)
```

### Scoped
- New instance for each agent
- Good for agent-specific state
- State isolated between agents
- Example: Debug provider with agent-specific logs

```python
DebugProviderConfig(
    provider_name="debug",
    provider_lifecycle="scoped",
    save_logs=True
)
```

### Stateless
- Created on-demand
- No persistent state
- Good for pure functions/utilities
- Example: API provider for one-off calls

```python
ApiProviderConfig(
    provider_name="api",
    provider_lifecycle="stateless"
)
```

## Event System

### Core Events
1. **on_start**
   - When agent initializes
   - Set up resources
   - Initialize state

2. **on_handoff**
   - When switching agents
   - Transfer state
   - Clean up resources

3. **on_message_completion**
   - Before/after message processing
   - Track costs
   - Update context

4. **on_tool_execution**
   - Before/after tool calls
   - Provide tool context
   - Log execution

### Event Handling

Providers handle events by implementing handler methods:
```python
class MyProvider(BaseEventHandleProvider):
    def handle_start(self) -> None:
        """Handle agent start."""
        pass

    def handle_handoff(self, next_agent: Agent) -> Agent | None:
        """Handle agent handoff."""
        return next_agent

    def handle_message_completion(self) -> None:
        """Handle message completion."""
        pass

    def handle_tool_execution(self) -> None:
        """Handle tool execution."""
        pass
```

### Event Flow
1. Schwarm triggers event
2. Agent receives event
3. Agent's providers handle event
4. Results flow back to Schwarm

## Provider Context

Providers have access to shared context:
```python
class ProviderContext:
    message_history: list[Message]
    current_agent: Agent
    available_agents: dict[str, Agent]
    available_tools: list[AgentFunction]
    available_providers: dict[str, Any]
    context_variables: dict[str, Any]
```

### Using Context
```python
class MyProvider(BaseEventHandleProvider):
    def handle_message_completion(self) -> None:
        if not self.context:
            return
            
        # Access message history
        latest_message = self.context.message_history[-1]
        
        # Access context variables
        user_data = self.context.context_variables.get("user_data")
        
        # Access current agent
        agent_name = self.context.current_agent.name
```

## Built-in Providers

### LiteLLMProvider
- Unified LLM interface
- Multiple model support
- Caching
- Cost tracking

```python
LiteLLMConfig(
    provider_name="lite_llm",
    provider_lifecycle="singleton",
    enable_cache=True,
    api_key="your-key"
)
```

### BudgetProvider
- Cost tracking
- Token counting
- Usage limits
- CSV logging

```python
BudgetProviderConfig(
    provider_name="budget",
    provider_lifecycle="scoped",
    max_spent=10.0,
    max_tokens=1000,
    effect_on_exceed="warning"
)
```

### ContextProvider
- State management
- Variable sharing
- Message history
- Tool results

```python
ContextProviderConfig(
    provider_name="context",
    provider_lifecycle="scoped"
)
```

### DebugProvider
- Console output
- Function logging
- State inspection
- User interaction

```python
DebugProviderConfig(
    provider_name="debug",
    provider_lifecycle="scoped",
    show_instructions=True,
    show_function_calls=True,
    save_logs=True
)
```

## Creating Custom Providers

### 1. Create Config
```python
from pydantic import Field
from schwarm.provider.models import BaseEventHandleProviderConfig

class MyProviderConfig(BaseEventHandleProviderConfig):
    """Configuration for my provider."""
    
    my_setting: str = Field(
        default="default",
        description="Custom setting"
    )
    
    def __init__(self, **data):
        super().__init__(
            _provider_type="event",
            provider_name="my_provider",
            provider_lifecycle="scoped",
            **data
        )
```

### 2. Create Provider
```python
from schwarm.provider.base import BaseEventHandleProvider

class MyProvider(BaseEventHandleProvider):
    """Custom provider implementation."""
    
    config: MyProviderConfig
    
    def handle_start(self) -> None:
        """Handle agent start."""
        if not self.context:
            return
            
        # Initialize with config
        setting = self.config.my_setting
        
        # Access context
        agent = self.context.current_agent
        
        # Do something
        print(f"Starting {agent.name} with {setting}")
```

### 3. Use Provider
```python
agent = Agent(
    name="my_agent",
    providers=[
        MyProviderConfig(
            my_setting="custom value"
        )
    ]
)
```

## Best Practices

### Provider Design
1. **Single Responsibility**
   - Each provider should do one thing well
   - Split complex providers into smaller ones
   - Use composition over inheritance

2. **State Management**
   - Choose appropriate lifecycle
   - Clean up resources
   - Handle state transitions
   - Use context appropriately

3. **Error Handling**
   - Graceful degradation
   - Clear error messages
   - Proper logging
   - State recovery

4. **Event Handling**
   - Subscribe only to needed events
   - Keep handlers focused
   - Consider ordering
   - Handle partial failures

### Testing

1. **Mock Context**
```python
mock_context = ProviderContext(
    current_agent=mock_agent,
    message_history=[],
    context_variables={}
)
```

2. **Test Provider**
```python
def test_provider():
    # Create provider
    config = MyProviderConfig(my_setting="test")
    provider = MyProvider(mock_agent, config)
    
    # Set context
    provider.update_context(mock_context)
    
    # Test event handling
    provider.handle_start()
    
    # Assert expected behavior
    assert something_happened
```

3. **Integration Test**
```python
def test_provider_integration():
    # Create agent with provider
    agent = Agent(
        name="test",
        providers=[MyProviderConfig()]
    )
    
    # Run through Schwarm
    schwarm = Schwarm()
    response = schwarm.run(agent, messages=[...])
    
    # Assert expected results
    assert response.context_variables["something"] == expected
