"""Example showing how to use the Temporal-based implementation."""

import asyncio

from temp_schwarm.activities import execution, providers
from temp_schwarm.client import TemporalClientManager, TemporalConfig
from temp_schwarm.models import AgentConfig, Message, ProviderConfig
from temp_schwarm.worker import SchwarmWorker, WorkerConfig
from temp_schwarm.workflows.agent import AgentWorkflow


# Example provider configurations
class LLMConfig(ProviderConfig):
    """LLM provider configuration."""

    def __init__(self):
        super().__init__(provider_type="llm", provider_name="gpt-4", settings={"model": "gpt-4", "temperature": 0.7})


class MemoryConfig(ProviderConfig):
    """Memory provider configuration."""

    def __init__(self):
        super().__init__(
            provider_type="memory", provider_name="zep", settings={"api_key": "test-key", "collection": "agent-memory"}
        )


async def main():
    """Run the example."""
    # Set up Temporal client
    temporal_config = TemporalConfig(host="localhost", port=7233, namespace="default", task_queue="schwarm-task-queue")
    client = await TemporalClientManager().get_client(temporal_config)

    # Create worker
    worker_config = WorkerConfig(
        task_queue="schwarm-task-queue",
        workflows=[AgentWorkflow],
        activities=[
            providers.initialize_provider,
            providers.cleanup_provider,
            execution.decide_action,
            execution.execute_function,
        ],
        temporal_config=temporal_config,
    )
    worker = SchwarmWorker(worker_config)

    # Start worker in background
    worker_task = asyncio.create_task(worker.start())

    try:
        # Create agent configurations
        researcher = AgentConfig(
            name="researcher",
            provider_configurations=[LLMConfig(), MemoryConfig()],
            instructions="You are a research agent that analyzes topics.",
        )

        # Start workflow
        handle = await client.start_workflow(
            AgentWorkflow.run, args=[researcher], id="research-workflow", task_queue="schwarm-task-queue"
        )

        # Send a message
        await handle.signal(AgentWorkflow.handle_message, Message(content="Research the history of AI"))

        # Wait for result
        result_dict = await handle.result()
        result = result_dict.to_result()

        print(f"Research result: {result.value}")

        # Query workflow state
        state = await handle.query(AgentWorkflow.get_state)
        print(f"Final workflow state: {state}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Cleanup
        await worker.shutdown()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    asyncio.run(main())
