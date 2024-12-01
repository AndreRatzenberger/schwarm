"""Shared type definitions."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class Message:
    """A message in a conversation."""

    content: str
    role: str = "user"
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class Tool(Protocol):
    """Protocol for tools that agents can use."""

    name: str
    description: str

    def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        ...


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    model: str
    api_key: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None


@dataclass
class CompletionResult:
    """Result of a completion request."""

    message: Message
    raw_response: Any | None = None


@dataclass
class ConversationResult:
    """Result of a conversation."""

    messages: list[Message]
    context: dict[str, Any]
