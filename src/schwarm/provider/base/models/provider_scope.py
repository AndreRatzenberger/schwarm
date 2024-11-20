"""Provider scope determines lifecycle and state management."""

from enum import Enum


class ProviderScope(Enum):
    """Provider scope determines lifecycle and state management."""

    GLOBAL = "global"  # One instance for entire Schwarm runtime
    SCOPED = "scoped"  # New instance per agent configuration
    EPHEMERAL = "ephemeral"  # Created on demand, no state
