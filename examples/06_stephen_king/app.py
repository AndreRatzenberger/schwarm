"""A general purpose long-term context agent system.

Agent flow:

Read history -> Update context -> Generate instructions -> Execute instructions -> Save history -> Update context -> Repeat
"""

import uuid

from rich.console import Console
from zep_python import FactRatingInstruction
from zep_python.client import Zep
from zep_python.types import Message as ZepMessage

from schwarm.core.schwarm import Schwarm
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/06_stephen_king"
MIN_FACT_RATING = 0.3

zep = Zep(api_key="zepzep", base_url="http://localhost:8000")


user_id = "stephen_king69"
session_id = str(uuid.uuid4())


# zep.user.add(user_id=user_id)


book_rating_instruction = """Rate information based on narrative value and story cohesion:
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
"""


zep.memory.add_session(
    user_id=user_id,
    session_id=session_id,
    fact_rating_instruction=FactRatingInstruction(
        instruction=book_rating_instruction,
    ),
)


stephen_king_agent = Agent(name="mr_stephen_king", provider_config=LiteLLMConfig(enable_cache=True))


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

        memory = zep.memory.get("user_agent", min_rating=MIN_FACT_RATING)
        facts = f"\n\n\nRelevant facts about the story so far:\n{memory.relevant_facts}"
        instruction += addendum + facts
    return instruction


stephen_king_agent.instructions = instruction_stephen_king_agent


def split_text(text: str, max_length: int = 1000) -> list:
    """Split text into smaller chunks."""
    result = []
    if len(text) <= max_length:
        return [ZepMessage(role="user", content=text)]
    for i in range(0, len(text), max_length):
        result.append(ZepMessage(role="user", content=text[i : i + max_length], role_type="user"))
    return result


def write_batch(context_variables: ContextVariables, text: str) -> Result:
    """Write down your story."""
    zep.memory.add(session_id="user_agent", messages=split_text(text))
    context_variables["book"] += text
    return Result(value=f"{text}", context_variables=context_variables, agent=stephen_king_agent)


def remember_things(context_variables: ContextVariables, what_you_want_to_remember: str) -> Result:
    """If you aren't sure about something that happened in the story, use this tool to remember it."""
    response = zep.memory.search_sessions(
        text=what_you_want_to_remember,
        user_id=user_id,
        search_scope="facts",
        min_fact_rating=MIN_FACT_RATING,
    )
    result = ""
    if response.results:
        for res in response.results:
            result += f"\n{res.fact}"

    return Result(value=f"{result}", context_variables=context_variables, agent=stephen_king_agent)


stephen_king_agent.functions = [write_batch, remember_things]

input = """
Write a story set in the SCP universe. It should follow a group of personel of the SCP foundation, and the adventures their work provides.
The story should be around 10000 words long, and should be a mix of horror and science fiction.
Start by create an outline for the story, and then write the first chapter.
"""

response = Schwarm().quickstart(stephen_king_agent, input, mode="interactive")
