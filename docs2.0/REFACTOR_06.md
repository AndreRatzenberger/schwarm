# Schwarm Framework Tool System Architecture

## Overview

This document focuses on the tool system architecture of the Schwarm framework, proposing enhancements while maintaining its flexible function execution capabilities.

## 1. Tool Core Architecture

### 1.1 Tool Registry

```python
# domain/tool/registry.py
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar

T = TypeVar('T')

@dataclass
class ToolMetadata:
    """Metadata for registered tools."""
    name: str
    description: str
    parameters: dict[str, Any]
    required_params: list[str]
    return_type: type
    tags: list[str] = field(default_factory=list)

class ToolRegistry:
    """Central registry for tool management."""
    
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._metadata: dict[str, ToolMetadata] = {}
        self._lock = asyncio.Lock()

    async def register(
        self,
        func: Callable[..., T],
        metadata: ToolMetadata | None = None
    ) -> None:
        """Register a tool with metadata."""
        async with self._lock:
            name = func.__name__
            if not metadata:
                metadata = self._extract_metadata(func)
            
            await self._validate_tool(func, metadata)
            self._tools[name] = func
            self._metadata[name] = metadata

    async def get_tool(
        self,
        name: str
    ) -> tuple[Callable, ToolMetadata]:
        """Get a tool and its metadata."""
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool {name} not found")
        return self._tools[name], self._metadata[name]

    def list_tools(
        self,
        tag: str | None = None
    ) -> list[ToolMetadata]:
        """List available tools, optionally filtered by tag."""
        if tag:
            return [
                meta for meta in self._metadata.values()
                if tag in meta.tags
            ]
        return list(self._metadata.values())
```

### 1.2 Tool Handler

```python
# domain/tool/handler.py
@dataclass
class ToolContext:
    """Context for tool execution."""
    agent_id: str
    tool_name: str
    parameters: dict[str, Any]
    context_variables: dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ToolResult:
    """Result from tool execution."""
    value: Any
    metadata: dict[str, Any]
    agent_handoff: str | None = None
    context_updates: dict[str, Any] = field(default_factory=dict)

class ToolHandler:
    """Enhanced tool execution handler."""
    
    def __init__(
        self,
        registry: ToolRegistry,
        validator: ToolValidator,
        metrics: ToolMetrics
    ):
        self.registry = registry
        self.validator = validator
        self.metrics = metrics
        self._error_handler = ToolErrorHandler()

    async def execute_tool(
        self,
        tool_call: ToolCall,
        context: ToolContext
    ) -> ToolResult:
        """Execute a tool with full context and monitoring."""
        try:
            await self.validator.validate_call(tool_call, context)
            
            async with self.metrics.measure_execution_time(context):
                tool, metadata = await self.registry.get_tool(tool_call.name)
                result = await self._execute_with_context(
                    tool,
                    tool_call.parameters,
                    context
                )
                
                processed_result = await self._process_result(result, context)
                await self.metrics.record_success(context)
                return processed_result
                
        except Exception as e:
            await self._error_handler.handle_error(e, context)
            raise

    async def execute_multiple(
        self,
        tool_calls: list[ToolCall],
        base_context: ToolContext
    ) -> list[ToolResult]:
        """Execute multiple tools with shared base context."""
        results = []
        for call in tool_calls:
            context = replace(
                base_context,
                tool_name=call.name,
                parameters=call.parameters
            )
            result = await self.execute_tool(call, context)
            results.append(result)
        return results
```

### 1.3 Tool Validation

```python
# domain/tool/validation.py
class ToolValidator:
    """Validates tool calls before execution."""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    async def validate_call(
        self,
        tool_call: ToolCall,
        context: ToolContext
    ) -> None:
        """Validate a tool call before execution."""
        tool, metadata = await self.registry.get_tool(tool_call.name)
        
        # Validate required parameters
        missing_params = [
            param for param in metadata.required_params
            if param not in tool_call.parameters
        ]
        if missing_params:
            raise ToolValidationError(
                f"Missing required parameters: {missing_params}"
            )

        # Validate parameter types
        for name, value in tool_call.parameters.items():
            expected_type = metadata.parameters[name]
            if not isinstance(value, expected_type):
                raise ToolValidationError(
                    f"Parameter {name} has invalid type. "
                    f"Expected {expected_type}, got {type(value)}"
                )
```

