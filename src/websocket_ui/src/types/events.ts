export enum EventType {
    START = "on_start",
    HANDOFF = "on_handoff",
    MESSAGE_COMPLETION = "on_message_completion",
    POST_MESSAGE_COMPLETION = "on_post_message_completion",
    TOOL_EXECUTION = "on_tool_execution",
    POST_TOOL_EXECUTION = "on_post_tool_execution",
    INSTRUCT = "on_instruct",
    POST_INSTRUCT = "on_post_instruct",
    NONE = "on_begin"
}

export interface OnChangePayload<T> {
    name: string;
    old_value: T;
    new_value: T;
}

export interface Event<T> {
    type: EventType;
    payload: T;
    agent_id: string;
    datetime: string;
}
