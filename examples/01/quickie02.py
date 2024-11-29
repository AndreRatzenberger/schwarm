# Quickie #2

import os
from pathlib import Path

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent
from schwarm.provider.llm_provider import LLMConfig

my_first_agent = Agent(
    name="my_first_agent", configs=[LLMConfig(name="ollama_chat/qwen2.5:7b-instruct-q8_0", streaming=True)]
)  # enter "ollama_chat/<model_name>"


# open prompts/v0.txt and assign it to var prompt
script_path = Path(os.path.abspath(__file__)).parent
with open(f"{script_path}/prompts/v0.txt", encoding="utf-8") as f:
    my_first_agent.instructions = f.read()


Schwarm(interaction_mode="stop_and_go").quickstart(agent=my_first_agent, input="I want a sleek web shop")
