# Examples and Patterns

This guide provides practical examples and common patterns for using the Schwarm framework effectively.

## Basic Examples

### Simple Question-Answer Agent
```python
from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent
from schwarm.models.message import Message
from schwarm.provider.models.lite_llm_config import LiteLLMConfig
from schwarm.provider.models.debug_provider_config import DebugProviderConfig

# Create agent
agent = Agent(
    name="qa_agent",
    model="gpt-4",
    instructions="You are a helpful assistant that answers questions clearly and concisely.",
    providers=[
        LiteLLMConfig(
            provider_name="lite_llm",
            provider_lifecycle="singleton",
            enable_cache=True
        ),
        DebugProviderConfig(
            provider_name="debug",
            provider_lifecycle="scoped",
            show_instructions=True
        )
    ]
)

# Run agent
schwarm = Schwarm()
response = schwarm.quickstart(
    agent=agent,
    input_text="What is the capital of France?",
    mode="auto"
)

# Get answer
answer = response.messages[-1].content
print(answer)
```

### Agent with Tool Usage
```python
from typing import Any

def search_web(query: str) -> str:
    """Search the web for information."""
    # Implement web search
    return f"Results for: {query}"

def save_to_file(filename: str, content: str) -> str:
    """Save content to a file."""
    with open(filename, 'w') as f:
        f.write(content)
    return f"Saved to {filename}"

# Create agent with tools
researcher = Agent(
    name="researcher",
    model="gpt-4",
    instructions="""You are a research agent. Use the search_web tool to find information,
    and save_to_file to store your findings.""",
    functions=[search_web, save_to_file],
    providers=[
        LiteLLMConfig(provider_name="lite_llm"),
        DebugProviderConfig(provider_name="debug")
    ]
)

# Run research task
response = schwarm.quickstart(
    agent=researcher,
    input_text="Research the history of Paris and save it to paris.txt",
    mode="interactive"  # Show tool usage
)
```

## Advanced Patterns

### Multi-Agent Conversation
```python
# Create agents
writer = Agent(
    name="writer",
    model="gpt-4",
    instructions="You are a creative writer.",
    providers=[LiteLLMConfig(provider_name="lite_llm")]
)

editor = Agent(
    name="editor",
    model="gpt-4",
    instructions="You are an editor who improves text.",
    providers=[LiteLLMConfig(provider_name="lite_llm")]
)

def transfer_to_editor(text: str) -> Agent:
    """Transfer text to editor."""
    return editor

def transfer_to_writer(feedback: str) -> Agent:
    """Transfer feedback to writer."""
    return writer

# Set up agent functions
writer.functions = [transfer_to_editor]
editor.functions = [transfer_to_writer]

# Run conversation
response = schwarm.run(
    agent=writer,
    messages=[Message(role="user", content="Write a story about a cat.")],
    context_variables={},
    max_turns=10  # Allow back-and-forth
)
```

### State Management with Context
```python
from schwarm.provider.models.context_provider_config import ContextProviderConfig

# Create agent with context
agent = Agent(
    name="stateful_agent",
    model="gpt-4",
    instructions="You are an agent that remembers context.",
    providers=[
        LiteLLMConfig(provider_name="lite_llm"),
        ContextProviderConfig(
            provider_name="context",
            provider_lifecycle="scoped"
        )
    ]
)

# First interaction
response1 = schwarm.quickstart(
    agent=agent,
    input_text="My name is Alice.",
    context_variables={}
)

# Second interaction uses previous context
response2 = schwarm.quickstart(
    agent=agent,
    input_text="What's my name?",
    context_variables=response1.context_variables
)
```

### Budget-Aware Agent
```python
from schwarm.provider.models.budget_provider_config import BudgetProviderConfig

# Create budget-aware agent
agent = Agent(
    name="budget_agent",
    model="gpt-4",
    instructions="You are a cost-conscious agent.",
    providers=[
        LiteLLMConfig(provider_name="lite_llm"),
        BudgetProviderConfig(
            provider_name="budget",
            provider_lifecycle="scoped",
            max_spent=1.0,
            max_tokens=1000,
            effect_on_exceed="error"
        )
    ]
)

# Run with budget tracking
try:
    response = schwarm.quickstart(
        agent=agent,
        input_text="Generate a long story.",
        mode="auto"
    )
except ValueError as e:
    print(f"Budget exceeded: {e}")
```

