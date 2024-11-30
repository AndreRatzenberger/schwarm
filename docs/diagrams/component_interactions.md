graph TD
    %% Core Components
    subgraph Core[schwarma-core]
        Provider[Provider Interface]
        Function[Function Interface]
        Event[Event System]
        Context[Context]
        
        Event --> Context
    end

    %% Agent Components
    subgraph Agents[schwarma-agents]
        AgentBuilder[Agent Builder]
        BaseAgent[Base Agent]
        
        AgentBuilder --> BaseAgent
        BaseAgent --> Provider
        BaseAgent --> Function
        BaseAgent --> Event
        BaseAgent --> Context
    end

    %% Provider Implementations
    subgraph Providers[Provider Implementations]
        LLMProvider[LLM Provider]
        CLIProvider[CLI Provider]
        MongoProvider[MongoDB Provider]
        
        LLMProvider --> Provider
        CLIProvider --> Provider
        MongoProvider --> Provider
        
        LLMProvider --> Event
        CLIProvider --> Event
        MongoProvider --> Event
    end

    %% Telemetry System
    subgraph Telemetry[schwarma-telemetry]
        TelemetryManager[Telemetry Manager]
        Exporters[Telemetry Exporters]
        
        TelemetryManager --> Event
        TelemetryManager --> Exporters
        
        FileExporter[File Exporter]
        JaegerExporter[Jaeger Exporter]
        SQLiteExporter[SQLite Exporter]
        
        Exporters --> FileExporter
        Exporters --> JaegerExporter
        Exporters --> SQLiteExporter
    end

    %% Function Implementations
    subgraph Functions[schwarma-functions]
        CommonFunctions[Common Functions]
        CLIFunctions[CLI Functions]
        
        CommonFunctions --> Function
        CLIFunctions --> Function
        CLIFunctions --> CLIProvider
    end

    %% Interactions
    BaseAgent -.-> LLMProvider
    BaseAgent -.-> CLIProvider
    BaseAgent -.-> MongoProvider
    BaseAgent -.-> CommonFunctions
    BaseAgent -.-> CLIFunctions

    %% Event Flow
    Event -.-> TelemetryManager
    
    %% Styling
    classDef interface fill:#f9f,stroke:#333,stroke-width:2px
    classDef component fill:#bbf,stroke:#333,stroke-width:1px
    classDef implementation fill:#dfd,stroke:#333,stroke-width:1px
    
    class Provider,Function,Event,Context interface
    class AgentBuilder,BaseAgent,TelemetryManager,Exporters component
    class LLMProvider,CLIProvider,MongoProvider,FileExporter,JaegerExporter,SQLiteExporter,CommonFunctions,CLIFunctions implementation

```

# SchwarMA Component Interactions

This diagram illustrates how different components within SchwarMA interact with each other through interfaces and events.

## Key Interactions

1. **Core Interfaces**
   - Provider Interface: Base contract for all providers
   - Function Interface: Base contract for executable capabilities
   - Event System: Communication backbone
   - Context: Shared state management

2. **Agent System**
   - Agent Builder: Constructs agents with desired capabilities
   - Base Agent: Orchestrates providers and functions
   - Interacts with all core interfaces

3. **Provider Implementations**
   - All providers implement the Provider interface
   - Providers emit events through the Event System
   - Each provider has a specific responsibility:
     * LLM Provider: Language model interactions
     * CLI Provider: Command-line operations
     * MongoDB Provider: Database operations

4. **Telemetry System**
   - Listens to events from all components
   - Manages multiple exporters
   - Provides different storage/transmission options:
     * File Exporter: Local file storage
     * Jaeger Exporter: Distributed tracing
     * SQLite Exporter: Local database storage

5. **Function Implementations**
   - Common Functions: Reusable capabilities
   - CLI Functions: Command-line specific functions
   - All functions implement the Function interface

## Design Benefits

1. **Loose Coupling**
   - Components interact through interfaces
   - Event-driven communication
   - Easy to add new implementations

2. **Modularity**
   - Clear component boundaries
   - Independent scaling
   - Pluggable implementations

3. **Observability**
   - Centralized event system
   - Comprehensive telemetry
   - Multiple export options

4. **Extensibility**
   - New providers can be added
   - New functions can be implemented
   - New exporters can be created
