"""Implementation of https://microsoft.github.io/autogen/dev/user-guide/agentchat-user-guide/examples/literature-review.html.

This example showcases how easy it is to migrate autogen examples to the Schwarm framework and improve on them DRAMATICALLY!



The original autogen example defines following agents:

google_search_agent
arxiv_search_agent
report_agent

in a round-robin way: google_search_agent -> arxiv_search_agent -> report_agent -> google_search_agent -> ...

tools are google_search_tool, arxiv_search_tool

Now the twist:
Instead of a single run system we make it so, that the system will run again with follow-up questions until the report_agent is satisfied with the report.

Let's get to work!
"""

import os
import shutil

import arxiv
from rich.console import Console

from schwarm.core.schwarm import Schwarm
from schwarm.models.message import Message
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.information_provider import InformationConfig
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.utils.file import save_dictionary_list, save_text_to_file
from schwarm.utils.settings import APP_SETTINGS

console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/04_autogen/.data"
if os.path.exists(APP_SETTINGS.DATA_FOLDER):
    shutil.rmtree(APP_SETTINGS.DATA_FOLDER)

# Optionally, recreate the folder if needed
os.makedirs(APP_SETTINGS.DATA_FOLDER)


#### AGENTS ####


google_search_agent = Agent(
    name="google_search_agent",
    configs=[
        LiteLLMConfig(enable_cache=True),
        InformationConfig(
            show_function_calls=True,
            function_calls_wait_for_user_input=True,
            show_instructions=True,
            instructions_wait_for_user_input=True,
            max_length=-1,
        ),
    ],
)
arxiv_search_agent = Agent(
    name="arxiv_search_agent",
    configs=[
        LiteLLMConfig(enable_cache=True),
        InformationConfig(
            show_function_calls=True,
            function_calls_wait_for_user_input=True,
            show_instructions=True,
            instructions_wait_for_user_input=True,
            max_length=-1,
        ),
    ],
)
report_agent = Agent(
    name="report_agent",
    configs=[
        LiteLLMConfig(enable_cache=True),
        InformationConfig(
            show_function_calls=True,
            function_calls_wait_for_user_input=True,
            show_instructions=True,
            instructions_wait_for_user_input=True,
            max_length=-1,
        ),
    ],
)
user_agent = Agent(
    name="user_agent",
    tool_choice="none",
    configs=[
        LiteLLMConfig(enable_cache=True),
        InformationConfig(
            show_function_calls=True,
            function_calls_wait_for_user_input=True,
            show_instructions=True,
            instructions_wait_for_user_input=True,
            max_length=-1,
        ),
    ],
)

### Instructions ###


def user_agent_instructions(context_variables: ContextVariables):
    """Instructions for the google search agent."""
    instruction = """You are a helpful assistant that focuses on producing beautifully formatted reports.
    """
    return instruction


def google_search_agent_instructions(context_variables: ContextVariables):
    """Instructions for the google search agent."""
    instruction = """Your job is to search for the latest research on the topic.
    You can use the google_search_tool to help you with that.
    """
    return instruction


def arxiv_search_agent_instructions(context_variables: ContextVariables):
    """Instructions for the arxiv search agent."""
    instruction = """Your job is to search for the latest research on the topic.
    You can use the arxiv_search_tool to help you with that.
    """
    return instruction


def report_agent_instructions(context_variables: ContextVariables):
    """Instructions for the report agent."""
    instruction = """You are a helpful assistant.
    Your task is to synthesize data extracted into a high quality in-depth literature review including CORRECT references.
    You MUST write a report that is formatted as a literature review with CORRECT references.
    Use write_report to write the report, then call transfer_to_google_search with a follow up query to improve or expand the report.
    """

    if "reports" in context_variables:
        instruction += "\n\nHere are the reports you have written so far:\n"
        for i, report in enumerate(context_variables["reports"]):
            instruction += f"\n{i + 1}. {report}"
    return instruction


google_search_agent.instructions = google_search_agent_instructions
arxiv_search_agent.instructions = arxiv_search_agent_instructions
report_agent.instructions = report_agent_instructions
user_agent.instructions = user_agent_instructions


