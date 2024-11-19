"""This module defines the agents used in the report example."""

import report_system.report_instructions as ri
from schwarm.models.types import Agent
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.services.budget_service import BudgetService

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=ri.orchestrator_instructions,
    parallel_tool_calls=False,
    provider_config=LiteLLMConfig(enable_cache=True),
)

outline_generator_agent = Agent(
    name="outline_generator_agent",
    instructions=ri.outline_instructions,
    parallel_tool_calls=False,
    provider_config=LiteLLMConfig(enable_cache=True),
)

writer_agent = Agent(
    name="writer_agent",
    instructions=ri.writer_instructions,
    parallel_tool_calls=False,
    provider_config=LiteLLMConfig(enable_cache=True),
    budget=BudgetService(save_budget=True, max_spent=1, max_tokens=1000, effect_on_exceed="warning"),
)


research_agent = Agent(
    name="research_agent",
    instructions=ri.research_instructions,
    parallel_tool_calls=False,
    provider_config=LiteLLMConfig(enable_cache=True),
)

editor_agent = Agent(
    name="editor_agent",
    instructions=ri.research_instructions,
    parallel_tool_calls=False,
    provider_config=LiteLLMConfig(enable_cache=True),
)
