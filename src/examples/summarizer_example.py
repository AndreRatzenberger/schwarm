"""Example demonstrating the use of the Schwarm framework."""

import asyncio
import os

from schwarm.agents.agent_builder import AgentBuilder
from schwarm.events.events import Event, EventType
from schwarm.functions.text_functions import summarize_function
from schwarm.providers.simple_llm_provider import SimpleLLMProvider


def log_event(event: Event) -> None:
    """Simple event listener that logs events to the console."""
    print(f"Event: {event.type.name}")
    if event.data:
        print(f"Data: {event.data}")
    print("---")


async def main() -> None:
    """Run the summarizer example."""
    # Create an LLM provider (using environment variable for API key)
    provider = SimpleLLMProvider(model="gpt-3.5-turbo", temperature=0.7, max_tokens=150)

    # Build an agent with the provider and summarize function
    agent = (
        AgentBuilder("SummarizerAgent")
        .with_instructions("I am an agent specialized in summarizing text using AI.")
        .with_provider(provider)
        .with_function(summarize_function)
        .with_event_listener(EventType.BEFORE_FUNCTION_EXECUTION, log_event)
        .with_event_listener(EventType.AFTER_FUNCTION_EXECUTION, log_event)
        .build()
    )

    # Initialize the agent
    await agent.initialize()

    # Store the provider in the context for the function to use
    agent.context.set("llm_provider", provider)

    # Example text to summarize
    text = """
    Artificial Intelligence (AI) is a broad field of computer science focused on 
    creating intelligent machines that can perform tasks typically requiring human 
    intelligence. These tasks include visual perception, speech recognition, 
    decision-making, language translation, and problem-solving. AI systems are 
    powered by machine learning algorithms that enable them to learn from data 
    and improve their performance over time without explicit programming. Deep 
    learning, a subset of machine learning, uses artificial neural networks 
    inspired by the human brain to process complex patterns in large datasets. 
    As AI technology continues to advance, it is increasingly being integrated 
    into various aspects of our daily lives, from virtual assistants and 
    recommendation systems to autonomous vehicles and medical diagnosis tools.
    """

    try:
        # Execute the summarize function
        print("Original text:")
        print(text)
        print("\nGenerating summary...")

        summary = await agent.execute_function(
            "summarize",
            text,
            max_length=50,  # Target length in words
        )

        print("\nSummary:")
        print(summary)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Ensure you have set your API key in the environment
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY environment variable")
    else:
        asyncio.run(main())
