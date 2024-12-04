"""A general purpose long-term context agent system.

Agent flow:

Read history -> Update context -> Generate instructions -> Execute instructions -> Save history -> Update context -> Repeat
"""

from typing import cast

from rich.console import Console

from schwarm.core.schwarm import Schwarm
from schwarm.models.agents.user_agent import UserAgent
from schwarm.models.types import Agent, ContextVariables
from schwarm.provider.llm_provider import LLMConfig
from schwarm.provider.provider_manager import ProviderManager
from schwarm.provider.zep_provider import ZepConfig, ZepProvider
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/07_zep_chat"
MIN_FACT_RATING = 0.3

zep_config = ZepConfig(
    user_id="schwarm",
    provider_name="zep",
    zep_api_key="zepzep",
    zep_api_url="http://localhost:8000",
    min_fact_rating=MIN_FACT_RATING,
    on_completion_save_completion_to_memory=True,
)

chat_agent = Agent(name="schwarm", configs=[LLMConfig(enable_cache=True), zep_config])
user_agent = UserAgent(agent_to_pass_to=chat_agent, default_handoff_agent=True)


def instruction_chat_agent(context_variables: ContextVariables) -> str:
    """Return the instructions for the user agent."""
    instruction = """
    You are a cool chatbot. You can help users with their questions.
    """

    memory = cast(ZepProvider, ProviderManager.get_provider("zep")).get_memory()

    context_variables["facts"] = memory
    facts = f"\n\n\nRelevant facts collected so far:\n{memory}"
    instruction += facts
    return instruction


chat_agent.instructions = instruction_chat_agent


response = Schwarm().quickstart(user_agent)
