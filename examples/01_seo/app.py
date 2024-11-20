"""A blog post creation process using provider-based agents for orchestration, writing, and SEO optimization.

System flow: User -> Orchestrator -> Blog Writer -> Orchestrator -> SEO Optimizer -> Orchestrator -> User

This example demonstrates the provider-based architecture with:
1. Event handling for tracking agent interactions
2. LLM integration for content generation
3. Context management for state tracking
4. Budget tracking for API usage
"""

import os
import shutil
from typing import Any

from rich.console import Console
from rich.markdown import Markdown

from schwarm.core.schwarm import Schwarm
from schwarm.models.display_config import DisplayConfig
from schwarm.models.message import Message
from schwarm.models.types import Agent, Result
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.provider.models.budget_provider_config import BudgetProviderConfig
from schwarm.provider.models.context_provider_config import ContextProviderConfig
from schwarm.provider.models.debug_provider_config import DebugProviderConfig
from schwarm.utils.file import save_text_to_file
from schwarm.utils.settings import APP_SETTINGS

# Setup console and working directory
console = Console()
console.clear()
APP_SETTINGS.DATA_FOLDER = "examples/01_seo/.data"
if os.path.exists(APP_SETTINGS.DATA_FOLDER):
    shutil.rmtree(APP_SETTINGS.DATA_FOLDER)
os.makedirs(APP_SETTINGS.DATA_FOLDER)

## INSTRUCTIONS ##


def orchestrator_instructions(context_variables: dict[str, Any]) -> str:
    """Instructions for the orchestrator agent.

    The orchestrator manages the blog creation workflow, coordinating between
    the writer and SEO optimizer until the content meets quality standards.
    """
    instruction = """You are the workflow orchestrator for blog post creation.
    Your role is to coordinate between the blog writer and SEO optimizer to produce
    high-quality, SEO-optimized content. Continue iterations until score > 8/10.
    
    Use these tools:
    - transfer_to_blog_writer: Initial blog creation
    - transfer_to_blog_writer_with_review: Revisions based on SEO feedback
    - transfer_to_seo_optimizer: Get SEO review
    - finish_blog: Complete when score >= 9
    """

    if "score" in context_variables:
        # Show current state for iteration
        instruction += f"\n\nCurrent Blog:\nTitle: {context_variables['blog_title']}\n\n{context_variables['blog']}"
        instruction += f"\n\nSEO Score: {context_variables['score']}"
        instruction += f"\nReview Notes: {context_variables['review']}"
        instruction += "\n\nDecide: transfer_to_blog_writer_with_review for improvements, or finish_blog if score >= 9"
    else:
        if "blog" in context_variables:
            instruction += "\n\nBlog draft ready but needs SEO review."
            instruction += "\nAction: transfer_to_seo_optimizer"
        else:
            instruction += "\n\nNew blog request received."
            instruction += "\nAction: transfer_to_blog_writer with detailed requirements"
    return instruction


def blog_writer_instructions(context_variables: dict[str, Any]) -> str:
    """Instructions for the blog writer agent.

    The writer focuses on creating engaging, well-structured content
    based on the topic and any SEO feedback.
    """
    instruction = """You are an expert blog writer skilled in creating engaging, informative content.
    
    Guidelines:
    - Create clear, well-structured content
    - Use engaging headlines and subheadings
    - Include relevant examples and details
    - Maintain natural, readable flow
    
    After writing, use transfer_blog_to_orchestrator to submit your work.
    """

    if "review" in context_variables:
        instruction += f"\n\nPrevious SEO Review (Score: {context_variables['score']}):"
        instruction += f"\nImprovement Points: {context_variables['review']}"
        instruction += f"\n\nOriginal Content:\n{context_variables['blog']}"

    return instruction


def seo_optimizer_instructions(context_variables: dict[str, Any]) -> str:
    """Instructions for the SEO optimizer agent.

    The optimizer analyzes content for SEO effectiveness and provides
    specific improvement recommendations.
    """
    instruction = """You are an SEO expert who evaluates and optimizes blog content.
    
    Evaluation criteria:
    - Keyword usage and placement
    - Meta description optimization
    - Header structure (H1, H2, etc.)
    - Content length and readability
    - Internal/external linking opportunities
    - Mobile optimization considerations
    
    Provide a detailed review using transfer_review_to_orchestrator:
    - Score (1-10)
    - Specific improvement points
    """

    if "blog" in context_variables:
        instruction += f"\n\nBlog to Review:\nTitle: {context_variables['blog_title']}\n\n{context_variables['blog']}"

    return instruction


