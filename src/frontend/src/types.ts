export interface Log {
  id: string;
  timestamp: string;
  parent_id: string;
  run_id: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'LOG' | 'START_TURN' | 'INSTRUCT' | 'MESSAGE_COMPLETION' | 'POST_MESSAGE_COMPLETION' | 'TOOL_EXECUTION' | 'POST_TOOL_EXECUTION' | 'HANDOFF';
  agent: string;
  message: string;
  attributes: Record<string, unknown>;
}

export interface Span {
  id: string;
  parent_span_id: string;
  run_id: string;
  name: string;
  start_time: string;
  status_code: string;
  attributes: Record<string, unknown>;
  [key: string]: unknown;
}

export interface WebSocketMessage {
  message_type: 'CHAT' | 'BREAK' | 'ERROR' | 'EVENT' | 'STREAM';
  message: string;
}


export interface StreamViewerProps {
  url?: string;
  onMessageReceived?: (message: string) => void;
  autoStart?: boolean;
}


export interface StreamMessage {
  type: 'content' | 'error' | 'end' | 'metadata';
  content: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
}

export interface StreamReaderHook {
  messages: StreamMessage[];
  error: string | null;
  isLoading: boolean;
  startStream: () => Promise<void>;
  stopStream: () => void;
  clearMessages: () => void;
}