## Common Patterns

### 1. Provider Composition
Combine providers for complex functionality:
```python
agent = Agent(
    name="complex_agent",
    providers=[
        LiteLLMConfig(...),      # LLM capabilities
        BudgetProviderConfig(...),# Cost tracking
        ContextProviderConfig(...),# State management
        DebugProviderConfig(...), # Debugging
        ZepProviderConfig(...)    # Long-term memory
    ]
)
```

### 2. Dynamic Instructions
Use callable instructions for context-aware behavior:
```python
def dynamic_instructions(context_variables: dict[str, Any]) -> str:
    user_name = context_variables.get("user_name", "user")
    return f"""You are talking to {user_name}.
    Be friendly and remember their preferences."""

agent = Agent(
    name="dynamic_agent",
    instructions=dynamic_instructions
)
```

### 3. Tool Chaining
Chain tools together for complex tasks:
```python
def search(query: str) -> str:
    return f"Results for {query}"

def summarize(text: str) -> str:
    return f"Summary of {text}"

def save(text: str) -> str:
    return f"Saved: {text}"

agent = Agent(
    name="chain_agent",
    functions=[search, summarize, save],
    instructions="""Follow these steps:
    1. Search for information
    2. Summarize the results
    3. Save the summary"""
)
```

### 4. Error Recovery
Handle errors gracefully with the debug provider:
```python
agent = Agent(
    name="robust_agent",
    providers=[
        LiteLLMConfig(...),
        DebugProviderConfig(
            save_logs=True,
            show_function_calls=True
        )
    ],
    instructions="""If a tool fails:
    1. Log the error
    2. Try an alternative approach
    3. If all fails, explain the issue"""
)
```

### 5. State Transitions
Handle state changes with context provider:
```python
def change_state(context_variables: dict[str, Any], new_state: str) -> dict[str, Any]:
    context_variables["state"] = new_state
    return context_variables

agent = Agent(
    name="state_agent",
    providers=[ContextProviderConfig(...)],
    functions=[change_state]
)
```

## Testing Patterns

### 1. Mock Providers
```python
class MockLLMProvider(BaseLLMProvider):
    def complete(self, messages: list[Message], **kwargs) -> Message:
        return Message(role="assistant", content="Mock response")

# Use in tests
agent = Agent(
    name="test_agent",
    providers=[MockLLMProvider.config]
)
```

### 2. Test Context
```python
@pytest.fixture
def test_context():
    return {
        "user_name": "test_user",
        "state": "initial"
    }

def test_agent_with_context(test_context):
    response = schwarm.quickstart(
        agent=agent,
        input_text="Hello",
        context_variables=test_context
    )
    assert "test_user" in response.messages[-1].content
```

### 3. Event Testing
```python
def test_budget_tracking():
    # Create agent with budget provider
    agent = Agent(
        providers=[
            BudgetProviderConfig(max_spent=1.0)
        ]
    )
    
    # Run until budget exceeded
    with pytest.raises(ValueError) as exc:
        schwarm.run(agent, messages=[...])
    
    assert "Budget exceeded" in str(exc.value)
```

## Performance Patterns

### 1. Caching
```python
agent = Agent(
    providers=[
        LiteLLMConfig(
            enable_cache=True,
            cache_type="disk",
            cache_dir=".cache"
        )
    ]
)
```

### 2. Parallel Tools
```python
agent = Agent(
    parallel_tool_calls=True,
    functions=[tool1, tool2, tool3]
)
```

### 3. Token Optimization
```python
agent = Agent(
    providers=[
        BudgetProviderConfig(
            max_tokens=1000,
            effect_on_exceed="warning"
        )
    ],
    instructions="Be concise to save tokens."
)
