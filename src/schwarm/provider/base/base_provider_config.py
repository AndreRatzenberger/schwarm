"""Base configuration for all providers."""

from enum import Enum

from pydantic import BaseModel, Field

from schwarm.models.types import Agent


class ProviderScope(Enum):
    """Defines how providers are managed in the system."""

    GLOBAL = "global"  # Single instance shared across all agents (e.g., vector store)
    AGENT = "agent"  # New instance per agent (e.g., LLM with specific settings)
    EPHEMERAL = "ephemeral"  # Created on demand, no persistence (e.g., API calls)


class BaseProviderConfig(BaseModel):
    """Base configuration for all providers."""

    agent: Agent = Field(..., description="Agent that this provider is associated with")
    provider_name: str = Field(..., description="Unique identifier for the provider")
    provider_type: str = Field(..., description="Type of provider (e.g., 'llm', 'memory', etc.)")
    scope: ProviderScope = Field(default=ProviderScope.AGENT, description="Provider lifecycle scope")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")

    class Config:
        """Pydantic configuration."""

        validate_assignment = True
