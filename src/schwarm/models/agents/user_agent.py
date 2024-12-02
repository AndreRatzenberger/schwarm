"""User agent for interacting with the system."""

from pydantic import Field

from schwarm.models.agent import Agent, Result
from schwarm.provider.user_interaction_provider import UserInteractionConfig


class UserAgent(Agent):
    """An agent which does nothing except routing user messages into the system."""

    agent_to_pass_to: Agent | None = Field(default=None, description="The agent to pass the user message to.")
    default_handoff_agent: bool = Field(default=False, description="Whether this agent is the default handoff agent.")

    def pass_to(self) -> Result:
        return Result(agent=self.agent_to_pass_to)

    def __init__(self, agent_to_pass_to: Agent, default_handoff_agent: bool = False):
        super().__init__()
        self.name = "UserAgent"
        self.model = "gpt-4"
        self.agent_to_pass_to = agent_to_pass_to
        self.default_handoff_agent = default_handoff_agent
        self.description = "User agent for interacting with the system."
        self.instructions = "You are a user agent."
        self.functions = [self.pass_to]
        self.tool_choice = "none"
        self.token_spent = 0
        self.total_cost = 0.0
        self.parallel_tool_calls = False
        self.configs = [UserInteractionConfig()]
        self.provider_names = []
