"""Minimal example."""

from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Agent
from schwarm.provider.llm_provider import LLMConfig

hello_agent = Agent(name="hello_agent", configs=[LLMConfig(name="ollama_chat/qwq", streaming=True)])

hello_agent.instructions = (
    "You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step."
)
input = """
 There are 2 houses, numbered 1 to 2 from left to right.
 Each house is occupied by a different person.
 Each house has a unique attribute for each of the following characteristics:
 - Each person has a unique name: **Arnold, Eric**
 - People own unique car models: **ford f150, tesla model 3**
 - The people keep unique animals: **cat, horse**
 
 **Clues**:
 1. Eric is directly left of the person who owns a Tesla Model 3.
 2. The person who keeps horses is in the first house.
"""

Schwarm().quickstart(hello_agent, input_text=input)
