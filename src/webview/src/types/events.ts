export interface Agent {
    name: string;
    model: string;
    description?: string;
    instructions?: string;
}

export interface Message {
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string | null;
    sender?: string | null;
    name?: string | null;
    tool_calls?: Array<{
        function: {
            name: string;
            arguments: Record<string, unknown>;
        };
    }> | null;
    tool_call_id?: string | null;
    info?: {
        token_counter: number;
        completion_cost: number;
    } | null;
    additional_info: Record<string, unknown>;
}

export interface ProviderContext {
    message_history: Message[];
    current_message: Message | null;
    current_agent: Agent | null;
    available_agents: Agent[];
    available_tools: Record<string, string>;  // TODO: Define tool type if needed
    available_providers: Record<string, string>;  // TODO: Define provider type if needed
    context_variables: Record<string, unknown>;
    instruction_str: string | null;
}

export enum EventType {
    START = "on_start",
    HANDOFF = "on_handoff",
    MESSAGE_COMPLETION = "on_message_completion",
    POST_MESSAGE_COMPLETION = "on_post_message_completion",
    TOOL_EXECUTION = "on_tool_execution",
    POST_TOOL_EXECUTION = "on_post_tool_execution",
    INSTRUCT = "on_instruct"
}

export interface Event {
    type: EventType;
    payload: ProviderContext;
    agent_id: string;
    datetime: string;
}
