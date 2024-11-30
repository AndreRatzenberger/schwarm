graph TD
    %% Core Package
    Core[schwarma-core]
    style Core fill:#f9f,stroke:#333,stroke-width:2px

    %% Main Packages
    Agents[schwarma-agents]
    ProviderLLM[schwarma-provider-llm]
    ProviderCLI[schwarma-provider-cli]
    ProviderMongo[schwarma-provider-mongo]
    Telemetry[schwarma-telemetry]
    Functions[schwarma-functions]

    %% Dependencies
    Agents --> Core
    ProviderLLM --> Core
    ProviderCLI --> Core
    ProviderMongo --> Core
    Telemetry --> Core
    Functions --> Core

    %% Core Components
    CoreEvents[Events System]
    CoreProvider[Provider Interface]
    CoreFunction[Function Interface]
    CoreContext[Context Management]

    Core --> CoreEvents
    Core --> CoreProvider
    Core --> CoreFunction
    Core --> CoreContext

    %% Package Contents
    AgentsBuilder[Agent Builder]
    AgentsBase[Base Agent]
    Agents --> AgentsBuilder
    Agents --> AgentsBase

    ProviderLLM --> LLMImpl[LLM Implementation]
    ProviderCLI --> CLIImpl[CLI Implementation]
    ProviderMongo --> MongoImpl[MongoDB Implementation]

    TelemetryManager[Telemetry Manager]
    TelemetryExporters[Exporters]
    Telemetry --> TelemetryManager
    Telemetry --> TelemetryExporters

    %% External Dependencies
    ExtLiteLLM[litellm]
    ExtOpenTelemetry[opentelemetry]
    ExtPydantic[pydantic]
    ExtTyping[typing-extensions]

    ProviderLLM --> ExtLiteLLM
    Telemetry --> ExtOpenTelemetry
    Core --> ExtPydantic
    Core --> ExtTyping

    %% Styling
    classDef package fill:#f9f,stroke:#333,stroke-width:2px
    classDef component fill:#bbf,stroke:#333,stroke-width:1px
    classDef external fill:#ddd,stroke:#333,stroke-width:1px

    class Core,Agents,ProviderLLM,ProviderCLI,ProviderMongo,Telemetry,Functions package
    class CoreEvents,CoreProvider,CoreFunction,CoreContext,AgentsBuilder,AgentsBase,LLMImpl,CLIImpl,MongoImpl,TelemetryManager,TelemetryExporters component
    class ExtLiteLLM,ExtOpenTelemetry,ExtPydantic,ExtTyping external
```

# SchwarMA Package Dependencies

This diagram shows the dependencies between SchwarMA packages and their key components.

## Package Structure

- **schwarma-core**: The foundation package containing essential interfaces and systems
  - Events System
  - Provider Interface
  - Function Interface
  - Context Management

- **schwarma-agents**: Agent implementation package
  - Agent Builder
  - Base Agent Implementation
  - Dependencies: schwarma-core

- **schwarma-provider-llm**: LLM provider implementation
  - LLM Implementation
  - Dependencies: schwarma-core, litellm

- **schwarma-provider-cli**: CLI provider implementation
  - CLI Implementation
  - Dependencies: schwarma-core

- **schwarma-provider-mongo**: MongoDB provider implementation
  - MongoDB Implementation
  - Dependencies: schwarma-core

- **schwarma-telemetry**: Telemetry system package
  - Telemetry Manager
  - Various Exporters
  - Dependencies: schwarma-core, opentelemetry

- **schwarma-functions**: Common function implementations
  - Dependencies: schwarma-core

## External Dependencies

- **litellm**: Used by schwarma-provider-llm for LLM interactions
- **opentelemetry**: Used by schwarma-telemetry for tracing and monitoring
- **pydantic**: Used across packages for data validation
- **typing-extensions**: Used across packages for type hints

## Design Principles

1. **Minimal Core**: schwarma-core contains only essential interfaces and systems
2. **Independent Packages**: Each package can be used independently
3. **Single Responsibility**: Each package has a clear, focused purpose
4. **Clean Dependencies**: All packages depend only on schwarma-core
5. **Modular Providers**: Provider implementations in separate packages
