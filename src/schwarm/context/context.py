"""Schwarm context module.

This module contains the SchwarmContext class, which is used to store the context of the Schwarm application.
Agents in Schwarm are mostly stateless, and the context is used to store information that is shared between agents,
and also information needed to evaluate the state and performance of the system.

"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentHandOffLog(BaseModel):
    """Agent tree class."""

    agent: str = Field(description="The name of the agent.")
    handoffs_to: list[str] = Field(default_factory=list, description="The children of the agent.")


class ContextManager(BaseModel):
    """Schwarm context class."""

    agents: list[AgentHandOffLog] = Field(default_factory=list, description="The agent tree.")

    event_log: list[tuple[datetime, str]] = Field(
        default=[], description="A list of events that have occurred in the system."
    )
    variables: dict[str, Any] = Field(
        default_factory=dict, description="A dictionary of variables that can be used by agents."
    )

    def add_variable(self, name: str, value: Any):
        """Adds a variable to the context."""
        self.variables[name] = value

    def get_variable(self, name: str) -> Any:
        """Gets a variable from the context."""
        return self.variables.get(name)

    def add_event(self, event: str):
        """Adds an event to the event log."""
        self.event_log.append((datetime.now(), event))

    def add_agent(self, agent_name: str, next_agent_name: str | None = None):
        """Adds an agent to the agent tree."""
        if next_agent_name:
            self._add_handoff(agent_name, next_agent_name)
        else:
            self.agents.append(AgentHandOffLog(agent=agent_name))

    def _add_handoff(self, agent: str, child: str):
        """Adds an agent to a parent agent."""
        for agent_tree in self.agents:
            if agent_tree.agent == agent:
                agent_tree.handoffs_to.append(child)
                return
