from pydantic import Field

from schwarm.models.agent import Agent, Result


class HandoffAgent(Agent):
    """Agent with special handoff capabilities."""

    possible_agents: list[Agent] = Field(default_factory=list, description="List of possible agents to handoff to")
    amount_of_agents: int = Field(default=0, description="Amount of agents to handoff to")
    duplicates_allowed: bool = Field(default=False, description="Whether duplicates are allowed")
    single_agent_fanout: bool = Field(
        default=False, description="A single agent fanout (A single agent is called multiple times)"
    )
    _internal_context: dict = Field(default_factory=dict, description="Internal context for handoff")

    def __init__(self, **data):
        """Create a new handoff agent."""
        super().__init__(**data)
        self.functions.append(self.handoff_to_agent)

    def instruction(self) -> str:
        """Return the instruction for this agent."""
        result = "These is all the information to the project you've got so far:"
        result += f"\n\n{super().instructions}"

        result = "\n\nThese are the possible agents to handoff to:"
        for agent in self.possible_agents:
            result += f"\n\n{agent.name}: {agent.description}"

        result += "\n\n Chose the most fitting agent."

        return "This agent can handoff to other agents."

    def handoff_to_agent(self, reason: str, agent_name: Agent) -> Result:
        """Handoff to a specific agent."""
        if agent_name not in self.possible_agents:
            return Result(
                value=f"Agent {agent_name} is not in the list of possible agents.",
                agent=self,
            )
        return Result()
