# Quickie #2

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent
from schwarm.provider.llm_provider import LLMConfig

my_first_agent = Agent(
    name="my_first_agent", configs=[LLMConfig(name="ollama_chat/qwen2.5:7b-instruct-q8_0", streaming=True)]
)  # enter "ollama_chat/<model_name>"

my_first_agent.instructions = ""

Schwarm(interaction_mode="stop_and_go").quickstart(agent=my_first_agent, input="proof that sqr(2) is irrational")
