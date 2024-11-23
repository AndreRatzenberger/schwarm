import { WebSocketServer } from 'ws';
import { createServer } from 'vite';
import { Event, EventType } from './src/types/events';

async function startServer() {
    // Start Vite dev server
    const vite = await createServer({
        server: {
            port: 5173
        }
    });

    await vite.listen();
    console.log('Vite server running on http://localhost:5173');

    // Start WebSocket server
    const wss = new WebSocketServer({ port: 8123 });
    console.log('WebSocket server running on ws://localhost:8123');

    // Store connected clients
    const clients = new Set();

    wss.on('connection', (ws) => {
        console.log('Client connected');
        clients.add(ws);

        ws.on('close', () => {
            console.log('Client disconnected');
            clients.delete(ws);
        });
    });

    // Simulate events every 5 seconds
    setInterval(() => {
        const event: Event<unknown> = {
            type: EventType.TOOL_EXECUTION,
            payload: {
                tool: "test_tool",
                params: { test: "value" }
            },
            agent_id: "test-agent",
            datetime: new Date().toISOString()
        };

        // Broadcast to all connected clients
        clients.forEach(client => {
            try {
                (client as WebSocket).send(JSON.stringify(event));
            } catch (error) {
                console.error('Failed to send message:', error);
            }
        });
    }, 5000);
}

startServer().catch(console.error);
