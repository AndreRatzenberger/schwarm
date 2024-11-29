import os

from schwarm.models.agent import Agent
from schwarm.models.agents.handoff_agent import HandoffAgent
from schwarm.provider.llm_provider import LLMConfig
from schwarm.provider.zep_provider import ZepConfig


# Get a list of all python files in a directory and its subdirectories
def get_python_files(directory):
    """get_python_files(directory) -> list of strings"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


directory = "/d:/Projects/_published/schwarm/examples/02"
python_files = get_python_files(directory)
print(python_files)


project_agent = HandoffAgent(
    name="project_agent",
    description="""
                        This agent is responsible for managing a project.
                        It oversees all agents and is orchestrating the project.
                        """,
    configs=[LLMConfig()],
)

knowledge_agent = Agent(
    name="knowledge_agent",
    description="""
                        This agent is responsible for managing knowledge.
                        It can be used to translate repositories into querieable knowledge 
                        or the state of a currently worked on project.
                        """,
    configs=[LLMConfig(), ZepConfig(zep_api_key="zepzep")],
)

plan_agent = Agent(
    name="plan_agent",
    description="""
                    This agent is responsible for generating a project plan.
                    It will focus on actual dewvelopment tasks and their dependencies,
                    so everyone knows what to do next and have a clear plan.
                        """,
    configs=[LLMConfig()],
)
user_story_agent = Agent(
    name="user_story_agent",
    description="""
                    Based on the project plan, this agent will generate user stories.
                    These are actionable tasks that can be assigned to developers, and are doable in a short time.
                    user stories are the smallest unit of work in a project and should not be bigger than 100 lines of code.
                    The description of a user story should be clear and concise, and contains every information needed to complete the task.
                        """,
    configs=[LLMConfig()],
)
coding_agent = Agent(
    name="coding_agent", description="An agent that is implementing user stories", configs=[LLMConfig()]
)
testing_agent = Agent(
    name="testing_agent",
    description="An agent that is writing tests for the code of the coding agent",
    configs=[LLMConfig()],
)
