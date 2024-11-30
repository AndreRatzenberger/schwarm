# Schwarm Framework Agent Architecture

## Overview

This document focuses on the agent architecture of the Schwarm framework, proposing enhancements while maintaining its flexible agent capabilities.

## 1. Agent Core Architecture

### 1.1 Base Agent

```python
# domain/agent/base.py
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

@dataclass(frozen=True)
class AgentConfig:
    """Configuration for agents."""
    name: str
    description: str = ""
    model: str = "gpt-4"
    tool_choice: Literal["none", "auto", "required"] = "required"
    parallel_tool_calls: bool = False
    provider_configs: list[ProviderConfig] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

class AgentProtocol(Protocol):
    """Protocol defining agent behavior."""
    
    @property
    def config(self) -> AgentConfig:
        """Agent configuration."""
        ...

    @property
    def state(self) -> AgentState:
        """Current agent state."""
        ...

    async def process(
        self,
        messages: list[Message],
        context: Context
    ) -> AgentResponse:
        """Process messages and return response."""
        ...

    async def get_instructions(
        self,
        context: Context
    ) -> str:
        """Get agent instructions."""
        ...

class BaseAgent:
    """Base implementation of agent behavior."""
    
    def __init__(
        self,
        config: AgentConfig,
        tool_registry: ToolRegistry,
        provider_registry: ProviderRegistry
    ):
        self.config = config
        self._tool_registry = tool_registry
        self._provider_registry = provider_registry
        self._state = AgentState()
        self._metrics = AgentMetrics()

    async def process(
        self,
        messages: list[Message],
        context: Context
    ) -> AgentResponse:
        """Process messages with monitoring."""
        try:
            async with self._metrics.measure_processing_time(context):
                instructions = await self.get_instructions(context)
                response = await self._process_with_instructions(
                    messages,
                    instructions,
                    context
                )
                await self._metrics.record_success(context)
                return response
        except Exception as e:
            await self._handle_error(e, context)
            raise
```

### 1.2 Agent State Management

```python
# domain/agent/state.py
@dataclass
class AgentState:
    """Maintains agent state."""
    
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    turn_count: int = 0
    last_instruction: str | None = None
    last_response: AgentResponse | None = None
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    metadata: dict[str, Any] = field(default_factory=dict)

    def update(self, **kwargs) -> None:
        """Update state attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

@dataclass
class TokenUsage:
    """Tracks token usage."""
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0

    def add_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float
    ) -> None:
        """Add token usage."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_cost += cost
```

## 2. Agent Patterns

### 2.1 Fan-Out Agent

```python
# domain/agent/patterns/fan_out.py
class FanOutAgent(BaseAgent):
    """Agent that distributes work to multiple agents."""
    
    def __init__(
        self,
        config: AgentConfig,
        target_agents: list[BaseAgent],
        aggregator: ResponseAggregator
    ):
        super().__init__(config)
        self.target_agents = target_agents
        self.aggregator = aggregator

    async def process(
        self,
        messages: list[Message],
        context: Context
    ) -> AgentResponse:
        """Process messages by distributing to target agents."""
        tasks = [
            agent.process(messages, context)
            for agent in self.target_agents
        ]
        
        responses = await asyncio.gather(*tasks)
        return await self.aggregator.aggregate(responses)
```

### 2.2 Handoff Agent

```python
# domain/agent/patterns/handoff.py
class HandoffAgent(BaseAgent):
    """Agent that can hand off to other agents."""
    
    def __init__(
        self,
        config: AgentConfig,
        agent_registry: AgentRegistry
    ):
        super().__init__(config)
        self.agent_registry = agent_registry

    async def process(
        self,
        messages: list[Message],
        context: Context
    ) -> AgentResponse:
        """Process messages with potential handoff."""
        response = await super().process(messages, context)
        
        if response.handoff:
            next_agent = await self.agent_registry.get_agent(
                response.handoff
            )
            return await next_agent.process(messages, context)
        
        return response
```

### 2.3 User Agent

```python
# domain/agent/patterns/user.py
class UserAgent(BaseAgent):
    """Agent representing user interactions."""
    
    async def process(
        self,
        messages: list[Message],
        context: Context
    ) -> AgentResponse:
        """Process user messages."""
        # User agents typically don't process messages
        # They just forward them to the next agent
        return AgentResponse(
            messages=messages,
            metadata={"source": "user"}
        )

    async def get_instructions(
        self,
        context: Context
    ) -> str:
        """User agents don't need instructions."""
        return ""
```

## 3. Agent Factory

```python
# application/agent/factory.py
class AgentFactory:
    """Factory for creating agents."""
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        provider_registry: ProviderRegistry,
        agent_registry: AgentRegistry
    ):
        self.tool_registry = tool_registry
        self.provider_registry = provider_registry
        self.agent_registry = agent_registry

    async def create_agent(
        self,
        config: AgentConfig
    ) -> BaseAgent:
        """Create an agent instance."""
        agent_class = self._get_agent_class(config)
        
        agent = agent_class(
            config=config,
            tool_registry=self.tool_registry,
            provider_registry=self.provider_registry
        )
        
        await self.agent_registry.register(agent)
        return agent

    def _get_agent_class(
        self,
        config: AgentConfig
    ) -> type[BaseAgent]:
        """Get appropriate agent class based on config."""
        # Map config patterns to agent classes
        patterns = {
            "fan_out": FanOutAgent,
            "handoff": HandoffAgent,
            "user": UserAgent
        }
        
        pattern = config.metadata.get("pattern", "base")
        return patterns.get(pattern, BaseAgent)
```

## 4. Implementation Guidelines

### 4.1 Agent Design

1. **State Management**
   - Keep state immutable
   - Use clear state transitions
   - Track token usage

2. **Error Handling**
   - Implement fallbacks
   - Handle timeouts
   - Manage rate limits

### 4.2 Performance

1. **Resource Management**
   - Monitor token usage
   - Implement timeouts
   - Handle concurrent processing

2. **Optimization**
   - Cache instructions
   - Reuse providers
   - Batch operations

### 4.3 Security

1. **Access Control**
   - Validate permissions
   - Sanitize inputs
   - Control tool access

## 5. Migration Strategy

### Phase 1: Core Architecture
1. Implement base agent
2. Add state management
3. Enhance error handling

### Phase 2: Patterns
1. Implement fan-out pattern
2. Add handoff capability
3. Create user agent

### Phase 3: Factory
1. Implement agent factory
2. Add pattern support
3. Enhance creation process

## Conclusion

This enhanced agent architecture provides a robust foundation for managing different types of agents in the Schwarm framework. The combination of clear patterns, strong state management, and flexible factory creation ensures reliable and maintainable agent operations while maintaining the framework's core flexibility.
