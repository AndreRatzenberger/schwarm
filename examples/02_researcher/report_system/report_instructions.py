"""Provide instructions for the agents in the report system."""

from schwarm.models.types import ContextVariables


def orchestrator_instructions(context_variables: ContextVariables) -> str:
    """Provide instructions for the orchestrator agent."""
    default = """
    You are the orchestrator. You are an agent that coordinates the other agents.
    The task of this agent system is creating top-notch reports, blogs, papers, articles, and
    any other written content that is needed by the user.
    Your tasks are to:
    """
    if not context_variables.get("report"):
        default += "- Transfer the user request to the outline generator:\n"
    else:
        if not context_variables.get("written_header"):
            default += "- Transfer the first outline to the blog writer:\n"
            default += f"""
            These are the context variables:
            Report: {context_variables.get("report")}
            report_outline: {context_variables.get("report_outline")}
            """
        else:
            default += "- Transfer the next not done outline element to the blog writer with transfer_to_writer:\n"
            default += f"""
            These are the context variables:
            already done: {context_variables.get("active_header")}

            written text: {context_variables.get("written_header")}

            Report: {context_variables.get("report")}
            report_outline: {context_variables.get("report_outline")}

            """

    return default


def outline_instructions(context_variables: ContextVariables) -> str:
    """Provide instructions for the orchestrator agent."""
    default = f"""
    Transfer back to the orchestrator agent with an outline for the requested report.

    These are the properties of the requested report:
    Report: {context_variables.get("report")}
    """
    return default


def research_instructions(context_variables: ContextVariables) -> str:
    """Provide instructions for the orchestrator agent."""
    default = f"""
    Transfer the results of your research back to the orchestrator

    These are the properties of the requested report:
    Report: {context_variables.get("report")}

    and the requests to search for
    """
    return default


def writer_instructions(context_variables: ContextVariables) -> str:
    """Provide instructions for the writer agent."""
    if context_variables.get("research_result"):
        default = f"""
        Call do_generate_text, if you have enough information for writing high quality text for the information below.
        Call do_research if you still need information.

        These are the information you have:
        Report: {context_variables.get("report")}
        Part to work on: {context_variables.get("active_header")}

        """

        default += f"""
        \n\nResearch result: {context_variables.get("research_result")}
        """
    else:
        default = f"""
        Call do_research for more information about this topic you should work on.

        These are the information you have:
        Report: {context_variables.get("report")}
        Part to work on: {context_variables.get("active_header")}

        """

    return default
