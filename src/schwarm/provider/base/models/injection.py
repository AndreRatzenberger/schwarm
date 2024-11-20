"""Type-safe injection system for provider modifications."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal, TypeAlias

from schwarm.models.agent import Agent


class InjectionTarget(Enum):
    """Available targets for injection tasks."""

    INSTRUCTION = "instruction"
    MESSAGE = "message"
    CONTEXT = "context"
    AGENT = "agent"
    TOOL = "tool"


@dataclass
class InstructionInjection:
    """Data to inject into instructions."""

    content: str
    position: Literal["prefix", "suffix", "replace"] = "suffix"


@dataclass
class MessageInjection:
    """Data to inject into message history."""

    content: str
    role: str = "system"


@dataclass
class ContextInjection:
    """Data to inject into context variables."""

    key: str
    value: Any


# Type alias for all possible injection values
InjectionValue: TypeAlias = InstructionInjection | MessageInjection | ContextInjection | Agent | dict[str, Any]


@dataclass
class InjectionTask:
    """Type-safe injection task.

    This replaces the previous InjectionTask model with a more type-safe version
    that properly handles different types of injections.
    """

    target: InjectionTarget
    value: InjectionValue

    def __post_init__(self) -> None:
        """Validate injection value matches target type."""
        valid_types = {
            InjectionTarget.INSTRUCTION: InstructionInjection,
            InjectionTarget.MESSAGE: MessageInjection,
            InjectionTarget.CONTEXT: ContextInjection,
            InjectionTarget.AGENT: Agent,
            InjectionTarget.TOOL: dict,
        }

        expected_type = valid_types[self.target]
        if not isinstance(self.value, expected_type):
            raise TypeError(
                f"Invalid value type for target {self.target}. "
                f"Expected {expected_type.__name__}, got {type(self.value).__name__}"
            )
