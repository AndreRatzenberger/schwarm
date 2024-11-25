classDiagram
    %% Base Classes
    class BaseProvider {
        <<Abstract>>
    }
    class BaseProviderConfig {
        +Scope scope
        +bool enabled
    }

    %% Provider Types
    class BaseLLMProvider {
        <<Abstract>>
        +test_connection()*
        +async_complete()*
        +complete()*
    }
    class BaseEventHandleProvider {
        <<Abstract>>
        +handle_event()*
    }

    %% Concrete Implementations
    class LiteLLMProvider {
        +test_connection()
        +async_complete()
        +complete()
    }
    class BudgetProvider {
        +handle_event()
    }
    class DebugProvider {
        +handle_event()
    }
    class ZepProvider {
        +handle_event()
    }

    %% Provider Configs
    class LiteLLMConfig {
        +str llm_model_id
    }
    class BudgetConfig {
    }
    class DebugConfig {
    }
    class ZepConfig {
    }

    %% Relationships
    BaseProvider <|-- BaseLLMProvider
    BaseProvider <|-- BaseEventHandleProvider
    
    BaseLLMProvider <|-- LiteLLMProvider
    BaseEventHandleProvider <|-- BudgetProvider
    BaseEventHandleProvider <|-- DebugProvider
    BaseEventHandleProvider <|-- ZepProvider
    
    BaseProviderConfig <|-- LiteLLMConfig
    BaseProviderConfig <|-- BudgetConfig
    BaseProviderConfig <|-- DebugConfig
    BaseProviderConfig <|-- ZepConfig

    LiteLLMProvider o-- LiteLLMConfig
    BudgetProvider o-- BudgetConfig
    DebugProvider o-- DebugConfig
    ZepProvider o-- ZepConfig

    %% Error Classes
    class LiteLLMError {
        <<Exception>>
    }
    class ConfigurationError {
        <<Exception>>
    }
    class CompletionError {
        <<Exception>>
    }
    class ConnectionError {
        <<Exception>>
    }

    LiteLLMError <|-- ConfigurationError
    LiteLLMError <|-- CompletionError
    LiteLLMError <|-- ConnectionError
