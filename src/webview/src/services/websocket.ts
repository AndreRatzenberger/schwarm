import { useDebugStore } from '../store/debugStore';
import { Event, EventType, EventPayload, BudgetData, Agent, Message } from '../types/events';

interface WebSocketMessage {
    type: 'history';
    data: Event[];
}

interface WebSocketEvent {
    type: EventType;
    data: EventPayload;
    timestamp: string;
}

type WebSocketResponse = WebSocketMessage | WebSocketEvent;

// Type guards
const isAgentStartData = (data: EventPayload): data is { agent: Agent } => {
    return 'agent' in data && typeof data.agent === 'object';
};

const isMessageCompletionData = (data: EventPayload): data is { agent: string; message: Message } => {
    return 'agent' in data && 'message' in data;
};

const isHandoffData = (data: EventPayload): data is { from: string; to: string; message: Message } => {
    return 'from' in data && 'to' in data;
};

const isBudgetData = (data: EventPayload): data is BudgetData => {
    return 'max_spent' in data && 'current_spent' in data;
};

class WebSocketService {
    private socket: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private reconnectDelay = 1000;

    connect(url: string): void {
        try {
            this.socket = new WebSocket(url);
            this.setupEventHandlers();
        } catch (error) {
            console.error('Failed to connect to WebSocket:', error);
            this.handleReconnect();
        }
    }

    private setupEventHandlers(): void {
        if (!this.socket) return;

        this.socket.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
            useDebugStore.getState().setConnected(true);
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            useDebugStore.getState().setConnected(false);
            this.handleReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            useDebugStore.getState().setConnected(false);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data) as WebSocketResponse;
                this.handleMessage(data);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
    }

    private handleMessage(data: WebSocketResponse): void {
        // Handle initial history load
        if ('type' in data && data.type === 'history') {
            data.data.forEach((event) => this.processEvent(event));
            return;
        }

        // Handle individual events
        this.processEvent(data as WebSocketEvent);
    }

    private processEvent(event: Event): void {
        const store = useDebugStore.getState();

        // Add event to history
        store.addEvent(event);

        // Process specific event types
        switch (event.type) {
            case 'agent_start': {
                if (isAgentStartData(event.data)) {
                    store.addAgent(event.data.agent);
                }
                break;
            }

            case 'message_completion': {
                if (isMessageCompletionData(event.data)) {
                    store.addMessage(event.data.message);
                }
                break;
            }

            case 'handoff': {
                if (isHandoffData(event.data)) {
                    store.addConnection(event.data.from, event.data.to);
                    store.setActiveAgent(event.data.to);
                }
                break;
            }

            case 'budget_update': {
                if (isBudgetData(event.data)) {
                    store.updateBudget(event.data);
                }
                break;
            }

            case 'reset': {
                store.clearEvents();
                break;
            }
        }
    }

    private handleReconnect(): void {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting to reconnect in ${delay}ms...`);
        setTimeout(() => {
            if (this.socket?.url) {
                this.connect(this.socket.url);
            }
        }, delay);
    }

    disconnect(): void {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            useDebugStore.getState().setConnected(false);
        }
    }
}

// Create a singleton instance
export const wsService = new WebSocketService();
