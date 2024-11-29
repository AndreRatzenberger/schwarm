"""Simplest Schwarm example."""

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent

# Create an agent with the name "hello_agent"
hello_agent = Agent(name="hello_agent")

# Start the agent
Schwarm().quickstart(agent=hello_agent)

# What model it it using?
# The first one it is going to find in either your env variables or .env files or whatever.
