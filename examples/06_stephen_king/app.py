"""A general purpose long-term context agent system.

Agent flow:

Read history -> Update context -> Generate instructions -> Execute instructions -> Save history -> Update context -> Repeat
"""

from typing import cast

from rich.console import Console

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.llm_provider import LLMConfig
from schwarm.provider.provider_manager import ProviderManager
from schwarm.provider.zep_provider import ZepConfig, ZepProvider
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/06_stephen_king"
MIN_FACT_RATING = 0.3

zep_config = ZepConfig(
    user_id="stephen_king69",
    provider_name="zep",
    zep_api_key="zepzep",
    zep_api_url="http://localhost:8000",
    min_fact_rating=MIN_FACT_RATING,
    zep_prompt="""Rate information based on narrative value and story cohesion:
                                    - Plot advancement potential
                                    - Character development contribution
                                    - Theme reinforcement
                                    - World-building enhancement
                                    - Narrative flow impact

                                    Scale:
                                    High: Essential narrative element
                                    High: Strong story contribution
                                    Med: Useful supporting details
                                    Med: Minor narrative value
                                    Low: No meaningful story impact

                                    When evaluating information, consider:
                                    1. How does it advance the current plot thread?
                                    2. What character insights does it provide?
                                    3. How does it reinforce key themes?
                                    4. Does it maintain narrative consistency?
                                    5. Is it placed at an optimal point in the story?
                                    """,
)

stephen_king_agent = Agent(name="stephen_king69", configs=[LLMConfig(enable_cache=True), zep_config])


def instruction_stephen_king_agent(context_variables: ContextVariables) -> str:
    """Return the instructions for the user agent."""
    instruction = """
    You are one of the best authors on the world. you are tasked to write your newest story.
    Execute "write_batch" to write something down to paper.
    Execute "remember_things" to remember things you aren't sure about or to check if something is at odds with previous established facts.
    
    """
    if "book" in context_variables:
        book = context_variables["book"]
        addendum = "\n\n You current story has this many words right now (goal: 10000): " + str(len(book) / 8)

        memory = cast(ZepProvider, ProviderManager.get_provider("zep")).get_memory()
        facts = f"\n\n\nRelevant facts about the story so far:\n{memory}"
        instruction += addendum + facts
    return instruction


def write_batch(context_variables: ContextVariables, text: str) -> Result:
    """Write down your story."""
    cast(ZepProvider, ProviderManager.get_provider("zep")).add_to_memory(text)
    if "book" not in context_variables:
        context_variables["book"] = ""
    context_variables["book"] += text
    return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)


def remember_things(context_variables: ContextVariables, what_you_want_to_remember: str) -> Result:
    """If you aren't sure about something that happened in the story, use this tool to remember it."""
    results = cast(ZepProvider, ProviderManager.get_provider("zep")).search_memory(what_you_want_to_remember)

    result = ""
    for res in results:
        result += f"\n{res.fact}"

    return Result(value=f"{result}", context_variables=context_variables, agent=stephen_king_agent)


stephen_king_agent.instructions = instruction_stephen_king_agent
stephen_king_agent.functions = [write_batch, remember_things]

input = """
Write a story set in the SCP universe. It should follow a group of personel of the SCP foundation, and the adventures their work provides.
The story should be around 10000 words long, and should be a mix of horror and science fiction.
Start by create an outline for the story, and then write the first chapter.
"""

response = Schwarm().quickstart(stephen_king_agent, input)
