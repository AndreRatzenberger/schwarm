export interface Agent {
    name: string;
    model: string;
    description?: string;
    instructions?: string;
}

export interface Message {
    role: 'user' | 'assistant' | 'tool';
    content: string;
    sender?: string;
    tool_calls?: Array<{
        function: {
            name: string;
            arguments: Record<string, unknown>;
        };
    }>;
    additional_info?: Record<string, unknown>;
}

export interface BudgetData {
    max_spent: number;
    max_tokens: number;
    current_spent: number;
    current_tokens: number;
}

export interface Event {
    timestamp: string;
    type: EventType;
    data: EventPayload;
}

export type EventType =
    | 'agent_start'
    | 'message_completion'
    | 'tool_execution'
    | 'tool_result'
    | 'handoff'
    | 'budget_update'
    | 'reset';

export type EventPayload = {
    agent_start: {
        agent: Agent;
    };
    message_completion: {
        agent: string;
        message: Message;
    };
    tool_execution: Array<{
        name: string;
        arguments: Record<string, unknown>;
    }>;
    tool_result: Array<Message>;
    handoff: {
        from: string;
        to: string;
        message: Message;
    };
    budget_update: BudgetData;
    reset: Record<string, never>;
}[EventType];
