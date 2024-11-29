classDiagram
    %% Core Capabilities
    class MemoryCapabilities {
        +add_to_memory(text)
        +search_memory(query)
        +enhance_instructions()
        +save_completion()
    }

    class EventHandling {
        +handle_event(event)
        +handle_start()
        +handle_message_completion()
        +handle_tool_execution()
        +handle_post_tool_execution()
    }

    class LLMOperations {
        +test_connection()
        +initialize()
        +prepare_messages()
        +create_completion_response()
        +complete(messages)
    }

    class BudgetTracking {
        +handle_start()
        +handle_post_message_completion()
        +handle_handoff()
        +show_budget()
    }

    class ToolManagement {
        +handle_function_result()
        +function_to_json()
    }

    class StreamProcessing {
        +process_chunk()
        +create_empty_message()
        +finalize_message()
        +merge_chunk()
    }

    %% Provider Management
    class ProviderOperations {
        +register_provider()
        +create_provider()
        +get_providers_by_class()
        +get_provider_by_id()
        +get_event_providers()
        +trigger_event()
    }

    %% File Operations
    class FileOperations {
        +load_dictionary_list()
        +save_text_to_file()
        +write_to_log()
        +ensure_log_directory()
    }

    %% Relationships
    ZepProvider --|> MemoryCapabilities
    DebugProvider --|> EventHandling
    LiteLLMProvider --|> LLMOperations
    BudgetProvider --|> BudgetTracking
    ProviderManager --|> ProviderOperations

    %% Utility Relationships
    ToolHandler --|> ToolManagement
    StreamHandler --|> StreamProcessing
    FileHandler --|> FileOperations
