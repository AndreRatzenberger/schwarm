from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Agent
from schwarm.models.agents.user_agent import UserAgent
from schwarm.provider.llm_provider import LLMConfig

hello_agent = Agent(name="hello_agent", configs=[LLMConfig(name="ollama_chat/qwq", streaming=True)])

user = UserAgent(agent_to_pass_to=hello_agent, default_handoff_agent=True)


Schwarm().quickstart(agent=user)
