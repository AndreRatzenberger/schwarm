classDiagram
    class ProviderManager {
        -dict _providers
        -dict _config_to_provider_map
        +register_provider()
        +create_provider_and_register()
        +get_providers_by_class()
        +get_provider_to_agent_name_by_class()
        +get_first_llm_provider()
        +trigger_event()
    }

    class Agent {
        +str name
        +str model
        +str description
        +str instructions
        +list functions
        +str tool_choice
        +bool parallel_tool_calls
        -ProviderManager _provider_manager
        +get_typed_provider()
        +quickstart()
    }

    class BaseEventHandleProvider {
        <<Abstract>>
        +handle_event()*
    }

    class BaseLLMProvider {
        <<Abstract>>
        +test_connection()*
        +async_complete()*
        +complete()*
    }

    class BaseProvider {
        <<Abstract>>
        -str _provider_id
        +ProviderContext context
    }

    ProviderManager "1" --o "*" BaseProvider : manages
    Agent "1" --o "1" ProviderManager : uses
    BaseProvider <|-- BaseLLMProvider
    BaseProvider <|-- BaseEventHandleProvider
