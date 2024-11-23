import { useDebugStore } from '../store/debugStore';
import { Event } from '../types/events';

interface WebSocketMessage {
    type: 'history';
    data: Event[];
}

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
                const data = JSON.parse(event.data) as WebSocketMessage | Event;

                // Handle initial history load
                if ('type' in data && data.type === 'history') {
                    data.data.forEach(event => this.processEvent(event));
                    return;
                }

                // Handle individual event
                this.processEvent(data as Event);
            } catch (error) {
                console.error('Failed to parse WebSocket message:', error);
            }
        };
    }

    private processEvent(event: Event): void {
        const store = useDebugStore.getState();

        // Add event to history
        store.addEvent(event);

        // Add agent to map if present
        if (event.payload.current_agent) {
            store.addAgent(event.payload.current_agent);
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
