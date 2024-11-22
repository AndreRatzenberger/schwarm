# Temporal-based Schwarm Implementation

This is a Temporal-based implementation of the Schwarm agent framework. It provides durability, retries, and observability while maintaining the same user interface as the original Schwarm.

## Key Features

- Agents become Temporal workflows
- Providers become activities
- Messages become signals
- Agent handoffs become child workflows
- Provider state becomes workflow state
- Everything is durable and retryable

## Setup

1. Install Temporal server locally or use Temporal Cloud
2. Install dependencies:
```bash
pip install temporalio
```

## Usage

### Basic Example

```python
import asyncio
from temp_schwarm.models import AgentConfig, ProviderConfig, Message
from temp_schwarm.client import TemporalClientManager, TemporalConfig

# Create provider configurations
llm_config = ProviderConfig(
    provider_type="llm",
    provider_name="gpt-4",
    settings={"model": "gpt-4"}
)

# Create agent configuration
agent = AgentConfig(
    name="assistant",
    provider_configurations=[llm_config],
    instructions="You are a helpful assistant."
)

async def main():
    # Connect to Temporal
    client = await TemporalClientManager().get_client()
    
    # Start workflow
    handle = await client.start_workflow(
        "AgentWorkflow.run",
        args=[agent],
        id="assistant-workflow",
        task_queue="schwarm-task-queue"
    )
    
    # Send message
    await handle.signal(
        "handle_message",
        Message(content="Hello!")
    )
    
    # Get result
    result = await handle.result()
    print(f"Result: {result.value}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent Handoff Example

```python
# Create two agents
researcher = AgentConfig(
    name="researcher",
    provider_configurations=[
        ProviderConfig(provider_type="llm", provider_name="gpt-4"),
        ProviderConfig(provider_type="memory", provider_name="zep")
    ]
)

visualizer = AgentConfig(
    name="visualizer",
    provider_configurations=[
        ProviderConfig(provider_type="llm", provider_name="gpt-4"),
        ProviderConfig(provider_type="plot", provider_name="plotly")
    ]
)

# Research function that hands off to visualizer
async def research_topic(context: dict, topic: str) -> Result:
    # Research logic here...
    return Result(
        value="Research findings...",
        target_agent=visualizer  # Handoff to visualizer
    )
```

## Architecture

1. **Workflows (`workflows/agent.py`)**
   - Represents agent execution
   - Handles provider initialization
   - Manages message processing
   - Coordinates agent handoffs

2. **Activities**
   - `providers.py`: Provider lifecycle management
   - `execution.py`: Function execution and decision making

3. **Models (`models.py`)**
   - `AgentConfig`: Agent configuration
   - `ProviderConfig`: Provider configuration
   - `Message`: Message representation
   - `Result`: Function results
   - `ResultDictionary`: Workflow-safe result representation

## Benefits

1. **Durability**
   - All state is persisted
   - Automatic retries on failure
   - Recoverable from crashes

2. **Observability**
   - Track workflow progress
   - Monitor provider states
   - Debug execution flow

3. **Scalability**
   - Activities run independently
   - Built-in queuing
   - Distributed execution

## Development

To run the example:

1. Start Temporal server:
```bash
temporal server start-dev
```

2. Run the example:
```bash
python examples/08_temporal/app.py
