"""cli web researcher example."""
## AGENTS ##

import os

import report_system.report_agents as ra
import report_system.report_functions as rf
from rich import inspect
from rich.console import Console

from schwarm.core.schwarm import Schwarm
from schwarm.models.display_config import DisplayConfig
from schwarm.models.message import Message
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
if os.path.exists(f"{APP_SETTINGS.DATA_FOLDER}/report.md"):
    os.remove(f"{APP_SETTINGS.DATA_FOLDER}/report.md")


# Define the functions for each agent

ra.orchestrator_agent.functions = [
    rf.transfer_to_outline_generator,
    rf.transfer_to_writer,
]  # TODO: Generic transfer function -> rf.transfer(agent, pydantic_base_model)
ra.outline_generator_agent.functions = [rf.transfer_outline_to_orchestrator]
ra.writer_agent.functions = [rf.do_generate_text, rf.do_research]
ra.research_agent.functions = [rf.transfer_research_to_writer]
ra.editor_agent.functions = [rf.transfer_feedback_to_writer]

# input = "I need a blog on the benefits of AI in healthcare."
input = "I need a blog about the history of cats as pets"

schwarm = Schwarm()
schwarm.register_agent(ra.orchestrator_agent)
schwarm.register_agent(ra.outline_generator_agent)
schwarm.register_agent(ra.writer_agent)
schwarm.register_agent(ra.editor_agent)


response = Schwarm().run(
    ra.orchestrator_agent,
    messages=[Message(role="user", content=input)],
    context_variables={},
    model_override="gpt-4o",
    max_turns=100,
    execute_tools=True,
    display_config=DisplayConfig(
        show_function_calls=True,
        function_calls_wait_for_user_input=True,
        function_calls_print_context_variables=True,
        show_instructions=True,
        instructions_wait_for_user_input=True,
        show_budget=True,
        show_budget_table=True,
    ),
    show_logs=False,
)
# model_override="ollama_chat/qwen2.5:7b-instruct-q8_0",
inspect(response)
console.print(f"Report: {response.messages}")
