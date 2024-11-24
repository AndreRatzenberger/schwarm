from schwarm.models.agent import Agent
from schwarm.provider.litellm_provider import LiteLLMConfig

hello_agent = Agent(name="hello_agent", configs=[LiteLLMConfig(enable_cache=True, enable_debug=True)])
hello_agent.quickstart(mode="interactive")