### Functions ###
# TODO Extract headings out of report -> iterate over every heading


def google_search(
    context_variables: ContextVariables, query: str, num_results: int = 5, max_chars: int = 2500
) -> Result:  # type: ignore[type-arg]
    """Search Google for the query and return the results including snippets and content."""
    import os
    import time

    import requests
    from bs4 import BeautifulSoup
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

    if not api_key or not search_engine_id:
        raise ValueError("API key or Search Engine ID not found in environment variables")

    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": api_key, "cx": search_engine_id, "q": query, "num": num_results}

    response = requests.get(url, params=params)  # type: ignore[arg-type]

    if response.status_code != 200:
        print(response.json())
        raise Exception(f"Error in API request: {response.status_code}")

    results = response.json().get("items", [])

    def get_page_content(url: str) -> str:
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            text = soup.get_text(separator=" ", strip=True)
            words = text.split()
            content = ""
            for word in words:
                if len(content) + len(word) + 1 > max_chars:
                    break
                content += " " + word
            return content.strip()
        except Exception as e:
            print(f"Error fetching {url}: {e!s}")
            return ""

    enriched_results = []
    for item in results:
        body = get_page_content(item["link"])
        enriched_results.append(
            {  # type: ignore
                "title": item["title"],
                "link": item["link"],
                "snippet": item["snippet"],
                "body": body,
            }
        )
        time.sleep(1)  # Be respectful to the servers

    save_dictionary_list("google_results.json", enriched_results)  # type: ignore

    context_variables["google_results"] = enriched_results

    return Result(value=f"{enriched_results}", context_variables=context_variables, agent=arxiv_search_agent)


def arxiv_search(context_variables: ContextVariables, query: str, max_results: int = 2) -> Result:  # type: ignore[type-arg]
    """Search Arxiv for papers and return the results including abstracts."""
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)

    results = []
    for paper in client.results(search):
        results.append(
            {  # type: ignore
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.strftime("%Y-%m-%d"),
                "abstract": paper.summary,
                "pdf_url": paper.pdf_url,
            }
        )

    # # Write results to a file
    # with open('arxiv_search_results.json', 'w') as f:
    #     json.dump(results, f, indent=2)

    save_dictionary_list("arxiv_search_results.json", results)  # type: ignore

    context_variables["arxiv_results"] = results

    return Result(value=f"{results}", context_variables=context_variables, agent=report_agent)


def transfer_to_google_search(context_variables: ContextVariables, new_query: str) -> Result:  # type: ignore[type-arg]
    """Transfer the query to the google search agent with a follow-up question or query."""
    context_variables["query"] = new_query
    return Result(value=f"Query: {new_query}", context_variables=context_variables, agent=google_search_agent)


def write_report(context_variables: ContextVariables, report: str) -> Result:  # type: ignore[type-arg]
    """Write the report in beautiful markdown to a file."""
    save_text_to_file("report.md", report)  # type: ignore

    if "reports" not in context_variables:
        context_variables["reports"] = []

    context_variables["reports"].append(report)  # type: ignore
    return Result(value=f"Report: {report}", context_variables=context_variables, agent=report_agent)


def finalize_report(context_variables: ContextVariables, final_report: str) -> Result:  # type: ignore[type-arg]
    """Finalize the report and finish the process."""
    save_text_to_file("final_report.md", final_report)  # type: ignore
    return Result(value=f"Report finalized {final_report}", context_variables=context_variables, agent=user_agent)


google_search_agent.functions.append(google_search)
arxiv_search_agent.functions.append(arxiv_search)
report_agent.functions.append(transfer_to_google_search)  # loop back to google_search
report_agent.functions.append(write_report)
# report_agent.functions.append(finalize_report)


input = "the latest research in AI agents"

response = Schwarm().run(
    google_search_agent,
    messages=[Message(role="user", content=input)],
    context_variables={},
    max_turns=100,
    execute_tools=True,
    show_logs=False,
)
