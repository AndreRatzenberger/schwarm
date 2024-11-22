"""Core agent workflow definition."""

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

from temp_schwarm.models import AgentConfig, Message, Result, ResultDictionary


@workflow.defn
class AgentWorkflow:
    """Represents an agent as a Temporal workflow."""

    def __init__(self):
        self._config: AgentConfig | None = None
        self._providers: dict[str, Any] = {}
        self._message_history: list[Message] = []
        self._context_variables: dict[str, Any] = {}
        self._should_terminate: bool = False
        self._last_result: ResultDictionary | None = None

    @workflow.run
    async def run(self, config: AgentConfig) -> ResultDictionary:
        """Start the agent workflow."""
        self._config = config

        # Initialize providers through activities
        for provider_config in config.provider_configurations:
            if provider_config.enabled:
                # Import here to avoid circular dependency
                from temp_schwarm.activities.providers import initialize_provider

                provider_state = await workflow.execute_activity(
                    initialize_provider,
                    args=[provider_config],
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(
                        initial_interval=timedelta(seconds=1),
                        maximum_interval=timedelta(minutes=1),
                        maximum_attempts=3,
                    ),
                )
                self._providers[provider_config.provider_name] = provider_state

        # Wait for messages/signals until termination
        await workflow.wait_condition(lambda: self._should_terminate)

        # Return last result or empty result
        return self._last_result or ResultDictionary(value="Workflow completed")

    @workflow.signal
    async def handle_message(self, message: Message) -> None:
        """Handle an incoming message."""
        self._message_history.append(message)

        # Import here to avoid circular dependency
        from temp_schwarm.activities.execution import decide_action, execute_function

        # Use LLM to decide what to do
        action = await workflow.execute_activity(
            decide_action,
            args=[message, self._context_variables, self._config],
            start_to_close_timeout=timedelta(minutes=1),
        )

        # Execute the chosen action
        result = await workflow.execute_activity(
            execute_function,
            args=[action, message, self._context_variables, self._providers],
            start_to_close_timeout=timedelta(minutes=5),
        )

        # Convert Result to ResultDictionary
        if isinstance(result, Result):
            self._last_result = ResultDictionary.from_result(result)
            self._context_variables.update(result.context_variables)

            # If handoff to another agent needed, start child workflow
            if result.target_agent:
                try:
                    child_handle = await workflow.start_child_workflow(
                        self.__class__.run,
                        args=[result.target_agent],
                        id=f"{workflow.info().workflow_id}_{result.target_agent.name}",
                    )
                    # Get child result
                    self._last_result = await child_handle.result()
                except Exception as e:
                    self._last_result = ResultDictionary(
                        value=f"Child workflow error: {e!s}", context_variables=self._context_variables
                    )
                finally:
                    self._should_terminate = True

    @workflow.query
    def get_state(self) -> dict[str, Any]:
        """Get current workflow state."""
        return {
            "config": self._config.__dict__ if self._config else None,
            "providers": self._providers,
            "message_history": [msg.__dict__ for msg in self._message_history],
            "context_variables": self._context_variables,
            "last_result": self._last_result.__dict__ if self._last_result else None,
        }

    @workflow.signal
    def terminate(self) -> None:
        """Signal to terminate the workflow."""
        self._should_terminate = True
