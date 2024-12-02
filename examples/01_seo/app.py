"""A simple example of a blog post creation process with an orchestrator, blog writer, and SEO optimizer.

System flow: User -> Orchestrator -> Blog Writer -> Orchestrator-> SEO Optimizer -> Orchestrator...... -> User
"""

import os
import shutil

from rich.console import Console
from rich.markdown import Markdown

from schwarm.core.schwarm import Schwarm
from schwarm.models.message import Message
from schwarm.models.types import Agent, ContextVariables, Result
from schwarm.provider.llm_provider import LLMConfig
from schwarm.utils.file import save_text_to_file
from schwarm.utils.settings import APP_SETTINGS


def main():
    console = Console()
    console.clear()
    APP_SETTINGS.DATA_FOLDER = "examples/01_seo/.data"
    if os.path.exists(APP_SETTINGS.DATA_FOLDER):
        shutil.rmtree(APP_SETTINGS.DATA_FOLDER)

    # Optionally, recreate the folder if needed
    os.makedirs(APP_SETTINGS.DATA_FOLDER)

    ## INSTRUCTIONS ##

    def orchestrator_instructions(context_variables: ContextVariables):
        """Instructions for the orchestrator."""
        instruction = """Your job is to orchestrate the conversation between the blog writer, and SEO optimizer.
        In the end there should be a blog post about the user's topic fully optimized for SEO.
        Continue until the score is >8/10
        """

        if context_variables.get("score"):
            instruction += f"\n\nBlog: \n\n{context_variables.get('blog_title')}\n\n{context_variables.get('blog')}"
            instruction += f"\n\nScore: {context_variables.get('score')}"
            instruction += f"\n\nReview: {context_variables.get('review')}"

            instruction += f"\n\ntransfer_to_blog_writer_with_review with a in-depth task description for the blog writer, or finish_blog if the score is a 9 or 10"
        else:
            if context_variables.get("blog"):
                instruction += "\n\nScore currently unknown. REVIEW NEEDED."
                instruction += "\n\ntransfer_to_seo_optimizer for reviewing"
            else:
                instruction += "\n\ntransfer_to_blog_writer with a in-depth task description for the blog writer."
        return instruction

    def blog_writer_instructions(context_variables: ContextVariables):
        """Instructions for the blog writer."""
        instruction = """Call transfer_blog_to_orchestrator."""

        return instruction

    def seo_optimizer_instructions(context_variables: ContextVariables):
        """Instructions for the SEO optimizer."""
        instruction = """You are a professional seo optimizer. call transfer_review_to_orchestrator"""

        return instruction

    ## AGENTS ##

    orchestrator_agent = Agent(
        name="orchestrator",
        instructions=orchestrator_instructions,
        parallel_tool_calls=False,
        configs=[LLMConfig(streaming=True)],
    )

    blog_writer = Agent(
        name="blog_writer",
        instructions=blog_writer_instructions,
        configs=[LLMConfig(streaming=True)],
    )

    seo_optimizer = Agent(
        name="seo_optimizer",
        instructions=seo_optimizer_instructions,
        configs=[LLMConfig(streaming=True)],
    )

    user_agent = Agent(
        name="user_agent",
        instructions="Print the final blog post.",
        configs=[LLMConfig(streaming=True)],
        tool_choice="none",  # forces to print the final blog post
    )

    ## FUNCTIONS ##

    def transfer_to_blog_writer(task: str) -> Agent:
        """Give a task to the blog writer."""
        return blog_writer

    def transfer_to_blog_writer_with_review(task: str, score: str, review: str, blog_to_improve: str) -> Agent:
        """Give a task to the blog writer.

        Arguments:
            task: The task for the blog writer
            score: The score of the blog (1-10)
            review: The review points to improve. A list of comma seperated strings, each element a point to improve.
            blog_to_improve: The current content of the blog that needs to be improved
        """
        return blog_writer

    def transfer_to_seo_optimizer(blog: str) -> Agent:
        """Transfer to SEO optimizer."""
        return seo_optimizer

    def transfer_blog_to_orchestrator(context_variables, blog_title: str, blog: str) -> Agent:  # type: ignore
        """Transfer the blog content to the orchestrator.

        Arguments:
            blog_title: The title of the blog
            blog: The content of the blog
        """
        context_variables["blog_title"] = blog_title
        context_variables["blog"] = blog
        context_variables["score"] = None
        context_variables["review"] = None
        if not os.path.exists(f"{APP_SETTINGS.DATA_FOLDER}/blog_first_draft.md"):
            save_text_to_file("blog_first_draft.md", blog_title, blog)
        return orchestrator_agent

    def transfer_review_to_orchestrator(context_variables: ContextVariables, score: str, review: list[str]) -> Result:  # type: ignore
        """Transfer the blog review to the orchestrator.

        Arguments:
            score: The score of the blog (1-10)
            review: The review points to improve. A list of comma seperated strings, each element a point to improve.
        """
        context_variables["review"] = review
        context_variables["score"] = score
        return Result(
            value=f"Score: {score} \n\n Review: {review}", agent=orchestrator_agent, context_variables=context_variables
        )

    def finish_blog(context_variables: ContextVariables, blog_title: str, finished_blog_without_title: str) -> Result:  # type: ignore
        """Transfer the final blog to the user.

        Arguments:
            blog_title: The title of the blog
            finished_blog_without_title: The final blog
        """
        save_text_to_file("blog.md", blog_title, finished_blog_without_title)
        return Result(
            value=blog_title + "\n\n" + finished_blog_without_title,
            agent=user_agent,
            context_variables=context_variables,
        )

    ############
    ## AGENTS ##
    ############

    orchestrator_agent.functions.append(transfer_to_blog_writer)
    orchestrator_agent.functions.append(transfer_to_seo_optimizer)  # type: ignore
    orchestrator_agent.functions.append(transfer_to_blog_writer_with_review)  # type: ignore
    orchestrator_agent.functions.append(finish_blog)  # type: ignore
    blog_writer.functions.append(transfer_blog_to_orchestrator)  # type: ignore
    seo_optimizer.functions.append(transfer_review_to_orchestrator)  # type: ignore

    console.print(Markdown("# Blog Demo"))

    # cached prompts
    # input = "I need a blog post about ways to use AI in cooking meals."

    input = "I need a blog post about weekend activities during autumn."

    response = Schwarm().run(
        orchestrator_agent,
        messages=[Message(role="user", content=input)],
        context_variables={},
        override_model="gpt-4o",
        max_turns=100,
        execute_tools=True,
    )

    console.print(Markdown("# Output"))
    console.print(Markdown(response.messages[-1].content))  # type: ignore


if __name__ == "__main__":
    main()
    # asyncio.run(main(), debug=True)
