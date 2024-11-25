classDiagram
    class Schwarm {
        -list _agents
        -ProviderManager _manager
        -ProviderContext _provider_context
        +register_agent()
        +quickstart()
        +run()
        -_complete_agent_request()
    }

    class Response {
        +list messages
        +Agent agent
        +dict context_variables
    }

    class ToolHandler {
        +handle_tool_calls()
    }

    class Message {
        +str role
        +str content
        +str sender
        +list tool_calls
    }

    class Agent {
        +str name
        +str model
        +str instructions
        +list functions
        +str tool_choice
        +bool parallel_tool_calls
    }

    class ProviderContext {
        +list message_history
        +Message current_message
        +Agent current_agent
        +dict context_variables
        +list available_agents
        +list available_tools
        +dict available_providers
    }

    Schwarm "1" --o "*" Agent : manages
    Schwarm "1" --o "1" ProviderManager : uses
    Schwarm --> ToolHandler : uses
    Schwarm --> Response : produces
    Response o-- Agent
    Response o-- Message
    Schwarm --> ProviderContext : maintains
    ProviderContext o-- Agent
    ProviderContext o-- Message
