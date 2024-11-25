classDiagram
    class EventType {
        <<Enumeration>>
        START
        HANDOFF
        MESSAGE_COMPLETION
        POST_MESSAGE_COMPLETION
        TOOL_EXECUTION
        POST_TOOL_EXECUTION
        INSTRUCT
        POST_INSTRUCT
    }

    class Event {
        +EventType type
        +T context
        +str agent_id
        +str datetime
    }

    class BaseEventHandleProvider {
        <<Abstract>>
        +handle_event(Event)*
    }

    class ProviderManager {
        +trigger_event()
        +get_event_providers()
    }

    class ProviderContext {
        +Agent current_agent
    }

    Event --> EventType
    Event o-- ProviderContext : context
    ProviderManager --> Event : triggers
    BaseEventHandleProvider --> Event : handles
    ProviderManager --> BaseEventHandleProvider : manages
