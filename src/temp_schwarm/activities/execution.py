"""Activities for decision making and function execution."""

from dataclasses import dataclass
from typing import Any

from temporalio import activity

from temp_schwarm.models import AgentConfig, Message, Result


@dataclass
class Action:
    """Represents a decided action to take."""

    action_type: str  # "function", "respond", "handoff"
    function_name: str | None = None
    function_args: dict[str, Any] | None = None
    response_text: str | None = None
    target_agent: AgentConfig | None = None


@activity.defn
async def decide_action(message: Message, context_variables: dict[str, Any], agent_config: AgentConfig) -> Action:
    """Decide what action to take for a message."""
    # This would normally use an LLM to decide
    # For now, just return a simple response action
    return Action(action_type="respond", response_text=f"Received message: {message.content}")


@activity.defn
async def execute_function(
    action: Action, message: Message, context_variables: dict[str, Any], provider_states: dict[str, Any]
) -> Result:
    """Execute a decided action."""
    if action.action_type == "respond":
        return Result(value=action.response_text, context_variables=context_variables)
    elif action.action_type == "handoff":
        return Result(
            value="Handing off to another agent", context_variables=context_variables, target_agent=action.target_agent
        )
    elif action.action_type == "function":
        # This would normally execute the actual function
        return Result(value=f"Executed function {action.function_name}", context_variables=context_variables)
    else:
        raise ValueError(f"Unknown action type: {action.action_type}")
