from rich.console import Console

from schwarm.core.agents.web_agent import WebAgent
from schwarm.core.schwarm import Schwarm
from schwarm.models.display_config import DisplayConfig
from schwarm.models.message import Message

console = Console()


web_agent = WebAgent(name="web_agent", query="OpenAI", mode="search", transfer_to=None)

input = "what are the latest news?"
# input = "visit https://huggingface.co/papers and summarize the latest research"


response = Schwarm().run(
    web_agent,
    messages=[Message(role="user", content=input)],
    context_variables={},
    model_override="gpt-4o",
    max_turns=100,
    execute_tools=True,
    display_config=DisplayConfig(
        show_function_calls=True,
        function_calls_wait_for_user_input=True,
        show_instructions=True,
        instructions_wait_for_user_input=True,
    ),
    show_logs=False,
)
