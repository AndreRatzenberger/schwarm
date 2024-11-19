"""Context variables model."""

from typing import Any, Union

from pydantic import BaseModel, Field


class ContextVariables(BaseModel):
    """A dictionary-like class for variables that can be used by agents."""

    variables: dict[str, Any] = Field(
        default_factory=dict, description="A dictionary of variables that can be used by agents."
    )

    def __getitem__(self, key: str) -> Any:
        """Get a variable value."""
        return self.variables[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a variable value."""
        self.variables[key] = value

    def __contains__(self, key: str) -> bool:
        """Check if a variable exists."""
        return key in self.variables

    def get(self, key: str, default: Any = None) -> Any:
        """Get a variable value with a default."""
        return self.variables.get(key, default)

    def update(self, other: Union[dict[str, Any], "ContextVariables"]) -> None:
        """Update variables from another dict or ContextVariables."""
        if isinstance(other, ContextVariables):
            self.variables.update(other.variables)
        else:
            self.variables.update(other)

    def copy(self) -> "ContextVariables":
        """Create a copy of the context variables."""
        return ContextVariables(variables=self.variables.copy())

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ContextVariables":
        """Create ContextVariables from a dictionary."""
        return cls(variables=d)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary."""
        return self.variables
