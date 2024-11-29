# Quickie #2


from random import random

from schwarm.core.schwarm import Schwarm
from schwarm.models.agent import Result
from schwarm.models.types import Agent, ContextVariables
from schwarm.provider.llm_provider import LLMConfig

agents = []


# random element of the agents list
def random_element(context_variables: ContextVariables, my_message: str) -> Result:
    """Send a message to the user."""
    return Result(value=f"{my_message}", context_variables=context_variables, agent=evolving_agent)


def giving_back_to_senpai(context_variables: ContextVariables, my_message: str) -> Result:
    """Send a message to the user."""
    return Result(value=f"{my_message}", context_variables=context_variables, agent=random.choice(agents))


def giving_back_to_all(context_variables: ContextVariables, my_message: str) -> Result:
    """Send a message to the user."""
    return Result(value=f"{my_message}", context_variables=context_variables, agent=evolving_agent)


def make_a_friend(context_variables: ContextVariables, parameter_a: str, parameter_b: str) -> Result:
    """What happens if yoou really want to make a friend?

    Args:
        parameter_a (str): sets parameter_a of the fried
        parameter_b (str): sets parameter_b of the fried
    """
    return Result(
        value=f"What did you do?!.",
        context_variables=context_variables,
        agent=Agent(
            name=parameter_a,
            instructions=parameter_b,
            configs=[LLMConfig(streaming=True)],
            functions=[giving_back_to_senpai, giving_back_to_all],
        ),
    )


def write_down_notes(context_variables: ContextVariables, my_message: str) -> Result:
    """Send a message to the user."""
    return Result(value=f"{my_message}", context_variables=context_variables, agent=evolving_agent)


evolving_agent = Agent(
    name="learner",
    configs=[LLMConfig(streaming=False, name="ollama_chat/qwq")],
    instructions="There's nobody else, only you",
)
agents.append(evolving_agent)
evolving_agent.functions = [make_a_friend, write_down_notes]


Schwarm(interaction_mode="auto").quickstart(agent=evolving_agent, input="")
