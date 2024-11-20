"""Base configuration for providers."""

from enum import Enum

from pydantic import BaseModel, Field


class ProviderScope(Enum):
    """Defines how providers are managed in the system."""

    GLOBAL = "global"  # Single instance shared across all agents
    AGENT = "agent"  # New instance per agent
    EPHEMERAL = "ephemeral"  # Created on demand


class BaseProviderConfig(BaseModel):
    """Base configuration for all providers."""

    provider_name: str = Field(..., description="Unique identifier for the provider")
    provider_type: str = Field(..., description="Type of provider (e.g., 'llm', 'memory', etc.)")
    provider_class: str | None = Field(None, description="Full path to provider class")
    scope: ProviderScope = Field(default=ProviderScope.AGENT, description="Provider lifecycle scope")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")

    def get_provider_class(self) -> type:
        """Get the provider class for this configuration."""
        if not self.provider_class:
            raise ValueError("Provider class not specified in configuration")

        # Import the provider class dynamically
        module_path, class_name = self.provider_class.rsplit(".", 1)
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