## PROVIDER CONFIGURATIONS ##

# LLM configuration with caching enabled
llm_config = LiteLLMConfig(
    provider_name="lite_llm",
    provider_lifecycle="singleton",
    provider_type="llm",
    enable_cache=True,
)

## AGENTS ##

orchestrator_agent = Agent(
    name="orchestrator",
    model="gpt-4",
    instructions=orchestrator_instructions,
    parallel_tool_calls=False,
    providers=[
        llm_config,
        DebugProviderConfig(),
        BudgetProviderConfig(),
    ],
)

blog_writer = Agent(
    name="blog_writer",
    model="gpt-4",
    instructions=blog_writer_instructions,
    providers=[
        llm_config,
        ContextProviderConfig(),
    ],
)

seo_optimizer = Agent(
    name="seo_optimizer",
    model="gpt-4",
    instructions=seo_optimizer_instructions,
    providers=[
        llm_config,
        ContextProviderConfig(),
    ],
)

user_agent = Agent(
    name="user_agent",
    model="gpt-4",
    instructions="Display the final blog post.",
    providers=[llm_config],
    tool_choice="none",  # Forces content display without tool use
)

## FUNCTIONS ##


def transfer_to_blog_writer(task: str) -> Agent:
    """Initiate blog writing with requirements."""
    return blog_writer


def transfer_to_blog_writer_with_review(task: str, score: str, review: str, blog_to_improve: str) -> Agent:
    """Request blog revision based on SEO review."""
    return blog_writer


def transfer_to_seo_optimizer(blog: str) -> Agent:
    """Submit blog for SEO review."""
    return seo_optimizer


def transfer_blog_to_orchestrator(context_variables: dict[str, Any], blog_title: str, blog: str) -> Agent:
    """Submit blog draft to orchestrator."""
    context_variables["blog_title"] = blog_title
    context_variables["blog"] = blog
    context_variables["score"] = None
    context_variables["review"] = None

    # Save first draft for comparison
    if not os.path.exists(f"{APP_SETTINGS.DATA_FOLDER}/blog_first_draft.md"):
        save_text_to_file("blog_first_draft.md", blog_title, blog)

    return orchestrator_agent


def transfer_review_to_orchestrator(context_variables: dict[str, Any], score: str, review: list[str]) -> Result:
    """Submit SEO review to orchestrator."""
    context_variables["review"] = review
    context_variables["score"] = score
    return Result(
        value=f"Score: {score}\n\nReview Points:\n{review}",
        agent=orchestrator_agent,
        context_variables=context_variables,
    )


def finish_blog(context_variables: dict[str, Any], blog_title: str, finished_blog_without_title: str) -> Result:
    """Complete blog creation process."""
    save_text_to_file("blog.md", blog_title, finished_blog_without_title)
    return Result(
        value=f"# {blog_title}\n\n{finished_blog_without_title}", agent=user_agent, context_variables=context_variables
    )


## FUNCTION REGISTRATION ##

orchestrator_agent.functions = [
    transfer_to_blog_writer,
    transfer_to_seo_optimizer,
    transfer_to_blog_writer_with_review,
    finish_blog,
]

blog_writer.functions = [transfer_blog_to_orchestrator]
seo_optimizer.functions = [transfer_review_to_orchestrator]

## MAIN EXECUTION ##

console.print(Markdown("# Blog Creation Demo"))

# Example blog topic
input_text = "Create a blog post about weekend activities during autumn."

# Run the workflow
response = Schwarm().run(
    orchestrator_agent,
    messages=[Message(role="user", content=input_text)],
    context_variables={},
    max_turns=100,
    execute_tools=True,
    display_config=DisplayConfig(
        show_function_calls=True,
        function_calls_wait_for_user_input=True,
        show_instructions=True,
        instructions_wait_for_user_input=True,
        max_length=-1,
    ),
    show_logs=False,
)

# Display result
console.print(Markdown("# Final Blog Post"))
# console.print(Markdown(response.messages[-1].content))
