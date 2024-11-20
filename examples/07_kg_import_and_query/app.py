"""A general purpose long-term context agent system.

Agent flow:

Read history -> Update context -> Generate instructions -> Execute instructions -> Save history -> Update context -> Repeat
"""

from typing import Any

from rich.console import Console

from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Agent
from schwarm.models.types import Result
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.provider.models.zep_config import ZepConfig
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/07_kg_import_and_query"


stephen_king_agent = Agent(
    name="mr_stephen_king", provider_configurations=[LiteLLMConfig(enable_cache=True), ZepConfig()]
)


def instruction_stephen_king_agent(context_variables: dict[str, Any]) -> str:
    """Return the instructions for the user agent."""
    instruction = """
    You are one of the best authors on the world. you are tasked to write your newest story.
    Execute "write_batch" to write something down to paper.
    Execute "remember_things" to remember things you aren't sure about or to check if something is at odds with previous established facts.

    """
    if "book" in context_variables:
        book = context_variables["book"]
        addendum = "\n\n You current story has this many words right now (goal: 10000): " + str(len(book) / 8)
        instruction += addendum
    return instruction


stephen_king_agent.instructions = instruction_stephen_king_agent


def write_batch(context_variables: dict[str, Any], text: str) -> Result:
    """Write down your story."""
    context_variables["zep_provider"].add_to_memory(text)
    context_variables["book"] += text
    return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)


def remember_things(context_variables: dict[str, Any], what_you_want_to_remember: str) -> Result:
    """If you aren't sure about something that happened in the story, use this tool to remember it."""
    result = context_variables["zep_provider"].search_memory(what_you_want_to_remember)
    if result:
        for res in result:
            result += f"\n{res.fact}"

    return Result(value=f"{result}", context_variables=context_variables, agent=stephen_king_agent)


stephen_king_agent.functions = [write_batch, remember_things]

input = """
Write a story set in the SCP universe. It should follow a group of personnel of the SCP foundation, and the adventures their work provides.
The story should be around 10000 words long, and should be a mix of horror and science fiction.
Start by create an outline for the story, and then write the first chapter.
"""

response = Schwarm().quickstart(stephen_king_agent, input, mode="interactive")
