# Schwarm Framework Streaming Architecture

## Overview

This document focuses on the streaming and message handling architecture of the Schwarm framework, proposing enhancements while maintaining its efficient streaming capabilities.

## 1. Stream Core Architecture

### 1.1 Stream Handler

```python
# domain/stream/handler.py
from dataclasses import dataclass, field
from typing import AsyncGenerator, Any

@dataclass
class StreamConfig:
    """Configuration for stream handling."""
    chunk_size: int = 1024
    timeout: float = 30.0
    retry_attempts: int = 3
    buffer_size: int = 8192

@dataclass
class StreamContext:
    """Context for stream processing."""
    agent_id: str
    message_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    chunks_processed: int = 0
    total_tokens: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

class StreamHandler:
    """Enhanced stream handling with monitoring and error recovery."""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self._buffer = AsyncStreamBuffer(config.buffer_size)
        self._metrics = StreamMetrics()
        self._error_handler = StreamErrorHandler()

    async def process_stream(
        self,
        stream: AsyncGenerator[Any, None],
        context: StreamContext
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process a stream with enhanced error handling and monitoring."""
        try:
            async with self._metrics.measure_processing_time(context):
                async for chunk in self._process_chunks(stream, context):
                    yield chunk
        except Exception as e:
            await self._error_handler.handle_error(e, context)
            raise

    async def _process_chunks(
        self,
        stream: AsyncGenerator[Any, None],
        context: StreamContext
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Process individual chunks with buffering."""
        yield {"delimiter": "start", "context": context.message_id}

        async for chunk in stream:
            processed_chunk = await self._process_single_chunk(chunk, context)
            await self._buffer.add(processed_chunk)
            
            while not self._buffer.empty():
                yield await self._buffer.get()

        yield {"delimiter": "end", "context": context.message_id}

    async def _process_single_chunk(
        self,
        chunk: Any,
        context: StreamContext
    ) -> dict[str, Any]:
        """Process a single chunk with validation."""
        try:
            delta = self._parse_chunk(chunk)
            context.chunks_processed += 1
            context.total_tokens += self._count_tokens(delta)
            
            return {
                "content": delta,
                "metadata": {
                    "agent_id": context.agent_id,
                    "message_id": context.message_id,
                    "chunk_number": context.chunks_processed,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            await self._error_handler.handle_chunk_error(e, chunk, context)
            raise
```

### 1.2 Stream Buffer

```python
# domain/stream/buffer.py
class AsyncStreamBuffer:
    """Async buffer for stream processing."""
    
    def __init__(self, max_size: int):
        self._buffer = asyncio.Queue(maxsize=max_size)
        self._lock = asyncio.Lock()

    async def add(self, item: Any) -> None:
        """Add item to buffer with backpressure."""
        async with self._lock:
            while self._buffer.full():
                await asyncio.sleep(0.1)
            await self._buffer.put(item)

    async def get(self) -> Any:
        """Get item from buffer."""
        return await self._buffer.get()

    @property
    def empty(self) -> bool:
        """Check if buffer is empty."""
        return self._buffer.empty()

    async def clear(self) -> None:
        """Clear buffer contents."""
        async with self._lock:
            while not self._buffer.empty():
                await self._buffer.get()
```

### 1.3 Message Accumulator

```python
# domain/stream/accumulator.py
class MessageAccumulator:
    """Accumulates streaming messages into final form."""
    
    def __init__(self):
        self._messages: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_message(
        self,
        message_id: str,
        agent_id: str
    ) -> None:
        """Initialize a new message."""
        async with self._lock:
            self._messages[message_id] = {
                "content": "",
                "agent_id": agent_id,
                "role": "assistant",
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": ""
                    }
                ),
                "metadata": {
                    "created_at": datetime.utcnow().isoformat(),
                    "chunks_received": 0,
                    "total_tokens": 0
                }
            }

    async def add_chunk(
        self,
        message_id: str,
        chunk: dict[str, Any]
    ) -> None:
        """Add a chunk to an existing message."""
        async with self._lock:
            if message_id not in self._messages:
                raise ValueError(f"Message {message_id} not found")
            
            message = self._messages[message_id]
            await self._merge_chunk(message, chunk)
            message["metadata"]["chunks_received"] += 1

    async def finalize_message(
        self,
        message_id: str
    ) -> dict[str, Any]:
        """Finalize a message for use."""
        async with self._lock:
            if message_id not in self._messages:
                raise ValueError(f"Message {message_id} not found")
            
            message = self._messages[message_id]
            message["tool_calls"] = list(message["tool_calls"].values()) or None
            message["metadata"]["finalized_at"] = datetime.utcnow().isoformat()
            
            return message
```

## 2. Stream Monitoring

### 2.1 Metrics Collection

```python
# domain/stream/metrics.py
class StreamMetrics:
    """Collects metrics for stream processing."""
    
    def __init__(self):
        self.meter = metrics.get_meter(__name__)
        self._setup_metrics()

    def _setup_metrics(self):
        self.chunks_processed = self.meter.create_counter(
            "stream_chunks_processed",
            description="Number of chunks processed"
        )
        self.processing_time = self.meter.create_histogram(
            "stream_processing_time",
            description="Stream processing time"
        )
        self.error_count = self.meter.create_counter(
            "stream_errors",
            description="Number of stream processing errors"
        )

    @contextlib.asynccontextmanager
    async def measure_processing_time(self, context: StreamContext):
        """Measure stream processing time."""
        start_time = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start_time
            self.processing_time.record(
                duration,
                {"agent_id": context.agent_id}
            )
```

### 2.2 Error Handling

```python
# domain/stream/error.py
class StreamErrorHandler:
    """Handles streaming errors with recovery strategies."""
    
    def __init__(self):
        self._metrics = StreamMetrics()
        self._recovery_strategies = self._setup_strategies()

    async def handle_error(
        self,
        error: Exception,
        context: StreamContext
    ) -> None:
        """Handle stream processing errors."""
        self._metrics.error_count.add(1, {
            "error_type": type(error).__name__,
            "agent_id": context.agent_id
        })
        
        strategy = self._get_recovery_strategy(error)
        if strategy:
            await strategy.execute(context)

    async def handle_chunk_error(
        self,
        error: Exception,
        chunk: Any,
        context: StreamContext
    ) -> None:
        """Handle chunk processing errors."""
        logger.error(
            f"Error processing chunk: {error}",
            extra={
                "chunk": chunk,
                "context": asdict(context)
            }
        )
        await self.handle_error(error, context)
```

## 3. Implementation Guidelines

### 3.1 Stream Processing

1. **Chunk Management**
   - Implement proper buffering
   - Handle backpressure
   - Process chunks asynchronously

2. **Error Handling**
   - Implement retry mechanisms
   - Handle partial failures
   - Maintain message integrity

### 3.2 Performance

1. **Memory Management**
   - Use efficient buffers
   - Implement cleanup
   - Handle large messages

2. **Monitoring**
   - Track processing time
   - Monitor error rates
   - Collect metrics

## 4. Migration Strategy

### Phase 1: Core Streaming
1. Implement new stream handler
2. Add buffer management
3. Enhance error handling

### Phase 2: Message Processing
1. Implement accumulator
2. Add validation
3. Enhance merging

### Phase 3: Monitoring
1. Add metrics collection
2. Implement error tracking
3. Add performance monitoring

## Conclusion

This enhanced streaming architecture provides a robust foundation for handling streaming responses in the Schwarm framework. The async-first approach, combined with proper buffering and monitoring, ensures reliable and efficient stream processing while maintaining the framework's core capabilities.