## 2. Tool Monitoring

### 2.1 Metrics Collection

```python
# domain/tool/metrics.py
class ToolMetrics:
    """Collects metrics for tool execution."""
    
    def __init__(self):
        self.meter = metrics.get_meter(__name__)
        self._setup_metrics()

    def _setup_metrics(self):
        self.executions = self.meter.create_counter(
            "tool_executions",
            description="Number of tool executions"
        )
        self.execution_time = self.meter.create_histogram(
            "tool_execution_time",
            description="Tool execution time"
        )
        self.errors = self.meter.create_counter(
            "tool_errors",
            description="Number of tool errors"
        )

    @contextlib.asynccontextmanager
    async def measure_execution_time(self, context: ToolContext):
        """Measure tool execution time."""
        start_time = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start_time
            self.execution_time.record(
                duration,
                {
                    "tool": context.tool_name,
                    "agent": context.agent_id
                }
            )

    async def record_success(self, context: ToolContext):
        """Record successful tool execution."""
        self.executions.add(
            1,
            {
                "tool": context.tool_name,
                "agent": context.agent_id,
                "status": "success"
            }
        )
```

### 2.2 Error Handling

```python
# domain/tool/error.py
class ToolErrorHandler:
    """Handles tool execution errors."""
    
    def __init__(self):
        self._metrics = ToolMetrics()
        self._recovery_strategies = self._setup_strategies()

    async def handle_error(
        self,
        error: Exception,
        context: ToolContext
    ) -> None:
        """Handle tool execution errors."""
        self._metrics.errors.add(
            1,
            {
                "tool": context.tool_name,
                "agent": context.agent_id,
                "error_type": type(error).__name__
            }
        )
        
        logger.error(
            f"Tool execution error: {error}",
            extra={
                "context": asdict(context),
                "error": str(error)
            }
        )
        
        strategy = self._get_recovery_strategy(error)
        if strategy:
            await strategy.execute(context)
```

## 3. Tool Definition

### 3.1 Tool Decorator

```python
# domain/tool/decorator.py
def tool(
    description: str,
    tags: list[str] | None = None
) -> Callable:
    """Decorator for registering tools."""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            context = kwargs.get('context')
            if context:
                # Add execution context
                kwargs['context'] = await enrich_context(context)
            
            # Execute tool with tracing
            with tracer.start_as_current_span(
                f"tool.{func.__name__}",
                attributes={
                    "tool.name": func.__name__,
                    "tool.tags": tags
                }
            ) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("tool.status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("tool.status", "error")
                    span.record_exception(e)
                    raise
        
        # Store metadata for registration
        wrapper.__tool_metadata__ = ToolMetadata(
            name=func.__name__,
            description=description,
            parameters=get_type_hints(func),
            required_params=get_required_params(func),
            return_type=get_return_type(func),
            tags=tags or []
        )
        return wrapper
    
    return decorator
```

## 4. Implementation Guidelines

### 4.1 Tool Design

1. **Function Signatures**
   - Use type hints
   - Document parameters
   - Define clear return types

2. **Error Handling**
   - Use specific exceptions
   - Implement recovery strategies
   - Provide clear error messages

### 4.2 Performance

1. **Execution**
   - Use async where appropriate
   - Implement timeouts
   - Handle long-running tools

2. **Resource Management**
   - Clean up resources
   - Handle concurrent execution
   - Implement rate limiting

### 4.3 Security

1. **Input Validation**
   - Validate all parameters
   - Sanitize inputs
   - Check permissions

2. **Output Handling**
   - Sanitize results
   - Handle sensitive data
   - Implement access control

## 5. Migration Strategy

### Phase 1: Core Infrastructure
1. Implement tool registry
2. Add validation system
3. Enhance error handling

### Phase 2: Monitoring
1. Add metrics collection
2. Implement tracing
3. Add performance monitoring

### Phase 3: Enhancement
1. Add async support
2. Implement tool decorator
3. Add security features

## Conclusion

This enhanced tool system architecture provides a robust foundation for managing tool execution in the Schwarm framework. The combination of strong validation, comprehensive monitoring, and flexible execution ensures reliable and maintainable tool operations while maintaining the framework's core capabilities.
