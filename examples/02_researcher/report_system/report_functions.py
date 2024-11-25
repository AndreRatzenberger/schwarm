"""This module contains the functions for the report system example."""

import os

from pydantic import BaseModel
from rich.console import Console
from tavily import TavilyClient

import report_system.report_agents as ra
from schwarm.models.message import Message
from schwarm.models.types import ContextVariables, Result
from schwarm.provider.litellm_provider import LiteLLMConfig, LiteLLMProvider
from schwarm.utils.file import load_dictionary_list, save_dictionary_list, save_text_to_file

console = Console()


class Report(BaseModel):
    """A report object to store the user query and status of the report."""

    user_query: str
    title: str
    report_type: str
    finished_parts: list[tuple[str, str]] = []


def transfer_outline_to_orchestrator(context_variables: ContextVariables, report_outline: list[str]) -> Result:
    """Calls the orchestrator with an outline for the requested report.

    Arguments:
        report_outline: The outline of the report. List of strings. each element is a heading or a paragraph summary
    """
    context_variables["report_outline"] = report_outline
    return Result(agent=ra.orchestrator_agent, context_variables=context_variables)


def transfer_to_writer(context_variables: ContextVariables, single_outline_element: str) -> Result:
    """Calls the writer with a single element from the outline for the requested report.

    Arguments:
        single_outline_element: An element from the outline of the report
    """
    context_variables["active_header"] = single_outline_element
    context_variables["research_result"] = None
    return Result(agent=ra.writer_agent, context_variables=context_variables)


def transfer_text_to_orchestrator(context_variables: ContextVariables, report_outline: list[str]) -> Result:
    """Calls the orchestrator with an outline for the requested report.

    Arguments:
        report_outline: The outline of the report. List of strings. each element is a heading or a paragraph summary
    """
    context_variables["report_outline"] = report_outline
    return Result(agent=ra.orchestrator_agent, context_variables=context_variables)


def transfer_text_to_editor(context_variables: ContextVariables, report_outline: list[str]) -> Result:
    """Calls the orchestrator with an outline for the requested report.

    Arguments:
        report_outline: The outline of the report. List of strings. each element is a heading or a paragraph summary
    """
    context_variables["report_outline"] = report_outline
    return Result(agent=ra.orchestrator_agent, context_variables=context_variables)


def do_research(context_variables: ContextVariables, query: str) -> Result:
    """Does research (with access to the web) with a search query you need an answer for.

    Arguments:
        query: A query, a question, a topic, or a keyword you need to search for
    """
    cached_research = load_dictionary_list("research.json")

    if cached_research and query in [research["query"] for research in cached_research]:  # type: ignore
        single_research = next(research for research in cached_research if research["query"] == query)  # type: ignore
        print(f"\n\n{query} already searched... loading...\n\n")
        context_variables["research_result"] = single_research
        return Result(value=f"{single_research}", agent=ra.writer_agent, context_variables=context_variables)

    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    response = client.search(query, include_answer=True)  # type: ignore

    context_variables["research_result"] = result_list = [response]  # type: ignore
    if cached_research:
        cached_research.extend(result_list)  # type: ignore
        save_dictionary_list(file_name="research.json", dic_list=cached_research)
    else:
        save_dictionary_list(file_name="research.json", dic_list=result_list)  # type: ignore

    return Result(value=f"{result_list}", agent=ra.writer_agent, context_variables=context_variables)


def do_set_next_part_to_work_on(context_variables: ContextVariables, next_part: str) -> Result:
    """Set the next part to work on in the report.

    Arguments:
        next_part: The next part to work on in the report
    """
    context_variables["active_header"] = next_part
    return Result(agent=ra.writer_agent, context_variables=context_variables)


def do_generate_text(context_variables: ContextVariables) -> Result:
    """Write text for the report for the current active outline."""
    provider = LiteLLMProvider(LiteLLMConfig(enable_cache=True))
    report = context_variables.get("report")

    info = f"Write a lengthy text fitting for the report type '{report.report_type}' for the current active outline element. It should be of highest quality."  # type: ignore

    active_header = context_variables.get("active_header")
    research_result = context_variables.get("research_result")

    info += f"\n\nContext information:"
    info += f"\n\nReport: {report}"
    info += f"\n\nSection: {active_header}"
    info += f"\n\nResearch result: {research_result}"

    info += f"""\n\nJUST WRITE THE TEXT FOR THE ACTIVE HEADER. DO NOT WORRY ABOUT THE REST OF THE REPORT.
    ALSO DON'T WRITE FLUFF OR EXPLANATIONS OR SIMILAR. JUST WRITE THE TEXT FOR THE ACTIVE HEADER."""
    info += f"""\n\nInclude the research information in the text with citations and full uri-links to the original sources.
    Start with a publishable title/header for the section, followed by high quality, well written, and informative and beautifully markdown formatted text.
    """

    msg = Message(role="user", content=info)
    result = provider.complete([msg])
    context_variables["written_header"] = (active_header, result.content)

    report.finished_parts.append((active_header, result.content))  # type: ignore

    save_text_to_file("report.md", report.title, result.content)  # type: ignore

    if result.content:
        return Result(value=result.content, agent=ra.orchestrator_agent, context_variables=context_variables)
    else:
        return Result(agent=ra.orchestrator_agent, context_variables=context_variables)


def transfer_to_outline_generator(
    context_variables: ContextVariables,
    user_query: str,
    title: str,
    report_type: str,
) -> Result:
    """Calls the outline generator to create an outline for a report.

    Args:
        user_query: The user query.
        title: The title of the report. Come up with a catchy one. Required
        report_type: The type of report. example: Blog, paper, article....
    """
    report = Report(
        user_query=user_query,
        title=title,
        report_type=report_type,
    )
    context_variables["report"] = report

    return Result(agent=ra.outline_generator_agent, context_variables=context_variables)


def transfer_feedback_to_writer(context_variables: ContextVariables, report_outline: list[str]) -> Result:
    """Calls the orchestrator with an outline for the requested report.

    Arguments:
        report_outline: The outline of the report. List of strings. each element is a heading or a paragraph summary
    """
    context_variables["report_outline"] = report_outline
    return Result(agent=ra.orchestrator_agent, context_variables=context_variables)


def transfer_research_to_writer(context_variables: ContextVariables, report_outline: list[str]) -> Result:
    """Calls the orchestrator with an outline for the requested report.

    Arguments:
        report_outline: The outline of the report. List of strings. each element is a heading or a paragraph summary
    """
    context_variables["report_outline"] = report_outline
    return Result(agent=ra.orchestrator_agent, context_variables=context_variables)
