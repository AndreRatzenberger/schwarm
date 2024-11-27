classDiagram
    class BaseProviderConfig {
        +Scope scope
        +bool enabled
    }

    class BaseLLMProviderConfig {
        +str llm_model_id
    }

    class BaseProvider {
        <<Abstract>>
        -str _provider_id
        +ProviderContext context
        +bool is_enabled
        +update_context(context)
        +get_context()
    }

    class BaseLLMProvider {
        <<Abstract>>
        +test_connection()* bool
        +async_complete(messages, override_model, stream)* Message
        +complete(messages, override_model, tools, tool_choice)* Message
    }

    class ABC {
        <<Abstract>>
    }

    BaseProviderConfig <|-- BaseLLMProviderConfig
    ABC <|-- BaseProvider
    BaseProvider <|-- BaseLLMProvider
    BaseProvider o-- BaseProviderConfig : config
    BaseLLMProvider o-- BaseLLMProviderConfig : config
