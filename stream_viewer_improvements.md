# StreamViewer Component Improvements

The current StreamViewer.tsx implementation correctly handles our stream messages, but here are some suggested improvements:

## 1. Enhanced Error Handling

```typescript
ws.onmessage = (event) => {
  try {
    const message: StreamMessage = JSON.parse(event.data);
    if (!message || typeof message !== 'object') {
      throw new Error('Invalid message format');
    }
    
    if (!('type' in message) || !['default', 'tool', 'close'].includes(message.type)) {
      throw new Error('Invalid message type');
    }
    
    if (message.type === 'close') {
      ws.close();
      return;
    }
    
    if (message.content) {
      setText(prev => prev + message.content);
    }
  } catch (e) {
    console.error('Error processing message:', e);
    setError(`Message processing error: ${e instanceof Error ? e.message : 'Unknown error'}`);
  }
};
```

## 2. Improved WebSocket Cleanup

```typescript
useEffect(() => {
  let timeoutId: NodeJS.Timeout;
  
  if (!isPaused) {
    connect();
  } else {
    disconnect();
  }
  
  return () => {
    clearTimeout(timeoutId);
    disconnect();
    setText(''); // Clear text on unmount
    setError(null);
  };
}, [url, isPaused]);
```

## 3. Message Buffering for Performance

```typescript
const useBufferedWebSocket = (url: string) => {
  const [text, setText] = useState('');
  const bufferRef = useRef<string>('');
  const bufferTimeoutRef = useRef<NodeJS.Timeout>();

  const flushBuffer = useCallback(() => {
    if (bufferRef.current) {
      setText(prev => prev + bufferRef.current);
      bufferRef.current = '';
    }
  }, []);

  const onMessage = useCallback((event: MessageEvent) => {
    try {
      const message: StreamMessage = JSON.parse(event.data);
      
      if (message.type === 'close') {
        flushBuffer();
        ws.current?.close();
        return;
      }
      
      if (message.content) {
        bufferRef.current += message.content;
        
        // Flush buffer after 50ms of no new messages
        clearTimeout(bufferTimeoutRef.current);
        bufferTimeoutRef.current = setTimeout(flushBuffer, 50);
      }
    } catch (e) {
      console.error('Error processing message:', e);
    }
  }, [flushBuffer]);

  // ... rest of the implementation
};
```

## 4. Connection Status Indicators

```typescript
interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  lastError: string | null;
  reconnectAttempt: number;
}

const [connectionState, setConnectionState] = useState<ConnectionState>({
  isConnected: false,
  isConnecting: false,
  lastError: null,
  reconnectAttempt: 0,
});

// Update UI to show more detailed connection status
const getConnectionStatus = () => {
  if (connectionState.isConnected) return 'Connected';
  if (connectionState.isConnecting) return `Connecting (Attempt ${connectionState.reconnectAttempt})`;
  if (connectionState.lastError) return `Error: ${connectionState.lastError}`;
  return 'Disconnected';
};
```

## 5. Rate Limiting

```typescript
const useRateLimitedWebSocket = (url: string) => {
  const messageQueueRef = useRef<string[]>([]);
  const processingRef = useRef(false);

  const processQueue = useCallback(async () => {
    if (processingRef.current || messageQueueRef.current.length === 0) return;
    
    processingRef.current = true;
    while (messageQueueRef.current.length > 0) {
      const content = messageQueueRef.current.shift();
      if (content) {
        setText(prev => prev + content);
        await new Promise(resolve => setTimeout(resolve, 16)); // ~60fps
      }
    }
    processingRef.current = false;
  }, []);

  // Use in onmessage handler
  if (message.content) {
    messageQueueRef.current.push(message.content);
    processQueue();
  }
};
```

## Integration with Stream Manager

The current implementation correctly handles all message types from our StreamManager:

1. Default messages on `/ws`
2. Tool messages on `/ws/tool`
3. Close messages for cleanup

The message format matches our StreamManager's output:
```typescript
{
  type: 'default' | 'tool' | 'close';
  content: string | null;
}
```

## Recommendations

1. Implement the enhanced error handling for more robust error reporting
2. Add the connection status indicators for better UX
3. Consider adding message buffering if dealing with high-frequency updates
4. Add rate limiting if performance becomes an issue with large streams

These improvements maintain compatibility with our StreamManager while adding more robust handling and better performance characteristics.
