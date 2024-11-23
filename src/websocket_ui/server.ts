import { WebSocket, WebSocketServer } from 'ws';
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
    const clients = new Set<WebSocket>();

    wss.on('connection', (ws: WebSocket) => {
        console.log('Client connected');
        clients.add(ws);

        // Handle incoming messages
        ws.on('message', (data) => {
            try {
                // Parse and validate the message
                const message = JSON.parse(data.toString());
                console.log('Received message:', message);

                // Broadcast the message to all connected clients
                clients.forEach((client: WebSocket) => {
                    if (client.readyState === WebSocket.OPEN) {
                        client.send(data.toString());
                    }
                });
            } catch (error) {
                console.error('Error handling message:', error);
            }
        });

        ws.on('close', () => {
            console.log('Client disconnected');
            clients.delete(ws);
        });

        ws.on('error', (error) => {
            console.error('WebSocket error:', error);
        });
    });

    // Handle server errors
    wss.on('error', (error) => {
        console.error('WebSocket server error:', error);
    });
}

startServer().catch(console.error);
