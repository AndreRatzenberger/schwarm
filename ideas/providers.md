# Schwarm Provider System

The provider system is the core extensibility mechanism in Schwarm. It enables both internal framework capabilities and external tool integration through a type-safe, event-driven architecture.

## Core Concepts

### Provider Manager
The central singleton that manages provider lifecycles and access:

```python
class ProviderManager:
    """Centralized provider management."""
    def get_provider(self, agent_id: str, provider_name: str) -> Optional[BaseProvider]: ...
    def get_typed_provider(self, agent_id: str, provider_name: str, 
                          provider_type: Type[P]) -> Optional[P]: ...
```

### Provider Scopes
```python
class ProviderScope(Enum):
    GLOBAL = "global"      # One instance for entire Schwarm runtime
    SCOPED = "scoped"      # New instance per agent configuration
    EPHEMERAL = "ephemeral"  # Created on demand, no state
```

### Event System
Type-safe event handling through modern Python features:

```python
class EventType(Enum):
    START = "on_start"
    HANDOFF = "on_handoff"
    MESSAGE_COMPLETION = "on_message_completion"
    TOOL_EXECUTION = "on_tool_execution"
    # ... more events

@dataclass
class Event(Generic[T]):
    """Type-safe event with payload."""
    type: EventType
    payload: T
```

## Provider Types

### 1. LLM Providers
Handle language model interactions with type safety:

```python
class LiteLLMProvider(BaseProvider):
    def complete(
        self,
        messages: list[Message],
        override_model: Optional[str] = None,
        tools: Optional[list[dict[str, Any]]] = None
    ) -> Message:
        """Generate completion with full type checking."""
```

Configuration:
```python
LiteLLMConfig(
    provider_name="lite_llm",
    scope=ProviderScope.GLOBAL,
    model_id="gpt-4",
    features=FeatureFlags(cache=True)
)
```

### 2. Event Handler Providers
React to system events with type-safe handlers:

```python
class BudgetProvider(ModernEventHandleProvider):
    @handles_event(EventType.MESSAGE_COMPLETION)
    def track_costs(self, event: Event[MessageCompletionData]) -> None:
        """Track costs with full type information."""
        completion = event.payload.messages[-1]
        self._update_costs(completion)
```

Configuration:
```python
BudgetProviderConfig(
    provider_name="budget",
    scope=ProviderScope.SCOPED,
    max_spent=10.0,
    max_tokens=1000
)
```

### 3. Tool Providers
External tools with type-safe provider access:

```python
@with_providers('zep', 'vector_store')
def advanced_search(
    providers: TypedProviderMap,
    context_variables: dict[str, Any],
    query: str
) -> Result:
    """Search with proper typing."""
    zep = providers['zep']  # Full IDE support
    vector_store = providers['vector_store']
    
    # Type-safe operations
    memory_results = zep.search_memory(query)
    vector_results = vector_store.search(query)
```

## Event Handling

### Event Data Types
```python
@dataclass
class HandoffData:
    next_agent: Agent
    current_agent: Agent
    context_variables: dict[str, Any]

@dataclass
class MessageCompletionData:
    messages: list[Message]
    context_variables: dict[str, Any]

@dataclass
class ToolExecutionData:
    tool_name: str
    args: dict[str, Any]
    context_variables: dict[str, Any]
```

### Handling Events
```python
class MyProvider(ModernEventHandleProvider):
    @handles_event(EventType.HANDOFF, priority=10)
    def handle_switch(self, event: Event[HandoffData]) -> Optional[InjectionTask]:
        """Handle agent switch with type safety."""
        if event.payload.next_agent.name == "target":
            return InjectionTask(
                target="agent",
                value="Pre-switch context"
            )

    @handles_event(EventType.MESSAGE_COMPLETION)
    def track_message(self, event: Event[MessageCompletionData]) -> None:
        """Track messages with type safety."""
        message = event.payload.messages[-1]
        self._log_message(message)
```

## Creating Custom Providers

### 1. Define Configuration
```python
class MyProviderConfig(BaseProviderConfig):
    """Provider configuration with validation."""
    
    setting: str = Field(
        default="default",
        description="Custom setting"
    )
    
    def __init__(self, **data):
        super().__init__(
            provider_name="my_provider",
            scope=ProviderScope.SCOPED,
            **data
        )
```

### 2. Implement Provider
```python
class MyProvider(ModernEventHandleProvider):
    config: MyProviderConfig
    
    @handles_event(EventType.START)
    def handle_start(self, event: Event[dict[str, Any]]) -> None:
        """Initialize with type safety."""
        setting = self.config.setting
        self._initialize(setting)
    
    @handles_event(EventType.MESSAGE_COMPLETION)
    def handle_message(self, event: Event[MessageCompletionData]) -> None:
        """Process messages with type safety."""
        for message in event.payload.messages:
            self._process(message)
```

### 3. Register and Use
```python
# Register with agent
agent = Agent(
    name="my_agent",
    provider_configurations=[
        MyProviderConfig(setting="custom")
    ]
)

# Use in tools
@with_providers('my_provider')
def my_tool(
    providers: TypedProviderMap,
    context_variables: dict[str, Any]
) -> Result:
    provider = providers['my_provider']  # Fully typed
    result = provider.do_something()
    return Result(value=result)
```

## Testing

### 1. Provider Tests
```python
def test_provider():
    # Create provider
    config = MyProviderConfig(setting="test")
    provider = MyProvider(config)
    
    # Create test event
    event = Event(
        type=EventType.START,
        payload={"test": "data"}
    )
    
    # Test handler
    result = provider.handle_event(event)
    assert result is not None
```

### 2. Tool Tests
```python
def test_tool():
    # Mock providers
    mock_providers = {
        'my_provider': Mock(spec=MyProvider)
    }
    
    # Test tool
    result = my_tool(
        providers=mock_providers,
        context_variables={'agent_id': 'test'}
    )
    
    assert result.value == expected
```

## Best Practices

1. **Type Safety**
   - Use typed event data
   - Define provider interfaces
   - Leverage IDE support

2. **Event Handling**
   - One handler per responsibility
   - Clear priority ordering
   - Proper error handling

3. **Provider Design**
   - Choose appropriate scope
   - Clean resource management
   - Clear configuration

4. **Tool Integration**
   - Use provider injection
   - Type-safe access
   - Clear error messages

5. **Testing**
   - Mock provider manager
   - Test event flow
   - Validate type safety