sequenceDiagram
    participant App as Application
    participant Agent as Agent
    participant Provider as Provider
    participant Function as Function
    participant Event as Event System
    participant Telemetry as Telemetry
    participant Context as Context

    Note over App,Context: Initialization Flow
    App->>Agent: Create agent
    Agent->>Event: Register listeners
    Agent->>Provider: Initialize providers
    Provider-->>Event: Emit PROVIDER_INITIALIZED
    Event-->>Telemetry: Forward event
    
    Note over App,Context: Function Execution Flow
    App->>Agent: Execute function
    Agent->>Event: Emit BEFORE_FUNCTION_EXECUTION
    Event-->>Telemetry: Forward event
    Agent->>Function: Execute
    Function->>Context: Get/Set state
    Context-->>Event: Emit CONTEXT_UPDATED
    Event-->>Telemetry: Forward event
    Function-->>Agent: Return result
    Agent->>Event: Emit AFTER_FUNCTION_EXECUTION
    Event-->>Telemetry: Forward event
    
    Note over App,Context: Provider Execution Flow
    App->>Agent: Use provider
    Agent->>Event: Emit BEFORE_PROVIDER_EXECUTION
    Event-->>Telemetry: Forward event
    Agent->>Provider: Execute
    Provider->>Context: Get/Set state
    Context-->>Event: Emit CONTEXT_UPDATED
    Event-->>Telemetry: Forward event
    Provider-->>Agent: Return result
    Agent->>Event: Emit AFTER_PROVIDER_EXECUTION
    Event-->>Telemetry: Forward event

```

# SchwarMA Event Flow

This diagram illustrates the event-driven communication patterns in SchwarMA, showing how different components interact through the event system.

## Key Flows

### Initialization Flow
1. Application creates an agent
2. Agent registers event listeners
3. Agent initializes providers
4. Providers emit initialization events
5. Telemetry system records initialization

### Function Execution Flow
1. Application requests function execution
2. Agent emits pre-execution event
3. Function executes with access to context
4. Context updates trigger events
5. Agent emits post-execution event
6. All events are recorded by telemetry

### Provider Execution Flow
1. Application requests provider execution
2. Agent emits pre-execution event
3. Provider executes with access to context
4. Context updates trigger events
5. Agent emits post-execution event
6. All events are recorded by telemetry

## Benefits of Event-Driven Design

1. **Decoupled Components**
   - Components communicate through events
   - No direct dependencies between components
   - Easy to add new event listeners

2. **Comprehensive Monitoring**
   - All operations generate events
   - Complete audit trail
   - Easy to add new monitoring systems

3. **State Management**
   - Context changes are event-driven
   - All state changes are observable
   - Easy to track state mutations

4. **Extensibility**
   - New event types can be added
   - New listeners can be registered
   - New telemetry exporters can be added

5. **Debugging**
   - Clear operation flow
   - All events are recorded
   - Easy to trace issues

## Event Types

1. **Lifecycle Events**
   - AGENT_INITIALIZED
   - AGENT_DESTROYED

2. **Function Events**
   - BEFORE_FUNCTION_EXECUTION
   - AFTER_FUNCTION_EXECUTION
   - FUNCTION_ERROR

3. **Provider Events**
   - BEFORE_PROVIDER_EXECUTION
   - AFTER_PROVIDER_EXECUTION
   - PROVIDER_ERROR

4. **Context Events**
   - CONTEXT_UPDATED
   - CONTEXT_CLEARED

Each event carries:
- Event type
- Timestamp
- Source identifier
- Relevant data payload
- Context snapshot (when applicable)
