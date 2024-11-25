"""Minimal example."""

from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Agent
from schwarm.provider.litellm_provider import LiteLLMConfig

hello_agent = Agent(name="hello_agent", configs=[LiteLLMConfig(enable_cache=True)])


Schwarm().quickstart(hello_agent)
