"""Core models for temp_schwarm."""

from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    """Base configuration for providers."""

    provider_type: str
    provider_name: str
    scope: str = "scoped"  # global, scoped, or ephemeral
    enabled: bool = True
    settings: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    provider_configurations: list[ProviderConfig]
    description: str = ""
    instructions: str = "You are a helpful agent."


@dataclass
class Message:
    """A message in the system."""

    content: str
    role: str = "user"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    """Result from an agent's work."""

    value: Any
    context_variables: dict[str, Any] = field(default_factory=dict)
    target_agent: AgentConfig | None = None


class ResultDictionary:
    """Dictionary representation of a Result for workflow state."""

    def __init__(
        self, value: Any, context_variables: dict[str, Any] | None = None, target_agent: dict[str, Any] | None = None
    ):
        self.value = value
        self.context_variables = context_variables or {}
        self.target_agent = target_agent
        self._is_awaited = False

    def __await__(self) -> Generator[None, None, "ResultDictionary"]:
        """Make ResultDictionary awaitable for Temporal compatibility."""
        yield
        return self

    @classmethod
    def from_result(cls, result: Result) -> "ResultDictionary":
        """Create ResultDictionary from Result."""
        return cls(
            value=result.value,
            context_variables=result.context_variables,
            target_agent=result.target_agent.__dict__ if result.target_agent else None,
        )

    def to_result(self) -> Result:
        """Convert back to Result."""
        target_agent = AgentConfig(**self.target_agent) if self.target_agent else None
        return Result(value=self.value, context_variables=self.context_variables, target_agent=target_agent)

    def __dict__(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {"value": self.value, "context_variables": self.context_variables, "target_agent": self.target_agent}
