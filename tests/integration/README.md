# WebSocket Test Server

This directory contains a test server that simulates the Schwarm backend's WebSocket functionality using the same managers as the main project.

## Setup

Install the required dependencies:
```bash
uv pip install -r requirements.txt
```

## Running the Test Server

Start the test server:
```bash
uv run test_websocket_messages.py
```

This will launch a FastAPI server on port 8123 that uses the following managers from the main project:

1. `WebsocketManager` for the `/ws` endpoint
   - Handles regular messages using the same singleton pattern
   - Maintains active connections and handles cleanup
   - Sends properly formatted WebsocketMessages

2. `StreamManager` for the `/ws/stream` endpoint
   - Handles streaming content using the same singleton pattern
   - Supports both default and tool message types
   - Manages streaming state and connection lifecycle

## REST Endpoints

The server provides REST endpoints to trigger sending messages through the managers:

1. `POST /trigger/messages`
   - Uses WebsocketManager to send various message types
   - Example: `curl -X POST http://localhost:8123/trigger/messages`
   - Sends: CHAT_REQUESTED, IS_WAITING, EVENT, PAUSE_STATUS

2. `POST /trigger/stream`
   - Uses StreamManager to send streaming content
   - Example: `curl -X POST http://localhost:8123/trigger/stream`
   - Sends chunks with proper delays and close signal

3. `POST /trigger/all`
   - Triggers both WebsocketManager and StreamManager messages
   - Example: `curl -X POST http://localhost:8123/trigger/all`

## Testing with Nektar Frontend

1. Start the test server using `uv run test_websocket_messages.py`
2. Launch the Nektar frontend application
3. Navigate to the "WebSocket Messages" tab
4. Use the REST endpoints to trigger messages:
   ```bash
   # Send all types of messages
   curl -X POST http://localhost:8123/trigger/all
   ```

## Expected Behavior

When triggering messages:
- WebsocketManager messages will be sent with 0.5-second delays
- StreamManager chunks will be sent with 0.2-second delays
- All messages will appear in the Nektar frontend's WebSocket Messages tab
- The managers maintain active connections and handle disconnections properly

## Troubleshooting

If messages are not appearing:
1. Verify the test server is running (should see console output)
2. Check that the Nektar frontend is configured to connect to localhost:8123
3. Look for any connection errors in the browser's developer console
4. Test the REST endpoints using curl to verify server functionality
5. Ensure no other service is using port 8123

## Implementation Details

The test server uses the exact same manager implementations as the main project:
- `WebsocketManager` from `schwarm.manager.websocket_manager`
- `StreamManager` from `schwarm.manager.stream_manager`
- `WebsocketMessage` from `schwarm.manager.websocket_messages`

This ensures that the test environment accurately reflects the behavior of the production system.
