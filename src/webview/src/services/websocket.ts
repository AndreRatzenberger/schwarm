import { useDebugStore } from '../store/debugStore';
import { Event, EventType, EventPayload, Agent, Message, BudgetData } from '../types/events';

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
        };

        this.socket.onclose = () => {
            console.log('WebSocket disconnected');
            this.handleReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
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
        if (data.type === 'history') {
            data.data.forEach((event) => this.processEvent(event));
            return;
        }

        // Handle individual events
        this.processEvent({
            type: data.type,
            data: data.data,
            timestamp: data.timestamp
        });
    }

    private processEvent(event: Event): void {
        const store = useDebugStore.getState();
        store.addEvent(event);

        switch (event.type) {
            case 'agent_start': {
                const agentData = event.data as { agent: Agent };
                store.addAgent(agentData.agent);
                break;
            }

            case 'message_completion': {
                const messageData = event.data as { agent: string; message: Message };
                store.addMessage(messageData.message);
                break;
            }

            case 'handoff': {
                const handoffData = event.data as { from: string; to: string; message: Message };
                store.addConnection(handoffData.from, handoffData.to);
                store.setActiveAgent(handoffData.to);
                break;
            }

            case 'budget_update': {
                const budgetData = event.data as BudgetData;
                store.updateBudget(budgetData);
                break;
            }

            case 'reset':
                store.clearEvents();
                break;
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
        }
    }
}

// Create a singleton instance
export const wsService = new WebSocketService();
